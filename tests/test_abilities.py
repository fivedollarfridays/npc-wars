"""Tests for ability system: power_up callback + use_ability action."""

from __future__ import annotations

from engine.abilities import (
    ABILITY_TYPES, AbilityDef, resolve_ability, tick_ability_effects,
    validate_ability,
)
from engine.combat import Bot


# ---------------------------------------------------------------------------
# Cycle 1: validate_ability
# ---------------------------------------------------------------------------


def _valid_def() -> dict:
    return {
        "name": "Fireball",
        "type": "damage",
        "potency": 30,
        "range": 2,
        "cooldown": 5,
        "energy_cost": 25,
    }


def test_validate_ability_accepts_valid_definition():
    result = validate_ability(_valid_def())
    assert result is not None
    assert isinstance(result, AbilityDef)
    assert result.name == "Fireball"
    assert result.type == "damage"
    assert result.potency == 30
    assert result.range == 2
    assert result.cooldown == 5
    assert result.energy_cost == 25


def test_validate_ability_rejects_invalid_type():
    d = _valid_def()
    d["type"] = "teleport"
    assert validate_ability(d) is None


def test_validate_ability_rejects_potency_out_of_range():
    for bad in (0, -1, 51, 100):
        d = _valid_def()
        d["potency"] = bad
        assert validate_ability(d) is None, f"potency={bad} should be rejected"


def test_validate_ability_rejects_range_out_of_range():
    for bad in (-1, 4, 10):
        d = _valid_def()
        d["range"] = bad
        assert validate_ability(d) is None, f"range={bad} should be rejected"


def test_validate_ability_rejects_cooldown_out_of_range():
    for bad in (0, 1, 11, 20):
        d = _valid_def()
        d["cooldown"] = bad
        assert validate_ability(d) is None, f"cooldown={bad} should be rejected"


def test_validate_ability_rejects_energy_cost_out_of_range():
    for bad in (0, 9, 41, 100):
        d = _valid_def()
        d["energy_cost"] = bad
        assert validate_ability(d) is None, f"energy_cost={bad} should be rejected"


def test_validate_ability_rejects_bad_name():
    for bad in ("", "x" * 31, 123, None):
        d = _valid_def()
        d["name"] = bad
        assert validate_ability(d) is None, f"name={bad!r} should be rejected"


def test_validate_ability_rejects_non_dict():
    assert validate_ability(None) is None
    assert validate_ability("fireball") is None
    assert validate_ability(42) is None


def test_validate_ability_rejects_missing_keys():
    for key in ("name", "type", "potency", "range", "cooldown", "energy_cost"):
        d = _valid_def()
        del d[key]
        assert validate_ability(d) is None, f"missing '{key}' should be rejected"


def test_ability_types_contains_four():
    assert ABILITY_TYPES == frozenset({"damage", "heal", "shield", "slow"})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_bot(name: str = "A", emoji: str = "A", x: int = 0, y: int = 0,
              hp: float = 100.0, energy: int = 100) -> Bot:
    bot = Bot(name=name, emoji=emoji, bio="", author="test",
              decide_func=lambda s: ("rest",), x=x, y=y)
    bot.hp = hp
    bot.energy = energy
    return bot


def _damage_ability(potency: int = 30, arange: int = 2,
                    cooldown: int = 5, cost: int = 25) -> AbilityDef:
    return AbilityDef(name="Fireball", type="damage", potency=potency,
                      range=arange, cooldown=cooldown, energy_cost=cost)


def _heal_ability(potency: int = 20) -> AbilityDef:
    return AbilityDef(name="Heal", type="heal", potency=potency,
                      range=0, cooldown=3, energy_cost=15)


def _shield_ability(potency: int = 10) -> AbilityDef:
    return AbilityDef(name="Barrier", type="shield", potency=potency,
                      range=0, cooldown=4, energy_cost=20)


def _slow_ability(potency: int = 15) -> AbilityDef:
    return AbilityDef(name="Frost", type="slow", potency=potency,
                      range=2, cooldown=3, energy_cost=15)


# ---------------------------------------------------------------------------
# Cycle 2: resolve_ability
# ---------------------------------------------------------------------------


def test_damage_ability_deals_potency_to_target():
    bot = _make_bot(emoji="A", x=0, y=0)
    target = _make_bot(emoji="B", x=1, y=0, hp=80.0)
    ability = _damage_ability(potency=30)
    events = resolve_ability(bot, target, ability, round_num=1, all_bots=[bot, target])
    assert len(events) >= 1
    assert events[0]["type"] == "ability_damage"
    assert target.hp < 80.0  # took damage


def test_heal_ability_restores_hp_capped():
    bot = _make_bot(emoji="A", hp=90.0)
    ability = _heal_ability(potency=20)
    events = resolve_ability(bot, None, ability, round_num=1, all_bots=[bot])
    assert len(events) >= 1
    assert events[0]["type"] == "ability_heal"
    # max_hp is derived from stats; default should be 100
    assert bot.hp <= bot.derived.max_hp


def test_shield_ability_grants_temp_dr():
    bot = _make_bot(emoji="A")
    ability = _shield_ability(potency=10)
    events = resolve_ability(bot, None, ability, round_num=1, all_bots=[bot])
    assert bot.ability_shield == 10
    assert bot.ability_shield_rounds == 2
    assert events[0]["type"] == "ability_shield"


def test_slow_ability_reduces_target_initiative():
    bot = _make_bot(emoji="A", x=0, y=0)
    target = _make_bot(emoji="B", x=1, y=0)
    ability = _slow_ability(potency=15)
    events = resolve_ability(bot, target, ability, round_num=1, all_bots=[bot, target])
    assert target.ability_slow == 15
    assert target.ability_slow_rounds == 3
    assert events[0]["type"] == "ability_slow"


