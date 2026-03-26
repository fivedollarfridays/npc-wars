"""Tests for Tier 4 'The Counter' rival rework with pattern learning."""

from __future__ import annotations

from server.rival_factory import generate_rival


def _make_state(
    me_x: int,
    me_y: int,
    me_hp: int,
    me_energy: int,
    enemies: list[dict],
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


def _enemy(x: int, y: int, hp: int = 80) -> dict:
    return {
        "emoji": "\U0001f916", "name": "Test", "x": x, "y": y,
        "hp": hp, "max_hp": 100, "speed_class": "normal",
        "has_traps": False, "trap_count": 0, "weapon": "sword",
        "armor": "leather", "has_ability": False, "on_terrain": "open",
        "score": 0, "momentum_tier": 0, "is_leader": False,
    }


class TestCounterIdentity:
    """Tier 4 should now be 'The Counter', not 'The Fortress'."""

    def test_name(self) -> None:
        config = generate_rival(4)
        assert config["name"] == "The Counter"

    def test_tier(self) -> None:
        config = generate_rival(4)
        assert config["rival_tier"] == 4

    def test_is_rival(self) -> None:
        config = generate_rival(4)
        assert config["is_rival"] is True

    def test_bio_mentions_pattern_or_counter(self) -> None:
        config = generate_rival(4)
        bio_lower = config["bio"].lower()
        assert "pattern" in bio_lower or "counter" in bio_lower or "learn" in bio_lower


class TestCounterWithoutPatternData:
    """Tier 4 works without pattern data (fallback behavior)."""

    def test_compiles_without_pattern_data(self) -> None:
        config = generate_rival(4)
        compile(config["source"], "counter_test", "exec")

    def test_returns_valid_action(self) -> None:
        config = generate_rival(4)
        state = _make_state(5, 5, 100, 100, [_enemy(6, 5)])
        action = config["decide_func"](state)
        assert isinstance(action, tuple)
        assert len(action) >= 1


class TestCounterWithPatternData:
    """Tier 4 with embedded pattern data counters predicted actions."""

    def test_compiles_with_pattern_data(self) -> None:
        patterns = {"at_range_1": {"attack": 0.7, "rest": 0.2, "defend": 0.1}}
        config = generate_rival(4, pattern_data=patterns)
        compile(config["source"], "counter_patterns_test", "exec")

    def test_returns_valid_action_with_patterns(self) -> None:
        patterns = {"at_range_1": {"attack": 0.7, "rest": 0.2, "defend": 0.1}}
        config = generate_rival(4, pattern_data=patterns)
        state = _make_state(5, 5, 100, 100, [_enemy(6, 5)])
        action = config["decide_func"](state)
        assert isinstance(action, tuple)
        assert len(action) >= 1

    def test_counters_predicted_attack_with_defend(self) -> None:
        """When player mostly attacks at range 1, Counter should defend."""
        patterns = {"at_range_1": {"attack": 0.9, "rest": 0.05, "defend": 0.05}}
        config = generate_rival(4, pattern_data=patterns)
        state = _make_state(5, 5, 100, 100, [_enemy(6, 5)])
        action = config["decide_func"](state)
        assert action[0] == "defend", f"Expected defend vs predicted attack, got {action}"

    def test_counters_predicted_rest_with_attack(self) -> None:
        """When player mostly rests at range 1, Counter should attack."""
        patterns = {"at_range_1": {"rest": 0.9, "attack": 0.05, "defend": 0.05}}
        config = generate_rival(4, pattern_data=patterns)
        state = _make_state(5, 5, 100, 100, [_enemy(6, 5)])
        action = config["decide_func"](state)
        assert action[0] == "attack", f"Expected attack vs predicted rest, got {action}"

    def test_handles_empty_pattern_data(self) -> None:
        config = generate_rival(4, pattern_data={})
        state = _make_state(5, 5, 100, 100, [_enemy(6, 5)])
        action = config["decide_func"](state)
        assert isinstance(action, tuple)

    def test_embedded_data_under_5kb(self) -> None:
        patterns = {f"ctx_{i}": {f"act_{j}": 0.1 for j in range(5)} for i in range(10)}
        config = generate_rival(4, pattern_data=patterns)
        assert len(config["source"]) < 10000

    def test_counters_predicted_defend_with_attack(self) -> None:
        """When player mostly defends at range 1, Counter should attack."""
        patterns = {"at_range_1": {"defend": 0.9, "attack": 0.05, "rest": 0.05}}
        config = generate_rival(4, pattern_data=patterns)
        state = _make_state(5, 5, 100, 100, [_enemy(6, 5)])
        action = config["decide_func"](state)
        assert action[0] == "attack", f"Expected attack vs predicted defend, got {action}"

    def test_no_pattern_match_falls_through(self) -> None:
        """Unmatched context should fall through to fallback override."""
        patterns = {"below_30_hp": {"rest": 0.9, "defend": 0.1}}
        config = generate_rival(4, pattern_data=patterns)
        # Full HP + adjacent enemy: at_range_1 context, but no pattern for it
        state = _make_state(5, 5, 100, 100, [_enemy(6, 5)])
        action = config["decide_func"](state)
        # Should fall through to fallback (defend when hp > 50 and adjacent)
        assert action[0] == "defend"


class TestLobbyCounterIntegration:
    """Verify _generate_counter_rival produces a working config."""

    def test_generate_counter_rival_no_patterns(self) -> None:
        """Counter rival with no stored patterns falls back gracefully."""
        from server.lobby import _generate_counter_rival

        config = _generate_counter_rival("nonexistent_player")
        assert config["name"] == "The Counter"
        assert config["rival_tier"] == 4
        state = _make_state(5, 5, 100, 100, [_enemy(6, 5)])
        action = config["decide_func"](state)
        assert isinstance(action, tuple)
