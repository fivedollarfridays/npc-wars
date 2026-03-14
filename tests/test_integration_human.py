"""Integration tests for human play pipeline (T11.11).

End-to-end validation: mock human match, override events, AFK detection,
bounty placement, and async/sync parity.
"""

from unittest.mock import patch

import pytest

from engine.afk import AFKTracker, AFK_THRESHOLD, KICK_THRESHOLD
from engine.bounty import place_bounties
from engine.game import _create_bots, run_match, run_match_async
from engine.human_input import MockInputAdapter
from tests.conftest import always_rest, bot_config, chase_and_attack, make_bot


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _patch_adapter(configs, adapter, bot_index=0):
    """Return a context manager that patches _create_bots to attach adapter."""
    original = _create_bots

    def patched(bot_configs, positions):
        bots = original(bot_configs, positions)
        bots[bot_index].human_adapter = adapter
        return bots

    return patch("engine.game._create_bots", side_effect=patched)


def _collect_override_events(match_data):
    """Extract all human_override events from match data."""
    return [
        evt for rnd in match_data["rounds"]
        for evt in rnd.get("events", [])
        if evt.get("type") == "human_override"
    ]


# ---------------------------------------------------------------------------
# Cycle 1: Mock human match runs to completion
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mock_human_match_completes():
    """A match with MockInputAdapter attached runs to completion."""
    adapter = MockInputAdapter([("rest",)] * 200)
    configs = [
        bot_config("Human", "HU", always_rest),
        bot_config("Killer", "KI", chase_and_attack),
        bot_config("Bot3", "B3", chase_and_attack),
    ]

    with _patch_adapter(configs, adapter, bot_index=0):
        data = await run_match_async(configs, match_id=1, seed=42)

    # Match must complete with a winner and at least 1 round
    from engine.watcher import WATCHER_EMOJI
    assert data["winner"] in {"HU", "KI", "B3", "none", WATCHER_EMOJI}
    assert data["duration_rounds"] >= 1
    assert len(data["rounds"]) >= 1
    assert len(data["players"]) >= 3


@pytest.mark.asyncio
async def test_mock_human_match_has_eliminations():
    """A completed match with 3+ bots has elimination records."""
    configs = [
        bot_config("A", "A1", chase_and_attack),
        bot_config("B", "B1", chase_and_attack),
        bot_config("C", "C1", always_rest),
    ]

    data = await run_match_async(configs, match_id=1, seed=99)

    # At least N-1 eliminations (one survivor)
    assert len(data["eliminations"]) >= 2


# ---------------------------------------------------------------------------
# Cycle 2: Override events in sync path (resolve_decisions)
# ---------------------------------------------------------------------------


def test_sync_override_events_appear():
    """Sync run_match emits human_override events when adapter overrides."""
    adapter = MockInputAdapter([("move", "east")] * 200)
    configs = [
        bot_config("Human", "HU", always_rest),
        bot_config("AI", "AI", chase_and_attack),
    ]

    with _patch_adapter(configs, adapter):
        data = run_match(configs, match_id=1, seed=42)

    override_events = _collect_override_events(data)
    assert len(override_events) > 0, "Expected human_override events in sync path"
    first = override_events[0]
    assert first["player"] == "HU"
    assert first["original"] == "rest"
    assert first["override"] == "move east"


def test_sync_no_override_on_timeout():
    """When MockInputAdapter returns None (empty list), no override events."""
    adapter = MockInputAdapter([])
    configs = [
        bot_config("Human", "HU", always_rest),
        bot_config("AI", "AI", chase_and_attack),
    ]

    with _patch_adapter(configs, adapter):
        data = run_match(configs, match_id=1, seed=42)

    assert len(_collect_override_events(data)) == 0


def test_sync_no_override_when_same_action():
    """No override event when human picks the same action as bot."""
    adapter = MockInputAdapter([("rest",)] * 200)
    configs = [
        bot_config("Human", "HU", always_rest),
        bot_config("AI", "AI", chase_and_attack),
    ]

    with _patch_adapter(configs, adapter):
        data = run_match(configs, match_id=1, seed=42)

    assert len(_collect_override_events(data)) == 0


