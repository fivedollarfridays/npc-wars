"""Tests for leader bounty scoring — killing the leader gives +20 bonus."""

from __future__ import annotations

from engine.scoring import (
    KILL_POINTS,
    LEADER_BOUNTY_POINTS,
    ScoreEvent,
    calculate_round_scores,
)


def _make_bots(*emojis: str, alive: bool = True) -> list[dict]:
    return [{"emoji": e, "alive": alive, "hp": 80} for e in emojis]


def _kill_event(attacker: str, victim: str) -> dict:
    return {"type": "kill", "attacker": attacker, "victim": victim}


def _hit_event(attacker: str, target: str, damage: int = 30) -> dict:
    return {"type": "hit", "attacker": attacker, "target": target, "damage": damage}


# --- Cycle 1: Core bounty ---

def test_kill_leader_gives_bounty() -> None:
    """Killing the leader: killer gets kill pts + bounty."""
    bots = _make_bots("A", "B")
    events = [_kill_event("A", "B"), _hit_event("A", "B")]
    scores, sevts = calculate_round_scores(
        bots, events, round_num=5, storm_border=0, prev_storm_border=0,
        leader_emoji="B",
    )
    # A gets: survival(1) + kill(10) + bounty(20) + damage(1) + clean_kill(5) = 37
    bounty_evts = [e for e in sevts if e.source == "leader_bounty"]
    assert len(bounty_evts) == 1
    assert bounty_evts[0].emoji == "A"
    assert bounty_evts[0].points == LEADER_BOUNTY_POINTS


def test_kill_non_leader_normal_points() -> None:
    """Killing a non-leader: normal kill points, no bounty."""
    bots = _make_bots("A", "B", "C")
    events = [_kill_event("A", "C"), _hit_event("A", "C")]
    scores, sevts = calculate_round_scores(
        bots, events, round_num=5, storm_border=0, prev_storm_border=0,
        leader_emoji="B",
    )
    bounty_evts = [e for e in sevts if e.source == "leader_bounty"]
    assert len(bounty_evts) == 0
    # A still gets kill points
    kill_evts = [e for e in sevts if e.source == "kill" and e.emoji == "A"]
    assert kill_evts[0].points == KILL_POINTS


def test_leader_bounty_event_in_score_events() -> None:
    """ScoreEvent with source='leader_bounty' exists with correct fields."""
    bots = _make_bots("X", "Y")
    events = [_kill_event("X", "Y"), _hit_event("X", "Y")]
    _, sevts = calculate_round_scores(
        bots, events, round_num=3, storm_border=0, prev_storm_border=0,
        leader_emoji="Y",
    )
    bounty = [e for e in sevts if e.source == "leader_bounty"]
    assert len(bounty) == 1
    assert bounty[0] == ScoreEvent(emoji="X", source="leader_bounty", points=20)


# --- Cycle 2: Edge cases ---

def test_storm_kills_leader_no_bounty() -> None:
    """Storm kills (attacker='storm'): no bounty awarded."""
    bots = _make_bots("A", "B")
    events = [{"type": "kill", "attacker": "storm", "victim": "B"}]
    _, sevts = calculate_round_scores(
        bots, events, round_num=5, storm_border=2, prev_storm_border=0,
        leader_emoji="B",
    )
    bounty_evts = [e for e in sevts if e.source == "leader_bounty"]
    assert len(bounty_evts) == 0


def test_no_leader_no_bounty() -> None:
    """When leader_emoji is None, no bounty given even if kills happen."""
    bots = _make_bots("A", "B")
    events = [_kill_event("A", "B"), _hit_event("A", "B")]
    _, sevts = calculate_round_scores(
        bots, events, round_num=5, storm_border=0, prev_storm_border=0,
        leader_emoji=None,
    )
    bounty_evts = [e for e in sevts if e.source == "leader_bounty"]
    assert len(bounty_evts) == 0


# --- Cycle 3: Stacking ---

def test_clean_kill_stacks_with_bounty() -> None:
    """Clean kill + bounty: 10 (kill) + 5 (clean) + 20 (bounty) = 35 from combat."""
    bots = _make_bots("A", "B")
    # A kills B, dealt damage, took 0 damage → clean kill
    events = [_kill_event("A", "B"), _hit_event("A", "B", damage=30)]
    scores, sevts = calculate_round_scores(
        bots, events, round_num=5, storm_border=0, prev_storm_border=0,
        leader_emoji="B",
    )
    a_evts = [e for e in sevts if e.emoji == "A"]
    sources = {e.source: e.points for e in a_evts}
    assert sources["kill"] == 10
    assert sources["clean_kill"] == 5
    assert sources["leader_bounty"] == 20
    # Total for A: survival(1) + kill(10) + clean_kill(5) + bounty(20) + damage(1) = 37
    assert scores["A"] == 37


# --- Cycle 4: Feed formatter ---

def test_feed_shows_regicide() -> None:
    """Feed formatter produces REGICIDE text for leader_bounty event."""
    from agentgrounds.wars.cli.feed import format_feed_event

    evt = {"type": "leader_bounty", "killer": "A", "victim": "B", "bonus": 20}
    line = format_feed_event(evt, rnd=5)
    assert line is not None
    assert "REGICIDE" in line
    assert "A" in line
    assert "B" in line
    assert "+20" in line
