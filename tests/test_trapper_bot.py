"""Tests for bots/example_trapper.py — trap-using example bot."""

from __future__ import annotations

import pathlib

from engine.bot_scanner import load_bot_module, scan_bot_file

_BOT_PATH = pathlib.Path(__file__).resolve().parent.parent / "bots" / "example_trapper.py"

VALID_ACTIONS = {"move", "attack", "rest", "defend", "trap"}
VALID_DIRECTIONS = {"north", "south", "east", "west"}


def _make_state(
    *,
    energy: int = 100,
    hp: int = 100,
    trap_cooldown: int = 0,
    traps: list | None = None,
    enemies: list | None = None,
    round_num: int = 5,
) -> dict:
    """Build a standard state dict with trap fields."""
    return {
        "me": {
            "x": 5,
            "y": 5,
            "hp": hp,
            "energy": energy,
            "attack_power": 25,
            "defense": 0,
            "power": 35,
            "speed": 20,
            "armor": 25,
            "mind": 20,
            "max_hp": 110,
            "max_energy": 100,
            "trap_cooldown": trap_cooldown,
            "traps": traps if traps is not None else [],
            "unlocked_actions": ["move", "attack", "rest", "defend", "trap"],
            "score": 0,
            "momentum_tier": 0,
            "is_leader": False,
            "passive_rounds": 0,
        },
        "enemies": enemies if enemies is not None else [],
        "round": round_num,
        "grid_size": 15,
        "storm_border": 0,
    }


def _adjacent_enemy(dx: int = 1, dy: int = 0, hp: int = 80) -> list[dict]:
    """Return an enemies list with one adjacent enemy."""
    return [{"name": "Foe", "emoji": "X", "x": 5 + dx, "y": 5 + dy, "hp": hp}]


def _distant_enemy(dx: int = 4, dy: int = 0, hp: int = 80) -> list[dict]:
    """Return an enemies list with one distant enemy."""
    return [{"name": "Foe", "emoji": "X", "x": 5 + dx, "y": 5 + dy, "hp": hp}]


def _assert_valid_action(action: tuple) -> None:
    """Assert action is a valid tuple."""
    assert isinstance(action, tuple)
    assert len(action) in (1, 2)
    assert action[0] in VALID_ACTIONS
    if len(action) == 2:
        assert action[1] in VALID_DIRECTIONS


# ---------- Cycle 1: security scan + required attributes ----------


class TestTrapperSecurity:
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


# ---------- Cycle 2: decide returns valid actions ----------


class TestTrapperDecide:
    def test_returns_valid_action_with_enemies(self):
        from bots.example_trapper import decide
        state = _make_state(enemies=_adjacent_enemy())
        action = decide(state)
        _assert_valid_action(action)

    def test_returns_valid_action_no_enemies(self):
        from bots.example_trapper import decide
        state = _make_state(enemies=[])
        action = decide(state)
        _assert_valid_action(action)

    def test_returns_valid_action_low_energy(self):
        from bots.example_trapper import decide
        state = _make_state(energy=5, enemies=_distant_enemy())
        action = decide(state)
        _assert_valid_action(action)


# ---------- Cycle 3: trap placement logic ----------


class TestTrapperTraps:
    def test_places_trap_when_ready_and_enemy_nearby(self):
        from bots.example_trapper import decide
        # Enemy 2-3 tiles away, trap cooldown ready, enough energy
        state = _make_state(
            energy=50,
            trap_cooldown=0,
            enemies=_distant_enemy(dx=3, dy=0),
        )
        action = decide(state)
        assert action[0] == "trap", f"Expected trap, got {action}"

    def test_no_trap_when_on_cooldown(self):
        from bots.example_trapper import decide
        state = _make_state(
            energy=50,
            trap_cooldown=2,
            enemies=_distant_enemy(dx=3, dy=0),
        )
        action = decide(state)
        assert action[0] != "trap", f"Should not trap on cooldown, got {action}"

    def test_no_trap_when_low_energy(self):
        from bots.example_trapper import decide
        state = _make_state(
            energy=10,
            trap_cooldown=0,
            enemies=_distant_enemy(dx=3, dy=0),
        )
        action = decide(state)
        assert action[0] != "trap", f"Should not trap with low energy, got {action}"

    def test_attacks_adjacent_enemy(self):
        from bots.example_trapper import decide
        state = _make_state(
            energy=50,
            trap_cooldown=0,
            enemies=_adjacent_enemy(dx=1, dy=0),
        )
        action = decide(state)
        assert action[0] == "attack", f"Expected attack on adjacent enemy, got {action}"


# ---------- Cycle 4: setup and react callbacks ----------


class TestTrapperCallbacks:
    def test_has_setup_function(self):
        module = load_bot_module(str(_BOT_PATH))
        assert callable(getattr(module, "setup", None))

    def test_has_react_function(self):
        module = load_bot_module(str(_BOT_PATH))
        assert callable(getattr(module, "react", None))

    def test_setup_does_not_crash(self):
        from bots.example_trapper import setup
        state = _make_state()
        setup(state)  # should not raise

    def test_react_does_not_crash(self):
        from bots.example_trapper import react
        state = _make_state(enemies=_adjacent_enemy())
        events = [
            {"type": "attack", "attacker": "X", "target": "T", "damage": 15},
        ]
        react(state, events)  # should not raise
