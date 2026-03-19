"""S28 Integration Gate — statistical validation for roll-based combat."""

from __future__ import annotations

from engine.game import run_match
from engine.loader import load_bots
from engine.stats import validate_allocation
from agentgrounds.wars.cli.feed import format_feed_event
from tests.conftest import bot_config, chase_and_attack

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BOTS_DIR = "bots"
SEED = 42
NUM_MATCHES = 20


def _builtin_configs() -> list[dict]:
    return load_bots(BOTS_DIR)


def _seeded_match(seed: int = SEED, configs: list[dict] | None = None) -> dict:
    cfgs = configs if configs is not None else _builtin_configs()
    return run_match(cfgs, match_id=1, seed=seed)


def _run_many(n: int = NUM_MATCHES, configs: list[dict] | None = None) -> list[dict]:
    """Run *n* seeded matches and return match data list."""
    return [_seeded_match(seed=i + 1, configs=configs) for i in range(n)]


def _custom_stat_config(
    name: str, emoji: str, power: int, speed: int, armor: int, mind: int,
) -> dict:
    alloc = validate_allocation(power, speed, armor, mind)
    return {
        "name": name, "emoji": emoji, "bio": "", "author": "test",
        "decide_func": chase_and_attack,
        "stat_allocation": alloc,
    }


def _collect_events(matches: list[dict], event_type: str) -> list[dict]:
    """Collect all events of a given type from a list of matches."""
    events: list[dict] = []
    for match in matches:
        for rnd in match["rounds"]:
            for evt in rnd.get("events", []):
                if evt.get("type") == event_type:
                    events.append(evt)
    return events


def _collect_all_attack_events(matches: list[dict]) -> list[dict]:
    """Collect all hit + attack_miss + ranged_hit + ranged_attack_miss events."""
    attack_types = {"hit", "attack_miss", "ranged_hit", "ranged_attack_miss"}
    events: list[dict] = []
    for match in matches:
        for rnd in match["rounds"]:
            for evt in rnd.get("events", []):
                if evt.get("type") in attack_types:
                    events.append(evt)
    return events


# ===========================================================================
# Statistical tests — run 20 seeded matches, check distributions
# ===========================================================================


class TestDamageDistribution:
    """Verify hit damage is within expected range."""

    def test_avg_damage_per_hit(self) -> None:
        matches = _run_many()
        hits = _collect_events(matches, "hit")
        assert len(hits) > 0, "No hit events found across 20 matches"
        avg = sum(h["damage"] for h in hits) / len(hits)
        # Crits inflate average above base 25; accept 20-40
        assert 20 <= avg <= 40, (
            f"Avg damage {avg:.1f} outside [20, 40] "
            f"(from {len(hits)} hits across {len(matches)} matches)"
        )


class TestMissRate:
    """Verify miss rate is within expected bounds."""

    def test_miss_rate(self) -> None:
        matches = _run_many()
        all_attacks = _collect_all_attack_events(matches)
        misses = [e for e in all_attacks if e["type"] in ("attack_miss", "ranged_attack_miss")]
        assert len(all_attacks) > 0, "No attack events found"
        miss_rate = len(misses) / len(all_attacks)
        # Ranged attacks have a -2 penalty, pushing overall miss rate higher
        assert 0.05 <= miss_rate <= 0.30, (
            f"Miss rate {miss_rate:.2%} outside [5%, 30%] "
            f"({len(misses)} misses / {len(all_attacks)} attacks)"
        )


class TestCritRate:
    """Verify crit rate is within expected bounds."""

    def test_crit_rate(self) -> None:
        matches = _run_many()
        hits = _collect_events(matches, "hit")
        ranged_hits = _collect_events(matches, "ranged_hit")
        all_hits = hits + ranged_hits
        assert len(all_hits) > 0, "No hit events found"
        crits = [h for h in all_hits if h.get("is_crit")]
        crit_rate = len(crits) / len(all_hits)
        assert 0.30 <= crit_rate <= 0.70, (
            f"Crit rate {crit_rate:.2%} outside [30%, 70%] "
            f"({len(crits)} crits / {len(all_hits)} hits)"
        )


class TestMatchLength:
    """Verify match length is within expected bounds."""

    def test_match_length(self) -> None:
        matches = _run_many()
        lengths = [len(m["rounds"]) for m in matches]
        avg = sum(lengths) / len(lengths)
        assert 15 <= avg <= 60, (
            f"Avg match length {avg:.1f} outside [15, 60] "
            f"(min={min(lengths)}, max={max(lengths)})"
        )


# ===========================================================================
# Event schema — roll data present
# ===========================================================================


class TestRollDataInEvents:
    """Verify hit/miss events contain roll data fields."""

    def test_hit_events_have_roll_data(self) -> None:
        matches = _run_many(5)
        hits = _collect_events(matches, "hit")
        assert len(hits) > 0, "No hit events found"
        for h in hits:
            for field in ("roll", "modifier", "ac", "is_crit"):
                assert field in h, f"Hit event missing '{field}': {h}"

    def test_attack_miss_events_have_roll_data(self) -> None:
        matches = _run_many(5)
        misses = _collect_events(matches, "attack_miss")
        assert len(misses) > 0, "No attack_miss events found"
        for m in misses:
            for field in ("roll", "modifier", "ac"):
                assert field in m, f"attack_miss event missing '{field}': {m}"


