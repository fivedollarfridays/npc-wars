"""Tests for bots/example_mage.py -- ability-using example bot."""

from __future__ import annotations

import pathlib

from engine.bot_scanner import load_bot_module, scan_bot_file

_BOT_PATH = pathlib.Path(__file__).resolve().parent.parent / "bots" / "example_mage.py"

VALID_ACTIONS = {"move", "attack", "rest", "defend", "use_ability"}
VALID_DIRECTIONS = {"north", "south", "east", "west"}


def _make_state(
    *,
    energy: int = 100,
    hp: int = 100,
    enemies: list | None = None,
    round_num: int = 5,
    ability: dict | None = None,
) -> dict:
    """Build a standard state dict for the mage bot."""
    ability_info = ability
    if ability_info is None:
        ability_info = {
            "name": "Arcane Bolt",
            "type": "damage",
            "potency": 25,
            "range": 2,
            "cooldown": 4,
            "cooldown_remaining": 0,
            "energy_cost": 20,
            "uses": 0,
            "ready": True,
        }
    return {
        "me": {
            "x": 5,
            "y": 5,
            "hp": hp,
            "energy": energy,
            "attack_power": 25,
            "defense": 0,
            "power": 15,
            "speed": 20,
            "armor": 20,
            "mind": 45,
            "max_hp": 110,
            "max_energy": 100,
            "trap_cooldown": 0,
            "traps": [],
            "unlocked_actions": sorted(VALID_ACTIONS),
            "score": 0,
            "momentum_tier": 0,
            "is_leader": False,
            "passive_rounds": 0,
            "ability": ability_info,
        },
        "enemies": enemies if enemies is not None else [],
        "round": round_num,
        "grid_size": 15,
        "storm_border": 0,
    }


def _adjacent_enemy(dx: int = 1, dy: int = 0, hp: int = 80) -> list[dict]:
    return [{"name": "Foe", "emoji": "X", "x": 5 + dx, "y": 5 + dy, "hp": hp}]


def _distant_enemy(dx: int = 4, dy: int = 0, hp: int = 80) -> list[dict]:
    return [{"name": "Foe", "emoji": "X", "x": 5 + dx, "y": 5 + dy, "hp": hp}]


def _nearby_enemy(dx: int = 2, dy: int = 0, hp: int = 80) -> list[dict]:
    """Enemy within ability range (2 tiles)."""
    return [{"name": "Foe", "emoji": "X", "x": 5 + dx, "y": 5 + dy, "hp": hp}]


def _assert_valid_action(action: tuple) -> None:
    assert isinstance(action, tuple)
    assert len(action) in (1, 2)
    assert action[0] in VALID_ACTIONS
    if len(action) == 2:
        assert action[1] in VALID_DIRECTIONS


# ---------- Cycle 1: security scan + required attributes ----------


class TestMageSecurity:
    def test_passes_security_scan(self):
        violations = scan_bot_file(str(_BOT_PATH))
        assert violations == [], f"Security violations: {violations}"

    def test_loads_without_error(self):
        module = load_bot_module(str(_BOT_PATH))
        assert module is not None

    def test_has_required_attributes(self):
        module = load_bot_module(str(_BOT_PATH))
        for attr in ("BOT_NAME", "BOT_EMOJI", "BOT_BIO", "BOT_AUTHOR",
                      "BOT_POWER", "BOT_SPEED", "BOT_ARMOR", "BOT_MIND"):
            assert hasattr(module, attr), f"Missing {attr}"

    def test_has_decide_function(self):
        module = load_bot_module(str(_BOT_PATH))
        assert callable(getattr(module, "decide", None))

    def test_stats_sum_to_100(self):
        module = load_bot_module(str(_BOT_PATH))
        total = module.BOT_POWER + module.BOT_SPEED + module.BOT_ARMOR + module.BOT_MIND
        assert total == 100, f"Stats sum to {total}, expected 100"

    def test_has_equipment(self):
        module = load_bot_module(str(_BOT_PATH))
        equip = getattr(module, "BOT_EQUIPMENT", None)
        assert equip is not None, "Missing BOT_EQUIPMENT"

    def test_equipment_valid(self):
        from engine.equipment import validate_equipment
        module = load_bot_module(str(_BOT_PATH))
        ok, msg = validate_equipment(module.BOT_EQUIPMENT)
        assert ok, f"Invalid equipment: {msg}"


# ---------- Cycle 2: decide returns valid actions ----------


class TestMageDecide:
    def test_returns_valid_action_with_enemies(self):
        from bots.example_mage import decide
        state = _make_state(enemies=_adjacent_enemy())
        action = decide(state)
        _assert_valid_action(action)

    def test_returns_valid_action_no_enemies(self):
        from bots.example_mage import decide
        state = _make_state(enemies=[])
        action = decide(state)
        _assert_valid_action(action)

    def test_returns_valid_action_low_energy(self):
        from bots.example_mage import decide
        state = _make_state(energy=5, enemies=_distant_enemy())
        action = decide(state)
        _assert_valid_action(action)

    def test_rests_when_no_enemies(self):
        from bots.example_mage import decide
        state = _make_state(enemies=[])
        action = decide(state)
        assert action == ("rest",)


# ---------- Cycle 3: ability-specific behavior ----------


class TestMageAbility:
    def test_has_power_up_function(self):
        module = load_bot_module(str(_BOT_PATH))
        assert callable(getattr(module, "power_up", None))

    def test_power_up_returns_valid_ability(self):
        from bots.example_mage import power_up
        from engine.abilities import validate_ability
        state = _make_state()
        result = power_up(state)
        ability = validate_ability(result)
        assert ability is not None, f"power_up returned invalid ability: {result}"
        assert ability.type == "damage"

    def test_has_evolve_function(self):
        module = load_bot_module(str(_BOT_PATH))
        assert callable(getattr(module, "evolve", None))

    def test_evolve_returns_dict(self):
        from bots.example_mage import evolve
        state = _make_state()
        result = evolve(state)
        assert isinstance(result, dict)

    def test_uses_ability_when_ready_and_enemy_in_range(self):
        from bots.example_mage import decide
        state = _make_state(
            energy=100,
            enemies=_nearby_enemy(dx=2, dy=0),
        )
        action = decide(state)
        assert action[0] == "use_ability", f"Expected use_ability, got {action}"

    def test_attacks_adjacent_enemy(self):
        from bots.example_mage import decide
        # Ability not ready (on cooldown)
        state = _make_state(
            energy=100,
            enemies=_adjacent_enemy(dx=1, dy=0),
            ability={
                "name": "Arcane Bolt", "type": "damage", "potency": 25,
                "range": 2, "cooldown": 4, "cooldown_remaining": 3,
                "energy_cost": 20, "uses": 1, "ready": False,
            },
        )
        action = decide(state)
        assert action[0] == "attack", f"Expected attack, got {action}"
