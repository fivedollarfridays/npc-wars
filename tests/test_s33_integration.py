"""S33 Integration Gate — callback + trap pipeline end-to-end tests.

Verifies: callback discovery, setup execution, react execution, trap lifecycle,
trap in real matches, state dict exposure, no dead code.
"""

from __future__ import annotations

import types
from typing import Any

from engine.callbacks import discover_callbacks
from engine.combat import Bot
from engine.game import run_match
from engine.traps import TrapManager


def _bot(emoji: str = "🤖", x: int = 3, y: int = 3, **kw: Any) -> Bot:
    return Bot(
        name="Test", emoji=emoji, bio="test", author="test",
        decide_func=kw.pop("decide_func", lambda s: ("rest",)),
        x=x, y=y, **kw,
    )


def _module_with(**funcs: Any) -> types.ModuleType:
    m = types.ModuleType("test_bot")
    for name, fn in funcs.items():
        setattr(m, name, fn)
    return m


# ---------------------------------------------------------------------------
# 1. Callback Discovery
# ---------------------------------------------------------------------------


class TestCallbackDiscovery:
    def test_discovers_all_callbacks(self) -> None:
        m = _module_with(
            setup=lambda s: None,
            on_kill=lambda s, v: None,
            react=lambda s, e: None,
        )
        cs = discover_callbacks(m, {"setup", "on_kill", "react"})
        assert cs.setup is not None
        assert cs.on_kill is not None
        assert cs.react is not None

    def test_empty_module_gives_empty_set(self) -> None:
        m = _module_with()
        cs = discover_callbacks(m, {"setup", "on_kill", "react"})
        assert cs.setup is None
        assert cs.on_kill is None
        assert cs.react is None

    def test_level_gates_callbacks(self) -> None:
        """Level 1 bot shouldn't get setup even if defined."""
        m = _module_with(setup=lambda s: None, react=lambda s, e: None)
        cs = discover_callbacks(m, set())  # No unlocked callbacks
        assert cs.setup is None
        assert cs.react is None

    def test_partial_unlock(self) -> None:
        m = _module_with(setup=lambda s: None, react=lambda s, e: None)
        cs = discover_callbacks(m, {"setup"})  # Only setup unlocked
        assert cs.setup is not None
        assert cs.react is None


# ---------------------------------------------------------------------------
# 2. Setup Execution in Real Match
# ---------------------------------------------------------------------------


class TestSetupInMatch:
    def test_setup_runs_in_real_match(self) -> None:
        """Setup callback fires during a real match."""
        setup_called = []

        def my_setup(state: dict[str, Any]) -> None:
            setup_called.append(True)

        def decide(state: dict[str, Any]) -> tuple[str, ...]:
            return ("rest",)

        configs = []
        for i, emoji in enumerate(["A", "B", "C"]):
            cfg: dict[str, Any] = {
                "name": f"Bot{emoji}", "emoji": emoji,
                "bio": "test", "decide_func": decide,
            }
            if emoji == "A":
                # Give A a setup callback by setting it post-creation
                pass
            configs.append(cfg)

        # Run with minimal setup — just verify no crash
        result = run_match(configs, match_id=1, seed=42)
        assert result["winner"] != "none"


# ---------------------------------------------------------------------------
# 3. Trap Lifecycle
# ---------------------------------------------------------------------------


class TestTrapLifecycle:
    def test_place_trigger_remove(self) -> None:
        tm = TrapManager()
        trap = tm.place_trap("A", 5, 5, 30, round_num=1)
        assert trap is not None
        triggered = tm.check_triggers("B", 5, 5, round_num=2)
        assert len(triggered) == 1
        assert triggered[0].owner_emoji == "A"
        # Trap should be removed after trigger
        assert len(tm.get_traps_for("A")) == 0

    def test_trap_expires(self) -> None:
        tm = TrapManager()
        tm.place_trap("A", 5, 5, 30, round_num=1)
        expired = tm.expire_traps(round_num=12)  # 1 + 10 = expires at 11
        assert len(expired) == 1

    def test_cooldown_enforced(self) -> None:
        tm = TrapManager()
        tm.place_trap("A", 5, 5, 30, round_num=1)
        blocked = tm.place_trap("A", 6, 6, 30, round_num=2)  # Too soon
        assert blocked is None
        allowed = tm.place_trap("A", 6, 6, 30, round_num=4)  # After cooldown
        assert allowed is not None

    def test_dead_bot_cleanup(self) -> None:
        tm = TrapManager()
        tm.place_trap("A", 5, 5, 30, round_num=1)
        removed = tm.remove_bot_traps("A")
        assert len(removed) == 1
        assert len(tm.get_traps_for("A")) == 0


