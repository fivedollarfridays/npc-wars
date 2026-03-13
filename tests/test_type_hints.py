"""Tests verifying mypy --strict passes on all engine modules."""

import subprocess


def test_mypy_strict_engine_zero_errors() -> None:
    """mypy engine/ --strict must report 0 errors."""
    result = subprocess.run(
        ["mypy", "engine/", "--strict"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"mypy --strict found errors:\n{result.stdout}\n{result.stderr}"
    )


def test_engine_types_module_imports() -> None:
    """engine/types.py must be importable and export expected names."""
    from engine.types import (  # noqa: F401
        EnemyInfo,
        SelfInfo,
        GameState,
        BotConfig,
        Event,
        MatchData,
    )


def test_combat_bot_decide_func_typed() -> None:
    """Bot.__init__ must accept a Callable for decide_func (not Any-untyped)."""
    from engine.combat import Bot

    import inspect
    sig = inspect.signature(Bot.__init__)
    param = sig.parameters["decide_func"]
    # The annotation should exist (not inspect.Parameter.empty)
    assert param.annotation is not inspect.Parameter.empty, (
        "decide_func parameter must have a type annotation"
    )
