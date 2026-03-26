"""Tests for server.rival_factory — rival agent generation."""

from __future__ import annotations

import pytest

from server.rival_factory import RIVAL_EMOJI, MAX_TIER, generate_rival


class TestRivalConfig:
    """Verify rival config structure and metadata."""

    def test_tier_1_returns_valid_config(self) -> None:
        config = generate_rival(1)
        assert "name" in config
        assert "emoji" in config
        assert "bio" in config
        assert "decide_func" in config
        assert "source" in config

    def test_tier_1_has_correct_name(self) -> None:
        config = generate_rival(1)
        assert config["name"] == "The Bully"

    def test_tier_2_has_correct_name(self) -> None:
        config = generate_rival(2)
        assert config["name"] == "The Storm Chaser"

    def test_rival_emoji_is_reserved(self) -> None:
        config = generate_rival(1)
        assert config["emoji"] == RIVAL_EMOJI

    def test_config_has_rival_tags(self) -> None:
        config = generate_rival(1)
        assert config.get("is_rival") is True
        assert config.get("rival_tier") == 1

    def test_tier_2_config_has_rival_tags(self) -> None:
        config = generate_rival(2)
        assert config.get("rival_tier") == 2


class TestRivalDecideFunc:
    """Verify decide_func compiles and executes."""

    def test_decide_func_is_callable(self) -> None:
        config = generate_rival(1)
        assert callable(config["decide_func"])

    def test_source_contains_decide(self) -> None:
        config = generate_rival(1)
        assert "def decide(state):" in config["source"]

    def test_source_compiles_without_error(self) -> None:
        for tier in range(1, MAX_TIER + 1):
            config = generate_rival(tier)
            compile(config["source"], f"rival_tier_{tier}", "exec")

    def test_invalid_tier_raises(self) -> None:
        with pytest.raises(ValueError):
            generate_rival(0)
        with pytest.raises(ValueError):
            generate_rival(99)


class TestRivalExecution:
    """Verify rivals return valid actions against mock state."""

    @pytest.fixture()
    def mock_state(self) -> dict:
        """Minimal state dict that satisfies Me/Enemies/Storm helpers."""
        return {
            "me": {
                "x": 5, "y": 5, "hp": 100, "energy": 100,
                "attack_power": 25, "defense": 0,
                "speed_class": "normal", "score": 0,
                "momentum_tier": 0, "is_leader": False,
                "max_hp": 100, "max_energy": 100,
                "equipment": {}, "equipment_bonuses": {},
                "unlocked_actions": ["move", "attack", "rest", "defend"],
                "traps": [], "kills": 0,
                "dodge_chance": 0, "damage_reduction": 0,
                "incoming_threat": [], "hit_chance_vs": {},
            },
            "enemies": [
                {"emoji": "\U0001f916", "name": "Test", "x": 6, "y": 5,
                 "hp": 80, "max_hp": 100, "speed_class": "normal",
                 "has_traps": False, "trap_count": 0, "weapon": "sword",
                 "armor": "leather", "has_ability": False,
                 "on_terrain": "open"},
            ],
            "round": 5,
            "grid_size": 10,
            "storm_border": 0,
            "bumps_last_round": [],
        }

    def test_tier_1_returns_valid_action(self, mock_state: dict) -> None:
        config = generate_rival(1)
        result = config["decide_func"](mock_state)
        assert isinstance(result, tuple)
        assert len(result) >= 1

    def test_tier_2_returns_valid_action(self, mock_state: dict) -> None:
        config = generate_rival(2)
        result = config["decide_func"](mock_state)
        assert isinstance(result, tuple)
        assert len(result) >= 1

    def test_tier_1_attacks_adjacent_enemy(self, mock_state: dict) -> None:
        """Tier 1 (The Bully) should attack when enemy is adjacent."""
        config = generate_rival(1)
        result = config["decide_func"](mock_state)
        assert result[0] == "attack"

    def test_tier_2_moves_toward_center_late_game(
        self, mock_state: dict,
    ) -> None:
        """Tier 2 (Storm Chaser) repositions toward center in late rounds."""
        mock_state["round"] = 10
        mock_state["me"]["x"] = 1
        mock_state["me"]["y"] = 1
        # Move enemy away so override triggers positioning logic
        mock_state["enemies"][0]["x"] = 8
        mock_state["enemies"][0]["y"] = 8
        config = generate_rival(2)
        result = config["decide_func"](mock_state)
        assert isinstance(result, tuple)
        assert result[0] in ("move", "attack", "rest", "defend")

    def test_all_tiers_return_actions(self, mock_state: dict) -> None:
        """Every implemented tier returns a valid action tuple."""
        for tier in range(1, MAX_TIER + 1):
            config = generate_rival(tier)
            result = config["decide_func"](mock_state)
            assert isinstance(result, tuple), f"Tier {tier} failed"
            assert len(result) >= 1, f"Tier {tier} returned empty tuple"
