"""Tests for Tier 5 'The Mirror' -- adaptive pattern-based rival."""

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


# ---------------------------------------------------------------------------
# Cycle 1: Identity
# ---------------------------------------------------------------------------


class TestMirrorIdentity:
    """Tier 5 should now be 'The Mirror'."""

    def test_mirror_name(self) -> None:
        config = generate_rival(5)
        assert config["name"] == "The Mirror"

    def test_mirror_tier_5(self) -> None:
        config = generate_rival(5)
        assert config["rival_tier"] == 5
        assert config["is_rival"] is True


# ---------------------------------------------------------------------------
# Cycle 2: Compilation with and without patterns
# ---------------------------------------------------------------------------


class TestMirrorCompilation:
    """Mirror compiles and runs with or without pattern data."""

    def test_compiles_without_patterns(self) -> None:
        config = generate_rival(5)
        compile(config["source"], "mirror_test", "exec")
        state = _make_state(5, 5, 100, 100, [_enemy(6, 5)])
        action = config["decide_func"](state)
        assert isinstance(action, tuple)
        assert len(action) >= 1

    def test_compiles_with_patterns_and_cap(self) -> None:
        patterns = {"at_range_1": {"attack": 0.8, "rest": 0.1, "defend": 0.1}}
        config = generate_rival(5, pattern_data=patterns, accuracy_cap=0.75)
        compile(config["source"], "mirror_patterns_test", "exec")
        state = _make_state(5, 5, 100, 100, [_enemy(6, 5)])
        action = config["decide_func"](state)
        assert isinstance(action, tuple)
        assert len(action) >= 1


# ---------------------------------------------------------------------------
# Cycle 3: Counter behavior + accuracy cap
# ---------------------------------------------------------------------------


class TestMirrorCounterBehavior:
    """Mirror counters predicted actions based on pattern data."""

    def test_counters_predicted_attack(self) -> None:
        """80% attack at_range_1 -> Mirror defends."""
        patterns = {"at_range_1": {"attack": 0.8, "rest": 0.1, "defend": 0.1}}
        config = generate_rival(5, pattern_data=patterns, accuracy_cap=1.0)
        state = _make_state(5, 5, 100, 100, [_enemy(6, 5)])
        action = config["decide_func"](state)
        assert action[0] == "defend", f"Expected defend vs predicted attack, got {action}"

    def test_counters_predicted_rest(self) -> None:
        """80% rest at_range_1 -> Mirror attacks."""
        patterns = {"at_range_1": {"rest": 0.8, "attack": 0.1, "defend": 0.1}}
        config = generate_rival(5, pattern_data=patterns, accuracy_cap=1.0)
        state = _make_state(5, 5, 100, 100, [_enemy(6, 5)])
        action = config["decide_func"](state)
        assert action[0] == "attack", f"Expected attack vs predicted rest, got {action}"

    def test_multi_context_highest_confidence(self) -> None:
        """When multiple contexts match, use highest confidence prediction."""
        patterns = {
            "at_range_1": {"attack": 0.6, "rest": 0.3, "defend": 0.1},
            "below_30_hp": {"rest": 0.9, "attack": 0.05, "defend": 0.05},
        }
        config = generate_rival(5, pattern_data=patterns, accuracy_cap=1.0)
        # HP < 30 + adjacent enemy -> both contexts match
        state = _make_state(5, 5, 25, 100, [_enemy(6, 5)])
        action = config["decide_func"](state)
        # below_30_hp has 90% rest -> counter is attack
        assert action[0] == "attack", f"Expected attack (counter rest@90%), got {action}"

    def test_accuracy_cap_zero_returns_random(self) -> None:
        """cap=0.0 -> never counters, picks random action."""
        import random as _rng
        _rng.seed(42)
        patterns = {"at_range_1": {"attack": 0.99, "rest": 0.005, "defend": 0.005}}
        config = generate_rival(5, pattern_data=patterns, accuracy_cap=0.0)
        state = _make_state(5, 5, 100, 100, [_enemy(6, 5)])
        # Run multiple times -- should never consistently counter
        actions = set()
        for _ in range(20):
            _rng.seed(_ * 7)
            action = config["decide_func"](state)
            actions.add(action[0])
        # With cap=0.0, we should see variety (not always "defend")
        assert len(actions) > 1, f"Expected variety with cap=0.0, got only {actions}"

    def test_accuracy_cap_one_always_counters(self) -> None:
        """cap=1.0 -> always counters."""
        patterns = {"at_range_1": {"attack": 0.99, "rest": 0.005, "defend": 0.005}}
        config = generate_rival(5, pattern_data=patterns, accuracy_cap=1.0)
        state = _make_state(5, 5, 100, 100, [_enemy(6, 5)])
        for _ in range(10):
            action = config["decide_func"](state)
            assert action[0] == "defend", f"cap=1.0 should always counter, got {action}"


# ---------------------------------------------------------------------------
# Cycle 4: Fallback, size, lobby
# ---------------------------------------------------------------------------


class TestMirrorFallbackAndSize:
    """Empty patterns fall back; source stays reasonable."""

    def test_empty_patterns_fallback(self) -> None:
        """No patterns -> falls back to old Grandmaster behavior."""
        config = generate_rival(5)
        # Low HP + adjacent enemy -> flee (move away)
        state = _make_state(5, 5, 20, 100, [_enemy(6, 5)])
        action = config["decide_func"](state)
        assert action[0] == "move", f"Expected flee (move) at low HP, got {action}"

    def test_source_size_reasonable(self) -> None:
        patterns = {f"ctx_{i}": {f"act_{j}": 0.1 for j in range(5)} for i in range(10)}
        config = generate_rival(5, pattern_data=patterns, accuracy_cap=0.75)
        assert len(config["source"]) < 15000


class TestMirrorLobbyIntegration:
    """Lobby generates valid Mirror config."""

    def test_lobby_generates_valid_config(self) -> None:
        from server.lobby import _generate_mirror_rival

        config = _generate_mirror_rival("nonexistent_player", conn=None)
        assert config["name"] == "The Mirror"
        assert config["rival_tier"] == 5
        state = _make_state(5, 5, 100, 100, [_enemy(6, 5)])
        action = config["decide_func"](state)
        assert isinstance(action, tuple)