def test_ability_deducts_energy():
    bot = _make_bot(emoji="A", energy=50)
    ability = _damage_ability(potency=10, cost=25)
    target = _make_bot(emoji="B", x=1, y=0)
    resolve_ability(bot, target, ability, round_num=1, all_bots=[bot, target])
    assert bot.energy == 25


def test_ability_cooldown_set_after_use():
    bot = _make_bot(emoji="A")
    ability = _damage_ability(potency=10, cooldown=5, cost=10)
    bot.ability = ability
    target = _make_bot(emoji="B", x=1, y=0)
    resolve_ability(bot, target, ability, round_num=1, all_bots=[bot, target])
    assert bot.ability_cooldown == 5


def test_ability_uses_incremented():
    bot = _make_bot(emoji="A")
    ability = _damage_ability(potency=10, cost=10)
    bot.ability = ability
    target = _make_bot(emoji="B", x=1, y=0)
    resolve_ability(bot, target, ability, round_num=1, all_bots=[bot, target])
    assert bot.ability_uses == 1


# ---------------------------------------------------------------------------
# Cycle 3: tick_ability_effects
# ---------------------------------------------------------------------------


def test_tick_clears_expired_shield():
    bot = _make_bot(emoji="A")
    bot.ability_shield = 10
    bot.ability_shield_rounds = 1
    tick_ability_effects([bot])
    assert bot.ability_shield_rounds == 0
    assert bot.ability_shield == 0


def test_tick_decrements_shield_rounds():
    bot = _make_bot(emoji="A")
    bot.ability_shield = 10
    bot.ability_shield_rounds = 2
    tick_ability_effects([bot])
    assert bot.ability_shield_rounds == 1
    assert bot.ability_shield == 10  # still active


def test_tick_clears_expired_slow():
    bot = _make_bot(emoji="A")
    bot.ability_slow = 15
    bot.ability_slow_rounds = 1
    tick_ability_effects([bot])
    assert bot.ability_slow_rounds == 0
    assert bot.ability_slow == 0


def test_tick_decrements_slow_rounds():
    bot = _make_bot(emoji="A")
    bot.ability_slow = 15
    bot.ability_slow_rounds = 3
    tick_ability_effects([bot])
    assert bot.ability_slow_rounds == 2
    assert bot.ability_slow == 15  # still active


# ---------------------------------------------------------------------------
# Cycle 4: power_up callback + state dict + sandbox
# ---------------------------------------------------------------------------


def test_power_up_callback_in_callback_names():
    from engine.callbacks import CALLBACK_NAMES
    assert "power_up" in CALLBACK_NAMES


def test_callback_set_has_power_up_field():
    from engine.callbacks import CallbackSet
    cs = CallbackSet()
    assert cs.power_up is None
    cs2 = CallbackSet(power_up=lambda s: None)
    assert cs2.power_up is not None


def test_run_power_up_callbacks_stores_ability():
    from engine.callback_runner import run_power_up_callbacks
    bot = _make_bot(emoji="M")
    bot.callbacks.power_up = lambda state: _valid_def()
    run_power_up_callbacks([bot], grid_size=10, storm_border=0)
    assert bot.ability is not None
    assert bot.ability.name == "Fireball"


def test_run_power_up_invalid_result_no_ability():
    from engine.callback_runner import run_power_up_callbacks
    bot = _make_bot(emoji="M")
    bot.callbacks.power_up = lambda state: {"name": "Bad"}  # invalid
    run_power_up_callbacks([bot], grid_size=10, storm_border=0)
    assert bot.ability is None


def test_bot_without_power_up_no_ability():
    from engine.callback_runner import run_power_up_callbacks
    bot = _make_bot(emoji="M")
    run_power_up_callbacks([bot], grid_size=10, storm_border=0)
    assert bot.ability is None


def test_use_ability_in_valid_actions():
    from engine.sandbox import VALID_ACTIONS
    assert "use_ability" in VALID_ACTIONS


def test_state_dict_has_ability_info():
    bot = _make_bot(emoji="M")
    ability = _damage_ability()
    bot.ability = ability
    bot.ability_cooldown = 2
    bot.ability_uses = 1
    d = bot.to_self_dict()
    assert "ability" in d
    ab = d["ability"]
    assert ab["name"] == "Fireball"
    assert ab["type"] == "damage"
    assert ab["cooldown_remaining"] == 2
    assert ab["uses"] == 1
    assert ab["ready"] is False  # on cooldown


def test_state_dict_ability_ready_when_no_cooldown():
    bot = _make_bot(emoji="M")
    bot.ability = _damage_ability(cost=10)
    bot.ability_cooldown = 0
    d = bot.to_self_dict()
    assert d["ability"]["ready"] is True


def test_state_dict_no_ability():
    bot = _make_bot(emoji="M")
    d = bot.to_self_dict()
    assert d["ability"] is None


def test_enemy_dict_has_ability_flag():
    bot = _make_bot(emoji="M")
    bot.ability = _damage_ability()
    d = bot.to_enemy_dict()
    assert d["has_ability"] is True


def test_enemy_dict_no_ability():
    bot = _make_bot(emoji="M")
    d = bot.to_enemy_dict()
    assert d["has_ability"] is False


def test_use_ability_with_no_ability_is_noop():
    """Bot without an ability using use_ability should produce no events."""
    bot = _make_bot(emoji="A")
    # No ability set, try to resolve — should return empty
    events = resolve_ability(bot, None, None, round_num=1, all_bots=[bot])  # type: ignore[arg-type]
    assert events == []
