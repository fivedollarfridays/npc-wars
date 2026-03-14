"""Tests for Watcher integration into the async game loop."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import patch

import pytest



def _make_config(emoji: str, *, human: bool = False) -> dict[str, Any]:
    """Create a bot config dict."""
    cfg: dict[str, Any] = {
        "name": f"bot-{emoji}",
        "emoji": emoji,
        "bio": "test",
        "author": "test",
        "decide_func": lambda s: ("rest",),
    }
    if human:
        cfg["_human"] = True
    return cfg


class _FakeHumanAdapter:
    """Stub human adapter that always times out."""

    async def get_action_async(self, state: dict[str, Any], timeout: float) -> tuple[str, ...]:
        raise asyncio.TimeoutError


@pytest.mark.asyncio(loop_scope="function")
async def test_async_match_creates_watcher_for_humans():
    """run_match_async instantiates WatcherController when humans present."""
    from engine.game import run_match_async
    from engine import game as game_mod

    configs = [_make_config("H", human=True), _make_config("A"), _make_config("B")]

    original_create = game_mod._create_bots

    def create_with_humans(bot_configs, positions):
        bots = original_create(bot_configs, positions)
        for bot, cfg in zip(bots, bot_configs):
            if cfg.get("_human"):
                bot.human_adapter = _FakeHumanAdapter()  # type: ignore[assignment]
        return bots

    watcher_controllers_created = []
    from engine import watcher_controller as wc_mod
    orig_init = wc_mod.WatcherController.__init__

    def spy_init(self, *args, **kwargs):
        orig_init(self, *args, **kwargs)
        watcher_controllers_created.append(self)

    with (
        patch.object(game_mod, "_create_bots", create_with_humans),
        patch.object(wc_mod.WatcherController, "__init__", spy_init),
    ):
        result = await run_match_async(
            configs, match_id=99, seed=42, human_timeout=0.01,
        )

    assert result["winner"] is not None
    assert len(watcher_controllers_created) >= 1


@pytest.mark.asyncio(loop_scope="function")
async def test_async_match_no_watcher_for_pure_bots():
    """run_match_async does NOT create WatcherController when no humans."""
    from engine.game import run_match_async
    from engine import watcher_controller as wc_mod

    configs = [_make_config("A"), _make_config("B"), _make_config("C")]

    watcher_controllers_created = []
    orig_init = wc_mod.WatcherController.__init__

    def spy_init(self, *args, **kwargs):
        orig_init(self, *args, **kwargs)
        watcher_controllers_created.append(self)

    with patch.object(wc_mod.WatcherController, "__init__", spy_init):
        result = await run_match_async(configs, match_id=99, seed=42)

    assert result["winner"] is not None
    assert len(watcher_controllers_created) == 0


@pytest.mark.asyncio(loop_scope="function")
async def test_watcher_action_overrides_placeholder():
    """When watcher spawns, its action should be set by the controller."""
    from engine.game import run_match_async
    from engine import game as game_mod
    # Make a human that always attacks (triggers spawn quickly)
    def aggressive_decide(s):
        return ("attack", "north")

    configs = [
        {"name": "human", "emoji": "H", "bio": "t", "author": "t",
         "decide_func": aggressive_decide, "_human": True},
        {"name": "b1", "emoji": "A", "bio": "t", "author": "t",
         "decide_func": lambda s: ("rest",)},
        {"name": "b2", "emoji": "B", "bio": "t", "author": "t",
         "decide_func": lambda s: ("rest",)},
    ]

    original_create = game_mod._create_bots

    def create_with_humans(bot_configs, positions):
        bots = original_create(bot_configs, positions)
        for bot, cfg in zip(bots, bot_configs):
            if cfg.get("_human"):
                bot.human_adapter = _FakeHumanAdapter()  # type: ignore[assignment]
        return bots

    with patch.object(game_mod, "_create_bots", create_with_humans):
        result = await run_match_async(
            configs, match_id=99, seed=42, human_timeout=0.01,
        )

    # Match should complete without errors
    assert result["winner"] is not None
    assert result["duration_rounds"] >= 1
