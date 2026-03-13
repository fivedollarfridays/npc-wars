"""Tests for energy clamping — energy should never go below 0."""

from tests.conftest import make_bot

from engine.combat import ATTACK_COST


class TestEnergyClamp:
    def test_energy_does_not_go_negative(self):
        bot = make_bot(energy=5)
        bot.apply_action_cost("attack")  # cost 15, energy 5 -> should be 0, not -10
        assert bot.energy >= 0

    def test_energy_clamped_to_zero(self):
        bot = make_bot(energy=5)
        bot.apply_action_cost("attack")
        assert bot.energy == 0

    def test_exact_cost_results_in_zero(self):
        bot = make_bot(energy=ATTACK_COST)
        bot.apply_action_cost("attack")
        assert bot.energy == 0

    def test_surplus_energy_normal_deduction(self):
        bot = make_bot(energy=100)
        bot.apply_action_cost("attack")
        assert bot.energy == 100 - ATTACK_COST
