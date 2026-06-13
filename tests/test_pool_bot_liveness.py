"""Liveness test for every shipped bot (T73.2).

Loads each bot via :func:`engine.loader.load_bots` from both shipped pools
(``bots/`` and ``agentgrounds/wars/builtin_bots/``), runs it for 20 rounds
against a stationary dummy with a fixed seed, and asserts it never accrues
``consecutive_failures`` and never dies by ``disconnected``. It also asserts
every bot passes :func:`scripts.validate_bot.validate_bot`, so shipping a
broken example becomes impossible.

Discovery is dynamic: any new bot file dropped into either directory is picked
up automatically, with no edit to this module.

Trapper, Viper, and Mage disconnect today because they emit locked
``trap``/``use_ability`` actions, which the engine rejects until the bot has
unlocked them — three rejections in a row trip ``MAX_CONSECUTIVE_FAILURES`` and
the bot is disconnected. They are marked ``xfail(strict=True)`` until **T73.5**
makes locked actions degrade gracefully; once it lands those cases will XPASS
and the strict marker forces this module to drop the xfails.
"""

from __future__ import annotations

import random

import pytest

from engine.callback_runner import run_power_up_callbacks, run_setup_callbacks
from engine.equipment import EQUIPMENT_DEFAULTS
from engine.game import _execute_round
from engine.loader import load_bots
from engine.match_modes import get_mode
from engine.match_setup import prepare_match
from engine.terrain import build_map
from engine.traps import TrapManager
from scripts.validate_bot import validate_bot

_BOT_DIRS = ("bots", "agentgrounds/wars/builtin_bots")
_SEED = 42
_ROUNDS = 20

# Bots that disconnect today because they emit locked trap/use_ability actions.
# These xfails are flipped by T73.5 (locked actions degrade gracefully).
_KNOWN_DISCONNECTS = frozenset({"Trapper", "Viper", "Mage"})


def _dummy_config(taken_emoji: str) -> dict:
    """A stationary, immortal opponent that always rests in place."""
    emoji = "⬛" if taken_emoji != "⬛" else "⬜"
    return {
        "name": "Dummy", "emoji": emoji, "bio": "", "author": "test",
        "decide_func": lambda state: ("rest",), "stat_allocation": None,
        "glyph": emoji, "equipment": dict(EQUIPMENT_DEFAULTS), "module": None,
    }


def _load_shipped() -> list[tuple[str, dict]]:
    """Every shipped bot from both pools, loaded via load_bots."""
    shipped: list[tuple[str, dict]] = []
    for directory in _BOT_DIRS:
        label = directory.split("/")[-1]
        for cfg in load_bots(directory):
            shipped.append((label, cfg))
    return shipped


_SHIPPED = _load_shipped()


def _liveness_params() -> list:
    params = []
    for label, cfg in _SHIPPED:
        marks = []
        if cfg["name"] in _KNOWN_DISCONNECTS:
            marks.append(pytest.mark.xfail(
                strict=True,
                reason="locked trap/use_ability disconnect; flipped by T73.5",
            ))
        params.append(pytest.param(cfg, id=f"{label}:{cfg['name']}", marks=marks))
    return params


def _validator_params() -> list:
    return [
        pytest.param(cfg["module"].__file__, id=f"{label}:{cfg['name']}")
        for label, cfg in _SHIPPED
    ]


def _run_liveness(cfg: dict) -> tuple[int, bool]:
    """Run cfg vs a pinned stationary dummy for _ROUNDS rounds.

    Returns (max consecutive_failures observed, whether it disconnected/died).
    The dummy is pinned two tiles away and kept immortal each round so the bot
    always has a visible opponent and the only way it can die is by its own
    repeated invalid actions.
    """
    random.seed(_SEED)  # bots use the global RNG; seed it for determinism
    mode = get_mode("standard")
    bots, _players, grid_size, rng = prepare_match(
        [cfg, _dummy_config(cfg["emoji"])], _SEED, mode=mode,
    )
    terrain = build_map("arena", grid_size)
    trap_manager = TrapManager()
    for bot in bots:
        bot._terrain = terrain
        bot._trap_manager = trap_manager
    test_bot, dummy = bots
    pin = (min(test_bot.x + 2, grid_size - 1), test_bot.y)
    run_setup_callbacks(bots, grid_size=grid_size, storm_border=0)
    run_power_up_callbacks(bots, grid_size=grid_size, storm_border=0)

    max_cf = 0
    for round_num in range(1, _ROUNDS + 1):
        dummy.x, dummy.y = pin
        dummy.hp, dummy.alive = 1e9, True
        for bot in bots:
            bot._current_round = round_num
        round_data, _elims, _bumps = _execute_round(
            bots, round_num, grid_size, 0, rng=rng,
            trap_manager=trap_manager, terrain=terrain,
        )
        max_cf = max(max_cf, test_bot.consecutive_failures)
        disconnected = round_data.get("actions", {}).get(test_bot.emoji) == ("disconnected",)
        if disconnected or not test_bot.alive:
            return max_cf, True
    return max_cf, False


@pytest.mark.parametrize("cfg", _liveness_params())
def test_bot_survives_dummy_match(cfg: dict) -> None:
    max_cf, disconnected = _run_liveness(cfg)
    assert max_cf == 0, f"{cfg['name']} accrued {max_cf} consecutive_failures"
    assert not disconnected, f"{cfg['name']} died by disconnected"


@pytest.mark.parametrize("path", _validator_params())
def test_bot_passes_validator(path: str) -> None:
    ok, errors = validate_bot(path)
    assert ok, f"validate_bot rejected {path}: {errors}"