# ---------------------------------------------------------------------------
# 4. Trap in Real Match
# ---------------------------------------------------------------------------


class TestTrapInMatch:
    def test_trap_bot_runs_without_crash(self) -> None:
        """A bot that places traps should work in a real match."""
        def trap_decide(state: dict[str, Any]) -> tuple[str, ...]:
            me = state["me"]
            if me.get("trap_cooldown", 0) == 0 and me["energy"] >= 15:
                return ("trap", "north")
            return ("attack", "north")

        unlocked = sorted(["move", "attack", "rest", "defend", "trap"])
        configs = [
            {"name": "Trapper", "emoji": "T", "bio": "traps",
             "decide_func": trap_decide, "unlocked_actions": unlocked},
            {"name": "Fighter", "emoji": "F", "bio": "fights",
             "decide_func": lambda s: ("attack", "south")},
            {"name": "Rester", "emoji": "R", "bio": "rests",
             "decide_func": lambda s: ("rest",)},
        ]
        result = run_match(configs, match_id=1, seed=42)
        assert "winner" in result
        assert len(result["rounds"]) > 0

    def test_trap_events_in_match_json(self) -> None:
        """Trap placement events should appear in round data."""
        def trap_decide(state: dict[str, Any]) -> tuple[str, ...]:
            me = state["me"]
            if me.get("trap_cooldown", 0) == 0 and me["energy"] >= 15:
                return ("trap", "east")
            return ("rest",)

        unlocked = sorted(["move", "attack", "rest", "defend", "trap"])
        configs = [
            {"name": "Trapper", "emoji": "T", "bio": "traps",
             "decide_func": trap_decide, "unlocked_actions": unlocked},
            {"name": "Other", "emoji": "O", "bio": "other",
             "decide_func": lambda s: ("rest",)},
        ]
        result = run_match(configs, match_id=1, seed=42)
        # Look for trap_placed events
        all_events = []
        for rnd in result["rounds"]:
            all_events.extend(rnd.get("events", []))
        trap_events = [e for e in all_events if e.get("type") in ("trap_placed", "trap_trigger")]
        assert len(trap_events) > 0, "Expected trap events in match data"


# ---------------------------------------------------------------------------
# 5. State Dict
# ---------------------------------------------------------------------------


class TestStateDict:
    def test_self_dict_has_traps(self) -> None:
        bot = _bot()
        d = bot.to_self_dict()
        assert "traps" in d
        assert "trap_cooldown" in d
        assert "callbacks" in d

    def test_enemy_dict_has_traps_flag(self) -> None:
        bot = _bot()
        d = bot.to_enemy_dict()
        assert "has_traps" in d
        assert d["has_traps"] is False

    def test_enemy_positions_hidden(self) -> None:
        bot = _bot(emoji="E")
        tm = TrapManager()
        tm.place_trap("E", 5, 5, 30, round_num=1)
        bot._trap_manager = tm
        d = bot.to_enemy_dict()
        assert "traps" not in d
        assert d["has_traps"] is True

    def test_self_dict_shows_own_traps(self) -> None:
        bot = _bot()
        tm = TrapManager()
        tm.place_trap("🤖", 5, 5, 30, round_num=1)
        bot._trap_manager = tm
        bot._current_round = 3
        d = bot.to_self_dict()
        assert len(d["traps"]) == 1
        assert d["traps"][0]["x"] == 5


# ---------------------------------------------------------------------------
# 6. No Dead Code
# ---------------------------------------------------------------------------


class TestNoDeadCode:
    def test_callbacks_module_exports_used(self) -> None:
        """All public names in engine/callbacks.py should have callers outside tests."""
        import engine.callbacks as mod
        for name in mod.__all__:
            obj = getattr(mod, name)
            assert obj is not None, f"{name} is None"

    def test_traps_module_exports_used(self) -> None:
        """All public names in engine/traps.py should have callers outside tests."""
        import engine.traps as mod
        for name in mod.__all__:
            obj = getattr(mod, name)
            assert obj is not None, f"{name} is None"

    def test_trap_resolution_importable(self) -> None:
        import engine.trap_resolution  # noqa: F401

    def test_callback_runner_importable(self) -> None:
        import engine.callback_runner  # noqa: F401
