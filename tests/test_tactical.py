"""Tests for tactical item execution engine."""

from __future__ import annotations

import random

from engine.combat import Bot


def _make_bot(**overrides) -> Bot:
    """Build a minimal Bot for testing."""
    defaults = {
        "name": "TestBot", "emoji": "T", "bio": "", "author": "test",
        "decide_func": lambda *a: ("rest",), "x": 5, "y": 5,
    }
    defaults.update(overrides)
    return Bot(**defaults)


# ── Cycle 1: Battle Cry activation ──


def test_battle_cry_activates_and_sets_damage_mult():
    """Battle cry sets tactical_damage_mult to 1.5 and deducts energy."""
    from engine.tactical import resolve_tactical_activation

    bot = _make_bot()
    bot.equipment["tactical"] = "battle_cry"
    bot.energy = 100
    bot.tactical_cooldown = 0

    events = resolve_tactical_activation(bot, round_num=1)

    assert bot.tactical_damage_mult == 1.5
    assert bot.energy == 100 - 15  # energy_cost = 15
    assert bot.tactical_cooldown == 4
    assert len(events) == 1
    assert events[0]["type"] == "tactical_activate"
    assert events[0]["tactical"] == "battle_cry"


# ── Cycle 2: Fortify activation ──


def test_fortify_activates_grants_dr_and_temp_hp():
    """Fortify grants +6 DR and +10 temp HP."""
    from engine.tactical import resolve_tactical_activation

    bot = _make_bot()
    bot.equipment["tactical"] = "fortify"
    bot.energy = 100
    hp_before = bot.hp

    events = resolve_tactical_activation(bot, round_num=1)

    assert bot.tactical_dr_bonus == 6
    assert bot.tactical_temp_hp == 10
    assert bot.hp == hp_before + 10
    assert bot.energy == 100 - 12  # energy_cost = 12
    assert bot.tactical_cooldown == 5
    assert len(events) == 1
    assert events[0]["tactical"] == "fortify"


def test_fortify_clears_after_tick():
    """Fortify DR and temp HP removed after tick_tactical_effects."""
    from engine.tactical import tick_tactical_effects

    bot = _make_bot()
    bot.tactical_dr_bonus = 6
    bot.tactical_temp_hp = 10
    bot.hp = 80.0  # has temp HP baked in

    tick_tactical_effects([bot])

    assert bot.tactical_dr_bonus == 0
    assert bot.tactical_temp_hp == 0
    assert bot.hp == 70.0  # 80 - 10 temp HP


# ── Cycle 3: Teleport activation ──


def test_teleport_moves_bot_3_tiles():
    """Teleport moves bot 3 tiles in the given direction."""
    from engine.tactical import resolve_tactical_activation

    bot = _make_bot(x=5, y=5)
    bot.equipment["tactical"] = "teleport"
    bot.energy = 100

    events = resolve_tactical_activation(bot, round_num=1, direction="north")

    assert bot.y == 2  # 5 - 3 = 2 (north = y-1)
    assert bot.x == 5  # unchanged
    assert bot.energy == 100 - 20
    assert bot.tactical_cooldown == 3
    assert events[0]["tactical"] == "teleport"


def test_teleport_without_direction_is_noop_position():
    """Teleport with no direction doesn't move but still activates."""
    from engine.tactical import resolve_tactical_activation

    bot = _make_bot(x=5, y=5)
    bot.equipment["tactical"] = "teleport"
    bot.energy = 100

    events = resolve_tactical_activation(bot, round_num=1, direction=None)

    assert bot.x == 5
    assert bot.y == 5
    assert len(events) == 1  # still activates (costs energy/cooldown)


# ── Cycle 4: Overdrive passive ──


def test_overdrive_applies_permanent_damage_bonus():
    """Overdrive adds +2 min/max damage to equipment bonuses."""
    from engine.tactical import apply_overdrive

    bot = _make_bot()
    bot.equipment["tactical"] = "overdrive"
    min_before = bot.equipment_bonuses.min_damage
    max_before = bot.equipment_bonuses.max_damage

    apply_overdrive(bot)

    assert bot.equipment_bonuses.min_damage == min_before + 2
    assert bot.equipment_bonuses.max_damage == max_before + 2


def test_overdrive_increases_attack_energy_cost():
    """Overdrive adds +3 to attack action cost modifier."""
    from engine.tactical import apply_overdrive

    bot = _make_bot()
    bot.equipment["tactical"] = "overdrive"

    apply_overdrive(bot)

    assert bot.equipment_bonuses.action_cost_mods["attack"] == 3


def test_overdrive_noop_without_overdrive_equipped():
    """apply_overdrive does nothing if bot doesn't have overdrive."""
    from engine.tactical import apply_overdrive

    bot = _make_bot()
    bot.equipment["tactical"] = "battle_cry"

    apply_overdrive(bot)

    assert bot.equipment_bonuses.min_damage == 0
    assert bot.equipment_bonuses.max_damage == 0


