"""Behavioral tests for Tier 1 rival 'The Bully'.

Verifies that The Bully teaches the intended lesson: punish passive play
by always attacking adjacent enemies and never resting when enemies are
nearby.
"""

from __future__ import annotations

import pytest

from server.rival_factory import generate_rival


@pytest.fixture()
def bully() -> dict:
    """Generate the Tier 1 Bully rival."""
    return generate_rival(1)


def _make_state(
    me_x: int,
    me_y: int,
    me_hp: int,
    me_energy: int,
    enemies: list[dict],
    round_num: int = 5,
    grid_size: int = 10,
    storm_border: int = 0,
) -> dict:
    """Build a minimal but valid state dict for testing."""
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


def _enemy(
    emoji: str, x: int, y: int, hp: int = 80,
) -> dict:
    """Build a minimal enemy dict."""
    return {
        "emoji": emoji, "name": f"Bot{emoji}", "x": x, "y": y,
        "hp": hp, "max_hp": 100, "speed_class": "normal",
        "has_traps": False, "trap_count": 0, "weapon": "sword",
        "armor": "leather", "has_ability": False, "on_terrain": "open",
        "score": 0, "momentum_tier": 0, "is_leader": False,
    }


class TestBullyIdentity:
    """Verify name, tier, and metadata."""

    def test_name(self, bully: dict) -> None:
        assert bully["name"] == "The Bully"

    def test_is_rival(self, bully: dict) -> None:
        assert bully["is_rival"] is True
        assert bully["rival_tier"] == 1


class TestBullyAttacksAdjacent:
    """Core teaching behavior: Bully always attacks adjacent enemies."""

    def test_attacks_adjacent_enemy(self, bully: dict) -> None:
        """Bully attacks when enemy is adjacent (distance 1)."""
        state = _make_state(5, 5, 100, 100, [_enemy("\U0001f916", 6, 5)])
        action = bully["decide_func"](state)
        assert action[0] == "attack", f"Expected attack, got {action}"

    def test_attacks_adjacent_even_at_low_hp(self, bully: dict) -> None:
        """Bully does NOT rest when adjacent enemy exists, even at low HP."""
        state = _make_state(5, 5, 10, 50, [_enemy("\U0001f916", 5, 6)])
        action = bully["decide_func"](state)
        assert action[0] == "attack", f"Expected attack at low HP, got {action}"

    def test_attacks_adjacent_even_at_low_energy(self, bully: dict) -> None:
        """Bully does NOT rest when adjacent enemy exists, even at low energy."""
        state = _make_state(5, 5, 80, 5, [_enemy("\U0001f916", 4, 5)])
        action = bully["decide_func"](state)
        assert action[0] == "attack", f"Expected attack at low energy, got {action}"

    def test_does_not_rest_when_adjacent(self, bully: dict) -> None:
        """Bully never rests when an enemy is adjacent."""
        state = _make_state(5, 5, 30, 20, [_enemy("\U0001f916", 6, 5)])
        action = bully["decide_func"](state)
        assert action[0] != "rest", (
            f"Bully should not rest adjacent to enemy, got {action}"
        )

    def test_targets_weakest_adjacent(self, bully: dict) -> None:
        """With multiple adjacent enemies, Bully targets the weakest."""
        enemies = [
            _enemy("\U0001f916", 6, 5, hp=80),
            _enemy("\U0001f47e", 4, 5, hp=20),
        ]
        state = _make_state(5, 5, 100, 100, enemies)
        action = bully["decide_func"](state)
        assert action[0] == "attack"
        # Attack direction should be toward (4,5) = west
        assert action[1] == "west", f"Should target weakest (west), got {action}"


class TestBullyChases:
    """Bully chases enemies that are nearby but not adjacent."""

    def test_chases_nearby_enemy(self, bully: dict) -> None:
        """Bully moves toward enemies within chase range."""
        state = _make_state(5, 5, 100, 100, [_enemy("\U0001f916", 8, 5)])
        action = bully["decide_func"](state)
        assert action[0] in ("move", "attack"), f"Expected chase, got {action}"


class TestBullyEdgeCases:
    """Edge cases and safety tests."""

    def test_returns_valid_tuple(self, bully: dict) -> None:
        """Action is always a valid tuple."""
        state = _make_state(5, 5, 100, 100, [_enemy("\U0001f916", 6, 5)])
        action = bully["decide_func"](state)
        assert isinstance(action, tuple)
        assert len(action) >= 1

    def test_handles_no_enemies(self, bully: dict) -> None:
        """Bully handles empty enemy list without error."""
        state = _make_state(5, 5, 100, 100, [])
        action = bully["decide_func"](state)
        assert isinstance(action, tuple)

    def test_handles_storm_danger(self, bully: dict) -> None:
        """Bully flees storm when in danger zone."""
        # storm_border=3: tiles 0-2 and 7-9 are storm
        # Bot at (1,5) is in storm (1 < 3)
        state = _make_state(1, 5, 100, 100, [_enemy("\U0001f916", 8, 5)], storm_border=3)
        action = bully["decide_func"](state)
        assert action[0] == "move", f"Expected storm escape, got {action}"

    def test_source_compiles(self, bully: dict) -> None:
        """Bully source code compiles without syntax errors."""
        compile(bully["source"], "bully_test", "exec")
