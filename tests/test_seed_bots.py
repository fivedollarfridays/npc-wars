"""Tests for seed bot energy thresholds after ATTACK_COST=10 rebalance."""

import pathlib

import pytest

from engine.bot_scanner import load_bot_module

# ---------- helpers ----------

_BOTS_DIR = pathlib.Path(__file__).resolve().parent.parent / "bots"

VALID_ACTIONS = {"move", "attack", "rest", "defend"}
VALID_DIRECTIONS = {"north", "south", "east", "west"}


def _make_state(
    *,
    energy: int = 100,
    hp: int = 100,
    enemies: list | None = None,
    bumps_last_round: list | None = None,
) -> dict:
    """Build a standard state dict for bot decide() calls."""
    state: dict = {
        "me": {
            "x": 5,
            "y": 5,
            "hp": hp,
            "energy": energy,
            "attack_power": 25,
            "defense": 0,
        },
        "enemies": enemies if enemies is not None else [],
        "round": 1,
        "grid_size": 15,
        "storm_border": 0,
    }
    if bumps_last_round is not None:
        state["bumps_last_round"] = bumps_last_round
    return state


def _adjacent_enemy(dx: int = 1, dy: int = 0) -> list[dict]:
    """Return an enemies list with one adjacent enemy."""
    return [{"name": "Foe", "emoji": "X", "x": 5 + dx, "y": 5 + dy, "hp": 80}]


def _assert_valid_action(action: tuple) -> None:
    """Assert action is a valid (action,) or (action, direction) tuple."""
    assert isinstance(action, tuple)
    assert len(action) in (1, 2)
    assert action[0] in VALID_ACTIONS
    if len(action) == 2:
        assert action[1] in VALID_DIRECTIONS


# ---------- Cycle 1: energy-10 attack thresholds ----------


class TestKiterEnergyThreshold:
    """KiteBot should attack at energy=10 (new ATTACK_COST)."""

    def test_kiter_attacks_at_energy_10(self):
        from bots.example_kiter import decide

        state = _make_state(energy=10, enemies=_adjacent_enemy(dx=1, dy=0))
        action = decide(state)
        assert action[0] == "attack", f"Expected attack at energy=10, got {action}"

    def test_kiter_flees_at_energy_9(self):
        from bots.example_kiter import decide

        state = _make_state(energy=9, enemies=_adjacent_enemy(dx=1, dy=0))
        action = decide(state)
        # energy < 10 triggers rest at line 34
        assert action[0] == "rest", f"Expected rest at energy=9, got {action}"


class TestTankEnergyThreshold:
    """TankBot should counterattack at energy=10 (new ATTACK_COST)."""

    def test_tank_attacks_at_energy_10(self):
        from bots.example_tank import decide

        state = _make_state(energy=10, enemies=_adjacent_enemy(dx=1, dy=0))
        action = decide(state)
        assert action[0] == "attack", f"Expected attack at energy=10, got {action}"

    def test_tank_defends_at_energy_9(self):
        from bots.example_tank import decide

        state = _make_state(energy=9, enemies=_adjacent_enemy(dx=1, dy=0))
        action = decide(state)
        # energy < 10 means no attack; adjacent (dist=1) <= 3, energy >= 10 needed
        # for defend too, but energy=9 so falls through to rest
        assert action[0] in ("defend", "rest"), f"Expected defend/rest at energy=9, got {action}"


# ---------- Cycle 2: all bots return valid actions ----------


def _seed_bot_paths() -> list[pathlib.Path]:
    """Return all seed bot .py files (exclude template and __init__)."""
    return sorted(
        p
        for p in _BOTS_DIR.glob("*.py")
        if not p.name.startswith("_") and p.name != "template.py"
    )


class TestAllSeedBotsValid:
    """Every seed bot should return a valid action tuple."""

    @pytest.mark.parametrize(
        "bot_path",
        _seed_bot_paths(),
        ids=lambda p: p.stem,
    )
    def test_returns_valid_action(self, bot_path: pathlib.Path):
        module = load_bot_module(str(bot_path))
        state = _make_state(energy=50, enemies=_adjacent_enemy())
        action = module.decide(state)
        _assert_valid_action(action)


# ---------- Cycle 3: bumps_last_round key tolerance ----------


class TestBumpsKeyTolerance:
    """Bots must not crash when state dict includes bumps_last_round."""

    @pytest.mark.parametrize(
        "bot_path",
        _seed_bot_paths(),
        ids=lambda p: p.stem,
    )
    def test_handles_bumps_key(self, bot_path: pathlib.Path):
        module = load_bot_module(str(bot_path))
        state = _make_state(
            energy=50,
            enemies=_adjacent_enemy(),
            bumps_last_round=[{"type": "bump", "bots": ["A", "B"]}],
        )
        action = module.decide(state)
        _assert_valid_action(action)