# ===========================================================================
# Stat effects — power / armor influence combat
# ===========================================================================


class TestStatEffects:
    """Verify stat allocations affect combat outcomes."""

    def test_high_power_more_damage(self) -> None:
        power_bot = _custom_stat_config("PowerBot", "\U0001f4aa", 50, 20, 15, 15)
        default_bot = bot_config("Default", "\U0001f47e", chase_and_attack)
        configs = [power_bot, default_bot]
        matches = _run_many(10, configs=configs)
        power_hits = [
            e for e in _collect_events(matches, "hit")
            if e["attacker"] == "\U0001f4aa"
        ]
        default_hits = [
            e for e in _collect_events(matches, "hit")
            if e["attacker"] == "\U0001f47e"
        ]
        if not power_hits or not default_hits:
            # Skip if one bot never hit (unlikely but possible)
            return
        power_avg = sum(h["damage"] for h in power_hits) / len(power_hits)
        default_avg = sum(h["damage"] for h in default_hits) / len(default_hits)
        assert power_avg > default_avg, (
            f"PowerBot avg {power_avg:.1f} should exceed default avg {default_avg:.1f}"
        )

    def test_high_armor_fewer_hits(self) -> None:
        tank = _custom_stat_config("Tank", "\U0001f6e1\ufe0f", 15, 15, 50, 20)
        default_bot = bot_config("Default", "\U0001f47e", chase_and_attack)
        configs = [tank, default_bot]
        matches = _run_many(10, configs=configs)
        # Count hits against each bot
        all_hits = _collect_events(matches, "hit")
        hits_vs_tank = [h for h in all_hits if h["target"] == "\U0001f6e1\ufe0f"]
        hits_vs_default = [h for h in all_hits if h["target"] == "\U0001f47e"]
        if not hits_vs_tank or not hits_vs_default:
            return
        # Tank has higher AC from DR, so should receive fewer hits
        # Use ratio rather than absolute count (matches may vary)
        tank_hit_rate = len(hits_vs_tank) / (len(hits_vs_tank) + len(hits_vs_default))
        assert tank_hit_rate < 0.50, (
            f"Tank received {tank_hit_rate:.2%} of hits, expected < 50% "
            f"({len(hits_vs_tank)} vs {len(hits_vs_default)})"
        )


# ===========================================================================
# Feed rendering
# ===========================================================================


class TestFeedRendering:
    """Verify feed formatters handle roll-based events."""

    def test_feed_shows_crit(self) -> None:
        evt = {
            "type": "hit", "attacker": "\U0001f916", "target": "\U0001f422",
            "damage": 37, "is_crit": True,
        }
        line = format_feed_event(evt, 5)
        assert line is not None
        assert "CRIT" in line

    def test_feed_shows_attack_miss(self) -> None:
        evt = {
            "type": "attack_miss", "attacker": "\U0001f916", "target": "\U0001f422",
            "roll": 3, "modifier": 2, "ac": 13,
        }
        line = format_feed_event(evt, 5)
        assert line is not None
        assert "dodged" in line


# ===========================================================================
# Regression & determinism
# ===========================================================================


class TestRegression:
    """Verify builtin bots still work and matches are deterministic."""

    def test_builtin_bots_still_work(self) -> None:
        configs = _builtin_configs()
        assert len(configs) >= 4, f"Expected >= 4 builtin bots, got {len(configs)}"
        match = _seeded_match(configs=configs)
        assert match["winner"] != "none", "Match ended with no winner"
        assert len(match["rounds"]) > 0, "Match has no rounds"

    def test_deterministic_with_seed(self) -> None:
        # Use deterministic bots (builtin bots use random module internally)
        configs = [
            bot_config("A", "\U0001f916", chase_and_attack),
            bot_config("B", "\U0001f47e", chase_and_attack),
            bot_config("C", "\U0001f3af", chase_and_attack),
            bot_config("D", "\U0001f422", chase_and_attack),
        ]
        m1 = _seeded_match(seed=999, configs=configs)
        m2 = _seeded_match(seed=999, configs=configs)
        assert m1["winner"] == m2["winner"], "Same seed produced different winners"
        assert len(m1["rounds"]) == len(m2["rounds"]), "Same seed produced different round counts"
        # Compare damage of first hit in each match
        for r1, r2 in zip(m1["rounds"], m2["rounds"]):
            e1 = [e for e in r1.get("events", []) if e.get("type") == "hit"]
            e2 = [e for e in r2.get("events", []) if e.get("type") == "hit"]
            assert len(e1) == len(e2), "Same seed produced different hit counts"
            for h1, h2 in zip(e1, e2):
                assert h1["damage"] == h2["damage"], "Same seed produced different damage"
