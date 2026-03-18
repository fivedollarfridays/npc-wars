"""Tests for engine/scoring.py — per-round point calculation."""

from __future__ import annotations

from engine.scoring import ScoreEvent, calculate_round_scores


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _bot(emoji: str, *, alive: bool = True, hp: int = 50) -> dict:
    """Minimal bot-like dict for scoring tests."""
    return {"emoji": emoji, "alive": alive, "hp": hp}


def _hit(attacker: str, target: str, damage: int) -> dict:
    return {"type": "hit", "attacker": attacker, "target": target, "damage": damage}


def _kill(attacker: str, victim: str) -> dict:
    return {"type": "kill", "attacker": attacker, "victim": victim}


# ---------------------------------------------------------------------------
# Cycle 1: survival & dead bots
# ---------------------------------------------------------------------------

def test_dead_bot_scores_zero() -> None:
    bots = [_bot("A", alive=False), _bot("B")]
    scores, events = calculate_round_scores(bots, [], round_num=1,
                                            storm_border=0, prev_storm_border=0)
    assert scores["A"] == 0


def test_alive_bot_gets_survival_point() -> None:
    bots = [_bot("A"), _bot("B")]
    scores, _ = calculate_round_scores(bots, [], round_num=1,
                                       storm_border=0, prev_storm_border=0)
    assert scores["A"] >= 1  # at least survival


# ---------------------------------------------------------------------------
# Cycle 2: kill & clean kill
# ---------------------------------------------------------------------------

def test_kill_awards_ten_points() -> None:
    bots = [_bot("A"), _bot("B"), _bot("C")]
    events = [_kill("A", "B"), _hit("A", "B", 25), _hit("C", "A", 5)]
    scores, _ = calculate_round_scores(bots, events, round_num=1,
                                       storm_border=0, prev_storm_border=0)
    # survival(1) + kill(10) + damage(25//25=1) = 12  (took damage → no clean kill)
    assert scores["A"] == 12


def test_clean_kill_bonus() -> None:
    """Kill + zero damage taken this round = +5 bonus on top of kill points."""
    bots = [_bot("A"), _bot("B")]
    events = [_kill("A", "B"), _hit("A", "B", 25)]
    # A took 0 damage → clean kill
    scores, _ = calculate_round_scores(bots, events, round_num=1,
                                       storm_border=0, prev_storm_border=0)
    # survival(1) + kill(10) + clean_kill(5) + damage(1) = 17
    assert scores["A"] == 17


def test_no_clean_kill_when_damage_taken() -> None:
    """Kill but also took damage → no clean kill bonus."""
    bots = [_bot("A"), _bot("B")]
    events = [_kill("A", "B"), _hit("A", "B", 25), _hit("B", "A", 10)]
    scores, _ = calculate_round_scores(bots, events, round_num=1,
                                       storm_border=0, prev_storm_border=0)
    # survival(1) + kill(10) + damage(1) = 12, no clean kill
    assert scores["A"] == 12


# ---------------------------------------------------------------------------
# Cycle 3: full HP & damage dealt
# ---------------------------------------------------------------------------

def test_full_hp_bonus() -> None:
    bots = [_bot("A", hp=100), _bot("B")]
    scores, _ = calculate_round_scores(bots, [], round_num=1,
                                       storm_border=0, prev_storm_border=0)
    # survival(1) + full_hp(2) = 3
    assert scores["A"] == 3


def test_damage_dealt_points() -> None:
    bots = [_bot("A"), _bot("B")]
    events = [_hit("A", "B", 50)]
    scores, _ = calculate_round_scores(bots, events, round_num=1,
                                       storm_border=0, prev_storm_border=0)
    # survival(1) + damage(50//25=2) = 3
    assert scores["A"] == 3


def test_damage_dealt_floors() -> None:
    bots = [_bot("A"), _bot("B")]
    events = [_hit("A", "B", 24)]
    scores, _ = calculate_round_scores(bots, events, round_num=1,
                                       storm_border=0, prev_storm_border=0)
    # survival(1) + damage(24//25=0) = 1
    assert scores["A"] == 1


# ---------------------------------------------------------------------------
# Cycle 4: storm survivor & last standing
# ---------------------------------------------------------------------------

def test_storm_survivor_on_activation() -> None:
    """Storm just activated (prev=0, current>0) → alive bots get +3."""
    bots = [_bot("A"), _bot("B")]
    scores, _ = calculate_round_scores(bots, [], round_num=5,
                                       storm_border=1, prev_storm_border=0)
    # survival(1) + storm_survivor(3) = 4
    assert scores["A"] == 4


def test_no_storm_survivor_after_first_round() -> None:
    """Storm already active (prev>0) → no bonus."""
    bots = [_bot("A"), _bot("B")]
    scores, _ = calculate_round_scores(bots, [], round_num=6,
                                       storm_border=2, prev_storm_border=1)
    assert scores["A"] == 1  # just survival


def test_last_standing() -> None:
    """Only one alive bot → +15 last standing."""
    bots = [_bot("A"), _bot("B", alive=False)]
    scores, _ = calculate_round_scores(bots, [], round_num=10,
                                       storm_border=0, prev_storm_border=0)
    # survival(1) + last_standing(15) = 16
    assert scores["A"] == 16


def test_no_last_standing_with_multiple_alive() -> None:
    bots = [_bot("A"), _bot("B")]
    scores, _ = calculate_round_scores(bots, [], round_num=10,
                                       storm_border=0, prev_storm_border=0)
    assert scores["A"] == 1  # just survival


# ---------------------------------------------------------------------------
# Score events
# ---------------------------------------------------------------------------

def test_score_events_returned() -> None:
    """Each score source should produce a ScoreEvent."""
    bots = [_bot("A", hp=100), _bot("B", alive=False)]
    scores, events = calculate_round_scores(bots, [], round_num=5,
                                            storm_border=0, prev_storm_border=0)
    sources = {e.source for e in events if e.emoji == "A"}
    assert "survival" in sources
    assert "full_hp" in sources
    assert "last_standing" in sources


def test_score_event_dataclass() -> None:
    evt = ScoreEvent(emoji="A", source="survival", points=1)
    assert evt.emoji == "A"
    assert evt.source == "survival"
    assert evt.points == 1
