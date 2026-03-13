"""Tests for engine/combat.py — Bot class, damage calc, death resolution."""

from tests.conftest import make_bot

from engine.combat import (
    ATTACK_COST,
    DEFEND_COST,
    MOVE_COST,
    STARTING_DEFENSE,
    STARTING_ENERGY,
    STARTING_HP,
    STARTING_ATTACK_POWER,
    resolve_deaths,
)


# --- Bot defaults ---


class TestBotDefaults:
    def test_starting_hp(self):
        bot = make_bot()
        assert bot.hp == STARTING_HP == 100

    def test_starting_energy(self):
        bot = make_bot()
        assert bot.energy == STARTING_ENERGY == 100

    def test_starting_attack_power(self):
        bot = make_bot()
        assert bot.attack_power == STARTING_ATTACK_POWER == 15

    def test_starting_defense(self):
        bot = make_bot()
        assert bot.defense == STARTING_DEFENSE == 0

    def test_starts_alive(self):
        bot = make_bot()
        assert bot.alive is True

    def test_starts_zero_kills(self):
        bot = make_bot()
        assert bot.kills == 0
        assert bot.damage_dealt == 0
        assert bot.damage_taken == 0
        assert bot.rounds_survived == 0

    def test_position_set(self):
        bot = make_bot(x=3, y=7)
        assert bot.x == 3
        assert bot.y == 7


# --- can_act ---


class TestCanAct:
    def test_full_energy_can_act(self):
        assert make_bot(energy=100).can_act() is True

    def test_exactly_move_cost_can_act(self):
        assert make_bot(energy=MOVE_COST).can_act() is True

    def test_below_move_cost_cannot_act(self):
        assert make_bot(energy=MOVE_COST - 1).can_act() is False

    def test_zero_energy_cannot_act(self):
        assert make_bot(energy=0).can_act() is False


# --- apply_action_cost ---


class TestApplyActionCost:
    def test_move_cost(self):
        bot = make_bot(energy=100)
        bot.apply_action_cost("move")
        assert bot.energy == 100 - MOVE_COST

    def test_attack_cost(self):
        bot = make_bot(energy=100)
        bot.apply_action_cost("attack")
        assert bot.energy == 100 - ATTACK_COST

    def test_defend_cost(self):
        bot = make_bot(energy=100)
        bot.apply_action_cost("defend")
        assert bot.energy == 100 - DEFEND_COST

    def test_rest_is_free(self):
        bot = make_bot(energy=50)
        bot.apply_action_cost("rest")
        assert bot.energy == 50

    def test_unknown_action_no_cost(self):
        bot = make_bot(energy=100)
        bot.apply_action_cost("unknown")
        assert bot.energy == 100


# --- resolve_deaths ---


class TestResolveDeaths:
    def test_no_deaths_when_all_healthy(self):
        bots = [make_bot(hp=50), make_bot(hp=50)]
        elims = resolve_deaths(bots, round_num=10)
        assert elims == []
        assert all(b.alive for b in bots)

    def test_single_death(self):
        bots = [make_bot(hp=0, emoji="💀"), make_bot(hp=50)]
        elims = resolve_deaths(bots, round_num=5)
        assert len(elims) == 1
        assert elims[0]["emoji"] == "💀"
        assert elims[0]["round"] == 5
        assert bots[0].alive is False

    def test_death_priority_lowest_hp_first(self):
        b1 = make_bot(hp=-5, emoji="🅰️", energy=50, damage_dealt=100)
        b2 = make_bot(hp=0, emoji="🅱️", energy=50, damage_dealt=100)
        elims = resolve_deaths([b1, b2], round_num=10)
        assert [e["emoji"] for e in elims] == ["🅰️", "🅱️"]

    def test_death_priority_hp_tied_lower_energy_first(self):
        b1 = make_bot(hp=0, emoji="🅰️", energy=10, damage_dealt=100)
        b2 = make_bot(hp=0, emoji="🅱️", energy=50, damage_dealt=100)
        elims = resolve_deaths([b1, b2], round_num=10)
        assert [e["emoji"] for e in elims] == ["🅰️", "🅱️"]

    def test_death_priority_hp_energy_tied_less_damage_first(self):
        b1 = make_bot(hp=0, emoji="🅰️", energy=50, damage_dealt=10)
        b2 = make_bot(hp=0, emoji="🅱️", energy=50, damage_dealt=100)
        elims = resolve_deaths([b1, b2], round_num=10)
        assert [e["emoji"] for e in elims] == ["🅰️", "🅱️"]

    def test_already_dead_not_re_eliminated(self):
        bot = make_bot(hp=0, emoji="💀")
        bot.alive = False  # Already dead from earlier round
        elims = resolve_deaths([bot], round_num=20)
        assert elims == []

    def test_marks_dead_bots_not_alive(self):
        bot = make_bot(hp=0)
        resolve_deaths([bot], round_num=1)
        assert bot.alive is False
