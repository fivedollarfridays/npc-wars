"""Tests for engine/levels.py — level progression table and calculator."""

from __future__ import annotations


# ── Cycle 1: LEVEL_TABLE structure ──────────────────────────────────


def test_level_table_has_all_defined_milestone_levels():
    """The hand-authored milestone levels must all be present."""
    from engine.levels import LEVEL_TABLE

    milestone_levels = {1, 2, 3, 5, 8, 10, 12, 15, 18, 22, 25, 30}
    for lvl in milestone_levels:
        assert lvl in LEVEL_TABLE, f"Level {lvl} missing from LEVEL_TABLE"


def test_level_table_covers_1_through_30():
    """LEVEL_TABLE must have entries for every level 1-30 (interpolated)."""
    from engine.levels import LEVEL_TABLE

    for lvl in range(1, 31):
        assert lvl in LEVEL_TABLE, f"Level {lvl} missing"
        entry = LEVEL_TABLE[lvl]
        assert "xp_required" in entry
        assert "line_budget" in entry


# ── Cycle 2: XP monotonically increasing, interpolation sanity ──────


def test_xp_monotonically_increasing():
    """XP requirements must strictly increase with level."""
    from engine.levels import LEVEL_TABLE

    prev_xp = -1
    for lvl in range(1, 31):
        xp = LEVEL_TABLE[lvl]["xp_required"]
        assert xp > prev_xp, f"Level {lvl} XP ({xp}) not > prev ({prev_xp})"
        prev_xp = xp


def test_interpolated_level_4_between_3_and_5():
    """Level 4 should be interpolated between level 3 (250) and level 5 (600)."""
    from engine.levels import LEVEL_TABLE

    assert LEVEL_TABLE[4]["xp_required"] == 425  # 250 + 0.5*(600-250)
    assert LEVEL_TABLE[4]["line_budget"] == 87  # 75 + 0.5*(100-75) = 87.5 -> 87


# ── Cycle 3: level_from_xp ─────────────────────────────────────────


def test_level_from_xp_zero():
    from engine.levels import level_from_xp

    assert level_from_xp(0) == 1


def test_level_from_xp_boundary_values():
    """Test exact boundary: 99 XP -> level 1, 100 XP -> level 2, 250 -> level 3."""
    from engine.levels import level_from_xp

    assert level_from_xp(99) == 1
    assert level_from_xp(100) == 2
    assert level_from_xp(250) == 3


def test_level_from_xp_max():
    """25000+ XP should give level 30."""
    from engine.levels import level_from_xp

    assert level_from_xp(25000) == 30
    assert level_from_xp(999999) == 30


# ── Cycle 4: xp_for_next_level / xp_to_next_level ──────────────────


def test_xp_for_next_level_at_level_1():
    from engine.levels import xp_for_next_level

    assert xp_for_next_level(1) == 100  # level 2 threshold


def test_xp_for_next_level_at_max():
    """At max level, return the max level's own XP (no next level)."""
    from engine.levels import xp_for_next_level, LEVEL_TABLE, MAX_LEVEL

    assert xp_for_next_level(MAX_LEVEL) == LEVEL_TABLE[MAX_LEVEL]["xp_required"]


def test_xp_to_next_level_remaining():
    from engine.levels import xp_to_next_level

    # Level 1, 50 XP -> need 100 total for level 2, remaining = 50
    assert xp_to_next_level(1, 50) == 50
    # Level 1, 0 XP -> remaining = 100
    assert xp_to_next_level(1, 0) == 100
    # Level 2, 100 XP -> need 250 for level 3, remaining = 150
    assert xp_to_next_level(2, 100) == 150


def test_xp_to_next_level_at_max():
    """At max level, remaining XP should be 0."""
    from engine.levels import xp_to_next_level, MAX_LEVEL

    assert xp_to_next_level(MAX_LEVEL, 99999) == 0


# ── Cycle 5: LevelUnlocks and unlocks_at_level ─────────────────────


def test_unlocks_at_level_1():
    """Level 1 gives starting actions and decide callback."""
    from engine.levels import unlocks_at_level

    unlocks = unlocks_at_level(1)
    assert unlocks.actions == {"move", "attack", "rest", "defend"}
    assert unlocks.callbacks == {"decide"}
    assert unlocks.line_budget == 50


def test_unlocks_at_level_5_cumulative():
    """Level 5 includes all actions from levels 1, 3, and 5."""
    from engine.levels import unlocks_at_level

    unlocks = unlocks_at_level(5)
    assert "move" in unlocks.actions  # from level 1
    assert "ranged_attack" in unlocks.actions  # from level 3
    assert "dash" in unlocks.actions  # from level 5
    assert "on_kill" in unlocks.callbacks  # from level 5
    assert unlocks.line_budget == 100


def test_unlocks_at_level_30_has_everything():
    """Level 30 should have all actions and callbacks ever unlocked."""
    from engine.levels import unlocks_at_level

    unlocks = unlocks_at_level(30)
    all_actions = {
        "move", "attack", "rest", "defend", "ranged_attack",
        "dash", "taunt", "trap", "use_ability",
    }
    all_callbacks = {
        "decide", "on_kill", "setup", "react", "power_up", "evolve",
    }
    assert unlocks.actions == all_actions
    assert unlocks.callbacks == all_callbacks
    assert unlocks.line_budget == 300


def test_level_unlocks_is_dataclass():
    """LevelUnlocks should be a proper dataclass."""
    from dataclasses import fields

    from engine.levels import LevelUnlocks

    names = {f.name for f in fields(LevelUnlocks)}
    assert names == {"actions", "callbacks", "line_budget"}
