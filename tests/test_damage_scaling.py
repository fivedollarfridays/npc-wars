"""Tests for round-based damage scaling."""

from engine.combat import get_round_bonus_attack, STARTING_ATTACK_POWER


class TestGetRoundBonusAttack:
    """Unit tests for get_round_bonus_attack()."""

    def test_no_bonus_round_1(self) -> None:
        assert get_round_bonus_attack(1) == 0

    def test_no_bonus_round_14(self) -> None:
        assert get_round_bonus_attack(14) == 0

    def test_no_bonus_round_15(self) -> None:
        assert get_round_bonus_attack(15) == 0

    def test_bonus_round_25(self) -> None:
        assert get_round_bonus_attack(25) == 2

    def test_bonus_round_35(self) -> None:
        assert get_round_bonus_attack(35) == 4

    def test_bonus_round_45(self) -> None:
        assert get_round_bonus_attack(45) == 6

    def test_bonus_round_55(self) -> None:
        assert get_round_bonus_attack(55) == 8


class TestDamageScalingInMatch:
    """Integration test: scaling applied during _execute_round."""

    def test_bot_attack_power_scales_in_late_rounds(self) -> None:
        """Verify attack_power reflects scaling during combat."""
        from engine.combat import Bot
        from engine.game import _execute_round
        from unittest.mock import patch

        bots = [
            Bot(name="A", emoji="A", bio="", author="t",
                decide_func=lambda s: ("rest",), x=0, y=0),
            Bot(name="B", emoji="B", bio="", author="t",
                decide_func=lambda s: ("rest",), x=5, y=5),
        ]
        with patch("engine.game.get_storm_border", return_value=0):
            _execute_round(bots, round_num=35, grid_size=10, storm_border=0)

        expected = STARTING_ATTACK_POWER + get_round_bonus_attack(35)
        assert bots[0].attack_power == expected
        assert bots[1].attack_power == expected
