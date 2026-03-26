"""Tests for Tier 3 Economist rework (T53.3)."""

from __future__ import annotations

import pytest

from server.rival_factory import generate_rival


@pytest.fixture()
def economist():
    return generate_rival(3)


def _make_state(me_hp, me_energy, enemies, round_num=5, grid_size=10, storm_border=0):
    return {
        "me": {
            "x": 5, "y": 5, "hp": me_hp, "energy": me_energy,
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


def _enemy(x, y, hp=80):
    return {
        "emoji": "\U0001f916", "name": "Test", "x": x, "y": y,
        "hp": hp, "max_hp": 100, "speed_class": "normal",
        "has_traps": False, "trap_count": 0, "weapon": "sword",
        "armor": "leather", "has_ability": False, "on_terrain": "open",
        "score": 0, "momentum_tier": 0, "is_leader": False,
    }


# ---------------------------------------------------------------------------
# Cycle 1: Identity
# ---------------------------------------------------------------------------

class TestEconomistIdentity:
    def test_name(self, economist):
        assert economist["name"] == "The Economist"

    def test_tier(self, economist):
        assert economist["rival_tier"] == 3

    def test_is_rival(self, economist):
        assert economist["is_rival"] is True


# ---------------------------------------------------------------------------
# Cycle 2: Behavior
# ---------------------------------------------------------------------------

class TestEconomistBehavior:
    def test_rests_at_low_energy_no_adjacent(self, economist):
        """Economist rests when energy < 30 and no adjacent enemy."""
        state = _make_state(100, 20, [_enemy(8, 5)])  # Enemy far away
        action = economist["decide_func"](state)
        assert action[0] == "rest", f"Expected rest at low energy, got {action}"

    def test_defends_at_low_energy_with_adjacent(self, economist):
        """Economist defends when energy < 30 and enemy adjacent."""
        state = _make_state(100, 20, [_enemy(6, 5)])  # Enemy adjacent
        action = economist["decide_func"](state)
        assert action[0] in ("defend", "rest"), f"Expected defend/rest at low energy, got {action}"

    def test_attacks_at_high_energy_with_adjacent(self, economist):
        """Economist attacks when energy >= 60 and enemy adjacent."""
        state = _make_state(100, 80, [_enemy(6, 5)])  # High energy, adjacent
        action = economist["decide_func"](state)
        assert action[0] == "attack", f"Expected attack at high energy, got {action}"

    def test_rests_at_safe_distance_medium_energy(self, economist):
        """Economist rests at safe distance when energy < 60."""
        state = _make_state(100, 45, [_enemy(9, 5)])  # Far enemy, medium energy
        action = economist["decide_func"](state)
        assert action[0] == "rest", f"Expected rest to build reserves, got {action}"

    def test_source_compiles(self, economist):
        compile(economist["source"], "economist_test", "exec")

    def test_returns_valid_tuple(self, economist):
        state = _make_state(100, 50, [_enemy(6, 5)])
        action = economist["decide_func"](state)
        assert isinstance(action, tuple)


# ---------------------------------------------------------------------------
# Cycle 3: Debrief
# ---------------------------------------------------------------------------

class TestEconomistDebrief:
    def test_debrief_identifies_energy_starved(self):
        from server.rival_debrief import analyze_rival_match
        from server.rival_factory import RIVAL_EMOJI

        match = {
            "match_id": 1,
            "rounds": [
                {"round": 5, "storm_border": 0, "positions": [
                    {"emoji": "\U0001f916", "x": 5, "y": 5, "hp": 60,
                     "energy": 15, "action": "rest", "alive": True, "max_hp": 100},
                    {"emoji": RIVAL_EMOJI, "x": 6, "y": 5, "hp": 90,
                     "energy": 70, "action": "attack west", "alive": True, "max_hp": 100},
                ], "events": []},
            ],
            "eliminations": [],
            "winner": RIVAL_EMOJI,
            "stats": {},
        }
        result = analyze_rival_match(match, "\U0001f916", 3)
        assert result["tier"] == 3
        assert "energy" in result["lesson"].lower()
        # Must identify the specific starved rounds (not generic fallback)
        assert "energy_starved_rounds" in result
        assert 5 in result["energy_starved_rounds"]

    def test_debrief_good_energy_management(self):
        from server.rival_debrief import analyze_rival_match
        from server.rival_factory import RIVAL_EMOJI

        match = {
            "match_id": 1,
            "rounds": [
                {"round": 5, "storm_border": 0, "positions": [
                    {"emoji": "\U0001f916", "x": 5, "y": 5, "hp": 80,
                     "energy": 65, "action": "attack east", "alive": True, "max_hp": 100},
                    {"emoji": RIVAL_EMOJI, "x": 6, "y": 5, "hp": 70,
                     "energy": 60, "action": "attack west", "alive": True, "max_hp": 100},
                ], "events": []},
            ],
            "eliminations": [],
            "winner": "\U0001f916",
            "stats": {},
        }
        result = analyze_rival_match(match, "\U0001f916", 3)
        assert result["tier"] == 3
        # No starved rounds when energy stayed healthy
        assert result.get("energy_starved_rounds", []) == []
        assert "good" in result["lesson"].lower() or "kept pace" in result["lesson"].lower()

    def test_debrief_has_required_keys(self):
        from server.rival_debrief import analyze_rival_match
        from server.rival_factory import RIVAL_EMOJI

        match = {
            "match_id": 1,
            "rounds": [],
            "eliminations": [],
            "winner": RIVAL_EMOJI,
            "stats": {},
        }
        result = analyze_rival_match(match, "\U0001f916", 3)
        assert "lesson" in result
        assert "tip" in result
        assert "what_happened" in result
        assert "key_round" in result
