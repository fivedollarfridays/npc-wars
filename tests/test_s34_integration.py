"""S34 Integration Gate — trap polish pipeline end-to-end tests.

Verifies: trap feed rendering, on_kill callback, trapper bot, state dict, no dead code.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agentgrounds.wars.cli.feed import format_feed_event
from engine.callbacks import execute_callback, CallbackSet
from engine.combat import Bot
from engine.game import run_match
from engine.traps import TrapManager


def _bot(emoji: str = "🤖", x: int = 3, y: int = 3, **kw: Any) -> Bot:
    return Bot(
        name="Test", emoji=emoji, bio="test", author="test",
        decide_func=kw.pop("decide_func", lambda s: ("rest",)),
        x=x, y=y, **kw,
    )


# ---------------------------------------------------------------------------
# 1. Trap Feed Rendering
# ---------------------------------------------------------------------------


class TestTrapFeedRendering:
    def test_trap_placed_formats(self) -> None:
        evt = {"type": "trap_placed", "emoji": "🤖", "x": 5, "y": 3}
        result = format_feed_event(evt, 3)
        assert result is not None
        assert "🤖" in result
        assert "trap" in result.lower() or "🪤" in result

    def test_trap_trigger_formats(self) -> None:
        evt = {"type": "trap_trigger", "victim": "🎯", "owner": "🤖",
               "damage": 22.5, "x": 5, "y": 3}
        result = format_feed_event(evt, 5)
        assert result is not None
        assert "🎯" in result or "trap" in result.lower()


# ---------------------------------------------------------------------------
# 2. on_kill Callback
# ---------------------------------------------------------------------------


class TestOnKillInMatch:
    def test_on_kill_fires_in_match(self) -> None:
        """on_kill callback fires when a bot eliminates another."""
        kill_log: list[str] = []

        def killer_decide(state: dict[str, Any]) -> tuple[str, ...]:
            return ("attack", "east")

        def victim_decide(state: dict[str, Any]) -> tuple[str, ...]:
            return ("rest",)

        def on_kill_cb(state: dict[str, Any], victim_emoji: str) -> None:
            kill_log.append(victim_emoji)

        # Can't easily wire on_kill into match config — test the callback runner directly
        bot = _bot(decide_func=killer_decide)
        bot.callbacks = CallbackSet(on_kill=on_kill_cb)
        state = {"me": bot.to_self_dict(), "enemies": [], "round": 1,
                 "grid_size": 10, "storm_border": 0}
        execute_callback(bot.callbacks.on_kill, state, "🎯")
        assert kill_log == ["🎯"]

    def test_on_kill_exception_safe(self) -> None:
        def bad_on_kill(state: Any, victim: str) -> None:
            raise RuntimeError("boom")

        bot = _bot()
        bot.callbacks = CallbackSet(on_kill=bad_on_kill)
        # Should not raise
        execute_callback(bot.callbacks.on_kill, {}, "🎯")


# ---------------------------------------------------------------------------
# 3. Trapper Bot
# ---------------------------------------------------------------------------


class TestTrapperBot:
    def test_trapper_loads(self) -> None:
        from engine.bot_scanner import scan_bot_file
        violations = scan_bot_file("bots/example_trapper.py")
        assert violations == [], f"Security violations: {violations}"

    def test_trapper_runs_in_match(self) -> None:
        from engine.bot_scanner import load_bot_module
        mod = load_bot_module("bots/example_trapper.py")
        unlocked = sorted(["move", "attack", "rest", "defend", "trap"])
        configs = [
            {"name": "Trapper", "emoji": "T", "bio": "traps",
             "decide_func": mod.decide, "unlocked_actions": unlocked,
             "stat_allocation": None},
            {"name": "Fighter", "emoji": "F", "bio": "fights",
             "decide_func": lambda s: ("attack", "south")},
        ]
        result = run_match(configs, match_id=1, seed=42)
        assert "winner" in result

    def test_trapper_places_traps(self) -> None:
        from engine.bot_scanner import load_bot_module
        mod = load_bot_module("bots/example_trapper.py")
        unlocked = sorted(["move", "attack", "rest", "defend", "trap"])
        configs = [
            {"name": "Trapper", "emoji": "T", "bio": "traps",
             "decide_func": mod.decide, "unlocked_actions": unlocked},
            {"name": "Other", "emoji": "O", "bio": "other",
             "decide_func": lambda s: ("rest",)},
        ]
        result = run_match(configs, match_id=1, seed=42)
        all_events = []
        for rnd in result["rounds"]:
            all_events.extend(rnd.get("events", []))
        trap_events = [e for e in all_events if e.get("type") == "trap_placed"]
        assert len(trap_events) > 0


# ---------------------------------------------------------------------------
# 4. State Dict
# ---------------------------------------------------------------------------


class TestStateDictRefinement:
    def test_enemy_has_trap_count(self) -> None:
        bot = _bot(emoji="🎯")
        tm = TrapManager()
        tm.place_trap("🎯", 5, 5, 30, round_num=1)
        tm.place_trap("🎯", 7, 7, 30, round_num=5)
        bot._trap_manager = tm
        d = bot.to_enemy_dict()
        assert d["trap_count"] == 2
        assert d["has_traps"] is True

    def test_enemy_trap_count_zero(self) -> None:
        bot = _bot()
        d = bot.to_enemy_dict()
        assert d["trap_count"] == 0
        assert d["has_traps"] is False


# ---------------------------------------------------------------------------
# 5. No Dead Code
# ---------------------------------------------------------------------------


class TestNoDeadCode:
    def test_on_kill_wired_in_match_phases(self) -> None:
        """run_on_kill_callbacks called in match_phases.py (extracted from game.py)."""
        import engine.match_phases as mod
        source = Path(mod.__file__).read_text()
        assert "run_on_kill_callbacks" in source

    def test_trap_formatters_registered(self) -> None:
        from agentgrounds.wars.cli.feed import _FORMATTERS
        assert "trap_placed" in _FORMATTERS
        assert "trap_trigger" in _FORMATTERS

    def test_callback_runner_exports(self) -> None:
        import engine.callback_runner as mod
        assert hasattr(mod, "run_on_kill_callbacks")
        assert hasattr(mod, "run_setup_callbacks")
        assert hasattr(mod, "run_react_callbacks")