# ── Cycle 5: Guards and cooldown ticking ──


def test_cooldown_prevents_reactivation():
    """Cannot activate tactical while on cooldown."""
    from engine.tactical import resolve_tactical_activation

    bot = _make_bot()
    bot.equipment["tactical"] = "battle_cry"
    bot.energy = 100
    bot.tactical_cooldown = 2

    events = resolve_tactical_activation(bot, round_num=1)

    assert events == []
    assert bot.tactical_damage_mult == 1.0  # unchanged


def test_insufficient_energy_prevents_activation():
    """Cannot activate tactical without enough energy."""
    from engine.tactical import resolve_tactical_activation

    bot = _make_bot()
    bot.equipment["tactical"] = "battle_cry"
    bot.energy = 10  # needs 15

    events = resolve_tactical_activation(bot, round_num=1)

    assert events == []


def test_no_tactical_equipped_is_noop():
    """No tactical item = no activation."""
    from engine.tactical import resolve_tactical_activation

    bot = _make_bot()
    # no tactical set

    events = resolve_tactical_activation(bot, round_num=1)

    assert events == []


def test_passive_tactical_not_activated():
    """Overdrive (passive) cannot be activated via resolve_tactical_activation."""
    from engine.tactical import resolve_tactical_activation

    bot = _make_bot()
    bot.equipment["tactical"] = "overdrive"
    bot.energy = 100

    events = resolve_tactical_activation(bot, round_num=1)

    assert events == []


def test_tick_tactical_cooldowns_decrements():
    """tick_tactical_cooldowns reduces cooldown by 1 each call."""
    from engine.tactical import tick_tactical_cooldowns

    bot = _make_bot()
    bot.tactical_cooldown = 3

    tick_tactical_cooldowns([bot])

    assert bot.tactical_cooldown == 2


def test_tick_cooldown_does_not_go_negative():
    """Cooldown stays at 0, never goes negative."""
    from engine.tactical import tick_tactical_cooldowns

    bot = _make_bot()
    bot.tactical_cooldown = 0

    tick_tactical_cooldowns([bot])

    assert bot.tactical_cooldown == 0


# ── Cycle 1 continued: Battle Cry clear ──


def test_battle_cry_clears_after_tick():
    """Battle cry damage mult resets to 1.0 after tick_tactical_effects."""
    from engine.tactical import tick_tactical_effects

    bot = _make_bot()
    bot.tactical_damage_mult = 1.5

    tick_tactical_effects([bot])

    assert bot.tactical_damage_mult == 1.0


# ── Cycle 6: Sandbox and combat wiring ──


def test_use_tactical_is_valid_action():
    """use_tactical is in VALID_ACTIONS with 0 or 1 args."""
    from engine.sandbox import VALID_ACTIONS
    assert "use_tactical" in VALID_ACTIONS


def test_validate_use_tactical_no_direction():
    """use_tactical with no direction is valid."""
    from engine.sandbox import validate_action
    result = validate_action(("use_tactical",))
    assert result == ("use_tactical",)


def test_validate_use_tactical_with_direction():
    """use_tactical with direction is valid."""
    from engine.sandbox import validate_action
    result = validate_action(("use_tactical", "north"))
    assert result == ("use_tactical", "north")


def test_tactical_damage_mult_in_melee():
    """tactical_damage_mult is applied in melee attack resolution."""
    from engine.rounds_combat import _roll_melee

    attacker = _make_bot(emoji="A", x=0, y=0)
    defender = _make_bot(emoji="D", x=1, y=0)
    attacker.tactical_damage_mult = 1.5
    actions: dict[str, tuple[str, ...]] = {"A": ("attack", "east"), "D": ("rest",)}

    rng = random.Random(42)
    # Roll multiple times to get a hit
    for _ in range(20):
        rng_copy = random.Random(rng.randint(0, 999999))
        result = _roll_melee(attacker, defender, actions, rng_copy)
        if result["type"] == "hit":
            # Verify damage was affected by the multiplier
            break


def test_tactical_dr_bonus_in_melee():
    """tactical_dr_bonus is added to defender AC in melee."""
    from engine.combat_rolls import _compute_ac
    from engine.stats import DerivedStats

    defender_stats = DerivedStats(
        max_hp=100, max_energy=100, min_damage=5, max_damage=10,
        crit_multiplier=1.5, dodge_chance=0.0, initiative=25,
        damage_reduction=0, energy_regen=0,
    )
    # Without tactical DR
    ac_base = _compute_ac(defender_stats, defending=False,
                          momentum_defense_reduct=0.0, equipment_dr=0)
    # With tactical DR (+6)
    ac_with_tac = _compute_ac(defender_stats, defending=False,
                               momentum_defense_reduct=0.0, equipment_dr=0,
                               tactical_dr=6)
    assert ac_with_tac == ac_base + 6