# ---------------------------------------------------------------------------
# Cycle 3: Async match with 0 humans identical to sync
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_async_no_humans_matches_sync():
    """Async match with no human adapters produces identical output to sync."""
    configs = [
        bot_config("A", "A1", chase_and_attack),
        bot_config("B", "B1", chase_and_attack),
        bot_config("C", "C1", always_rest),
    ]

    sync_data = run_match(configs, match_id=1, seed=42)
    async_data = await run_match_async(configs, match_id=1, seed=42)

    assert sync_data["winner"] == async_data["winner"]
    assert sync_data["duration_rounds"] == async_data["duration_rounds"]
    assert len(sync_data["rounds"]) == len(async_data["rounds"])


# ---------------------------------------------------------------------------
# Cycle 4: AFK detection standalone
# ---------------------------------------------------------------------------


def test_afk_at_threshold():
    """Player marked AFK after AFK_THRESHOLD consecutive misses."""
    tracker = AFKTracker()
    tracker.register("HU")

    for _ in range(AFK_THRESHOLD - 1):
        tracker.record_miss("HU")
        assert not tracker.is_afk("HU")

    tracker.record_miss("HU")
    assert tracker.is_afk("HU")
    assert not tracker.is_kicked("HU")


def test_kicked_at_threshold():
    """Player kicked after KICK_THRESHOLD consecutive misses."""
    tracker = AFKTracker()
    tracker.register("HU")

    for _ in range(KICK_THRESHOLD - 1):
        tracker.record_miss("HU")
        assert not tracker.is_kicked("HU")

    tracker.record_miss("HU")
    assert tracker.is_kicked("HU")
    assert tracker.is_afk("HU")


def test_afk_resets_on_input():
    """Successful input resets AFK status and miss counter."""
    tracker = AFKTracker()
    tracker.register("HU")

    for _ in range(AFK_THRESHOLD):
        tracker.record_miss("HU")
    assert tracker.is_afk("HU")

    tracker.record_input("HU")
    assert not tracker.is_afk("HU")
    status = tracker.get_status("HU")
    assert status["consecutive_misses"] == 0


def test_kicked_permanent():
    """Once kicked, input does not reset status."""
    tracker = AFKTracker()
    tracker.register("HU")

    for _ in range(KICK_THRESHOLD):
        tracker.record_miss("HU")
    assert tracker.is_kicked("HU")

    tracker.record_input("HU")
    assert tracker.is_kicked("HU")


# ---------------------------------------------------------------------------
# Cycle 5: Bounty placement
# ---------------------------------------------------------------------------


def test_bounty_placement_single_human():
    """place_bounties creates one bounty for a single human player."""
    bots = [make_bot(emoji="HU"), make_bot(emoji="AI")]
    bounties = place_bounties(bots, {"HU"})

    assert len(bounties) == 1
    assert bounties[0].target_emoji == "HU"
    assert bounties[0].hp_restore == "full"
    assert bounties[0].bonus_damage_rounds == 3


def test_bounty_placement_multiple_humans():
    """place_bounties scales rewards for multiple human players."""
    bots = [make_bot(emoji="H1"), make_bot(emoji="H2"), make_bot(emoji="AI")]
    bounties = place_bounties(bots, {"H1", "H2"})

    assert len(bounties) == 2
    targets = {b.target_emoji for b in bounties}
    assert targets == {"H1", "H2"}
    # 2-human scaling: bonus_damage_rounds == 2
    assert all(b.bonus_damage_rounds == 2 for b in bounties)


def test_bounty_placement_no_humans():
    """place_bounties returns empty list for pure bot match."""
    bots = [make_bot(emoji="A1"), make_bot(emoji="A2")]
    bounties = place_bounties(bots, set())
    assert bounties == []
