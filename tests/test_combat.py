"""Tests for engine/combat.py — Bot class, damage calc, death resolution."""

from tests.conftest import make_bot

from engine.stats import (
    DEFAULT_ALLOCATION,
    DerivedStats,
    StatAllocation,
    calculate_derived,
)

from engine.combat import (
    ACTION_COSTS,
    ATTACK_COST,
    DEFEND_COST,
    MOVE_COST,
    REST_HEAL,
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
        assert bot.attack_power == STARTING_ATTACK_POWER == 25

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
        # Third alive bot prevents "spare the best" rule from triggering
        alive = make_bot(hp=50, emoji="🟢")
        b1 = make_bot(hp=-5, emoji="🅰️", energy=50, damage_dealt=100)
        b2 = make_bot(hp=0, emoji="🅱️", energy=50, damage_dealt=100)
        elims = resolve_deaths([alive, b1, b2], round_num=10)
        assert [e["emoji"] for e in elims] == ["🅰️", "🅱️"]

    def test_death_priority_hp_tied_lower_energy_first(self):
        alive = make_bot(hp=50, emoji="🟢")
        b1 = make_bot(hp=0, emoji="🅰️", energy=10, damage_dealt=100)
        b2 = make_bot(hp=0, emoji="🅱️", energy=50, damage_dealt=100)
        elims = resolve_deaths([alive, b1, b2], round_num=10)
        assert [e["emoji"] for e in elims] == ["🅰️", "🅱️"]

    def test_death_priority_hp_energy_tied_less_damage_first(self):
        alive = make_bot(hp=50, emoji="🟢")
        b1 = make_bot(hp=0, emoji="🅰️", energy=50, damage_dealt=10)
        b2 = make_bot(hp=0, emoji="🅱️", energy=50, damage_dealt=100)
        elims = resolve_deaths([alive, b1, b2], round_num=10)
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


# --- Balance constants (T8.1) ---


class TestBalanceConstants:
    def test_attack_power_is_25(self):
        assert STARTING_ATTACK_POWER == 25

    def test_rest_heal_is_5(self):
        assert REST_HEAL == 5

    def test_attack_cost_is_10(self):
        assert ATTACK_COST == 10

    def test_action_costs_attack_is_10(self):
        assert ACTION_COSTS["attack"] == 10


# --- Stat allocation on Bot (T27.3) ---


class TestBotStatAllocation:
    def test_bot_default_stats(self):
        """Bot() without stat_allocation has stats == DEFAULT_ALLOCATION."""
        bot = make_bot()
        assert bot.stats == DEFAULT_ALLOCATION

    def test_bot_default_hp_100(self):
        """Bot() without stat_allocation has hp == 100."""
        bot = make_bot()
        assert bot.hp == 100

    def test_bot_default_energy_100(self):
        """Bot() without stat_allocation has energy == 100."""
        bot = make_bot()
        assert bot.energy == 100

    def test_bot_custom_stats_hp(self):
        """Bot with high armor (50) has hp == 95 (versatility-penalized)."""
        alloc = StatAllocation(15, 15, 50, 20)
        bot = make_bot(stat_allocation=alloc)
        expected_hp = calculate_derived(alloc).max_hp
        assert expected_hp == 95
        assert bot.hp == 95

    def test_bot_custom_stats_energy(self):
        """Bot with high mind (50) has energy == 120."""
        alloc = StatAllocation(15, 15, 20, 50)
        bot = make_bot(stat_allocation=alloc)
        expected_energy = calculate_derived(alloc).max_energy
        assert expected_energy == 120
        assert bot.energy == 120

    def test_bot_has_derived(self):
        """Bot().derived is a DerivedStats instance."""
        bot = make_bot()
        assert isinstance(bot.derived, DerivedStats)

    def test_bot_stats_accessible(self):
        """Bot().stats.power == 25 for default allocation."""
        bot = make_bot()
        assert bot.stats.power == 25
        assert bot.stats.speed == 25
        assert bot.stats.armor == 25
        assert bot.stats.mind == 25

    def test_make_bot_with_stats(self):
        """make_bot(stat_allocation=...) passes through to Bot."""
        alloc = StatAllocation(30, 30, 20, 20)
        bot = make_bot(stat_allocation=alloc)
        assert bot.stats == alloc
        assert bot.derived == calculate_derived(alloc)
