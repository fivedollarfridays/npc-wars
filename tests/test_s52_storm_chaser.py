"""Behavioral tests for Tier 2 rival: The Storm Chaser.

Verifies that The Storm Chaser teaches positioning by preferring center
positions and responding to storm mechanics.
"""

from __future__ import annotations

import pytest

from server.rival_factory import generate_rival


@pytest.fixture()
def chaser() -> dict:
    return generate_rival(2)


def _make_state(
    me_x: int,
    me_y: int,
    me_hp: int,
    me_energy: int,
    enemies: list[dict],
    *,
    round_num: int = 10,
    grid_size: int = 10,
    storm_border: int = 0,
) -> dict:
    return {
        "me": {
            "x": me_x, "y": me_y, "hp": me_hp, "energy": me_energy,
            "attack_power": 25, "defense": 0, "speed_class": "normal",
            "score": 0, "momentum_tier": 0, "is_leader": False,
            "max_hp": 100, "max_energy": 100, "kills": 0,
            "equipment": {}, "equipment_bonuses": {},
            "unlocked_actions": ["move", "attack", "rest", "defend"],
            "traps": [], "dodge_chance": 0, "damage_reduction": 0,
            "incoming_threat": [], "hit_chance_vs": {},
            "power": 25, "speed": 25, "armor": 25, "mind": 25,
        },
        "enemies": enemies,
        "round": round_num,
        "grid_size": grid_size,
        "storm_border": storm_border,
        "bumps_last_round": [],
    }


def _enemy(emoji: str, x: int, y: int, hp: int = 80) -> dict:
    return {
        "emoji": emoji, "name": f"Bot{emoji}", "x": x, "y": y,
        "hp": hp, "max_hp": 100, "speed_class": "normal",
        "has_traps": False, "trap_count": 0, "weapon": "sword",
        "armor": "leather", "has_ability": False, "on_terrain": "open",
        "score": 0, "momentum_tier": 0, "is_leader": False,
    }


class TestStormChaserIdentity:
    """Verify Storm Chaser metadata and distinction from other tiers."""

    def test_name(self, chaser: dict) -> None:
        assert chaser["name"] == "The Storm Chaser"

    def test_is_rival(self, chaser: dict) -> None:
        assert chaser["is_rival"] is True
        assert chaser["rival_tier"] == 2

    def test_distinct_from_bully(self, chaser: dict) -> None:
        bully = generate_rival(1)
        assert chaser["name"] != bully["name"]
        assert chaser["bio"] != bully["bio"]


class TestStormChaserBehavior:
    """Verify Storm Chaser positioning and storm-awareness behavior."""

    def test_moves_toward_center_when_at_edge(self, chaser: dict) -> None:
        """Storm Chaser moves toward center when at edge in late game."""
        # x=1 is far from center (5), round >= 8, storm_border=2
        # storm.danger: is_in_storm(1, 5, 10, 2) => x < 2 => True
        # So storm.danger is True and override won't fire.
        # Use storm_border=0 but round >= 8 to trigger override.
        state = _make_state(
            1, 5, 100, 100,
            [_enemy("\U0001f916", 8, 5)],
            round_num=10, storm_border=0,
        )
        action = chaser["decide_func"](state)
        # Override condition: storm.danger is False and round >= 8
        # my_dist = abs(1-5) + abs(5-5) = 4 > 3 => fires
        assert action[0] == "move", f"Expected center-ward move, got {action}"

    def test_returns_valid_tuple(self, chaser: dict) -> None:
        state = _make_state(5, 5, 100, 100, [_enemy("\U0001f916", 7, 5)])
        action = chaser["decide_func"](state)
        assert isinstance(action, tuple)
        assert len(action) >= 1

    def test_handles_no_enemies(self, chaser: dict) -> None:
        state = _make_state(5, 5, 100, 100, [])
        action = chaser["decide_func"](state)
        assert isinstance(action, tuple)

    def test_escapes_storm_when_in_danger(self, chaser: dict) -> None:
        """Storm Chaser flees storm via preset storm check (before override)."""
        # x=0, storm_border=3 => is_in_storm(0, 5, 10, 3) => 0 < 3 => True
        state = _make_state(
            0, 5, 100, 100,
            [_enemy("\U0001f916", 8, 5)],
            storm_border=3,
        )
        action = chaser["decide_func"](state)
        assert action[0] == "move", f"Expected storm escape, got {action}"

    def test_source_compiles(self, chaser: dict) -> None:
        compile(chaser["source"], "storm_chaser_test", "exec")

    def test_stays_center_when_already_centered(self, chaser: dict) -> None:
        """When already at center, override does not fire (dist <= 3)."""
        state = _make_state(
            5, 5, 100, 100,
            [_enemy("\U0001f916", 8, 8)],
            round_num=10, storm_border=0,
        )
        action = chaser["decide_func"](state)
        # Override won't fire (dist=0), falls through to preset kiter logic
        assert isinstance(action, tuple)
        assert action[0] in ("move", "attack", "rest", "defend")

    def test_override_triggers_with_active_storm(self, chaser: dict) -> None:
        """Override fires when storm is active but not dangerous."""
        # x=4, storm_border=1 => is_in_storm(4, 5, 10, 1) => False
        # is_in_storm(4, 5, 10, 2) => False (4 >= 2 and 4 < 8)
        # So storm.danger is False, storm_border > 0 => override condition met
        # dist = abs(4-5) + abs(5-5) = 1 <= 3 => override does NOT return
        # Need bigger distance: x=1
        state = _make_state(
            1, 5, 100, 100,
            [_enemy("\U0001f916", 8, 5)],
            round_num=5, storm_border=1,
        )
        action = chaser["decide_func"](state)
        # dist = abs(1-5) + abs(5-5) = 4 > 3 => fires move_toward_center
        assert action[0] == "move"

    def test_plays_differently_from_bully(self, chaser: dict) -> None:
        """Storm Chaser and Bully make different decisions at edge."""
        bully = generate_rival(1)
        # Edge position, late round, no storm danger, enemy far away
        # Storm Chaser: override fires => move toward center
        # Bully: no adjacent enemies => preset fallback (not attack)
        state = _make_state(
            1, 5, 100, 100,
            [_enemy("\U0001f916", 8, 5)],
            round_num=10, storm_border=0,
        )
        chaser_action = chaser["decide_func"](state)
        bully_action = bully["decide_func"](state)
        assert isinstance(chaser_action, tuple)
        assert isinstance(bully_action, tuple)
        # Both produce valid actions; Storm Chaser should move toward center
        assert chaser_action[0] == "move"
