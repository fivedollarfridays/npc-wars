"""Tests for engine/decision_trace.py — decision tracing for bot execution."""

import importlib.util
import sys
import types
from pathlib import Path
from textwrap import dedent

import pytest


def _make_bot_module(tmp_path: Path, name: str, source: str) -> types.ModuleType:
    """Write source to a temp .py file and import it as a module."""
    path = tmp_path / f"{name}.py"
    path.write_text(dedent(source))
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# -- Fixtures: bot modules --------------------------------------------------


@pytest.fixture()
def simple_bot(tmp_path):
    """Bot with a linear if/elif chain and BOT_TRACE enabled."""
    return _make_bot_module(tmp_path, "_test_simple_bot", """\
        BOT_NAME = "Simple"
        BOT_EMOJI = "S"
        BOT_TRACE = True

        def decide(state):
            me = state["me"]
            if me["hp"] < 30:
                return ("rest",)
            if me["energy"] < 20:
                return ("rest",)
            return ("attack", "north")
    """)


@pytest.fixture()
def complex_bot(tmp_path):
    """Bot that delegates to helper functions within the module."""
    return _make_bot_module(tmp_path, "_test_complex_bot", """\
        BOT_NAME = "Complex"
        BOT_EMOJI = "C"
        BOT_TRACE = True

        def _should_flee(me):
            if me["hp"] < 20:
                return True
            return False

        def _pick_combat(me):
            if me["energy"] >= 30:
                return ("attack", "south")
            return ("defend",)

        def decide(state):
            me = state["me"]
            if _should_flee(me):
                return ("move", "north")
            return _pick_combat(me)
    """)


@pytest.fixture()
def no_trace_bot(tmp_path):
    """Bot without BOT_TRACE flag — tracing should be skipped."""
    return _make_bot_module(tmp_path, "_test_no_trace_bot", """\
        BOT_NAME = "Silent"
        BOT_EMOJI = "N"

        def decide(state):
            return ("rest",)
    """)


@pytest.fixture()
def base_state():
    return {
        "me": {"hp": 100, "energy": 50, "x": 3, "y": 3},
        "enemies": [],
        "round": 5,
        "grid_size": 10,
        "storm_border": 0,
    }


# -- Tests -------------------------------------------------------------------


class TestTraceDecisionSignature:
    """trace_decision(bot_module, state) returns (action, trace_dict)."""

    def test_returns_action_and_trace(self, simple_bot, base_state):
        from engine.decision_trace import trace_decision

        action, trace = trace_decision(simple_bot, base_state)
        assert isinstance(action, tuple)
        assert trace is not None

    def test_no_trace_flag_returns_none_trace(self, no_trace_bot, base_state):
        from engine.decision_trace import trace_decision

        action, trace = trace_decision(no_trace_bot, base_state)
        assert action == ("rest",)
        assert trace is None


class TestTraceCapture:
    """Trace captures conditions checked, branch taken, key state values."""

    def test_trace_has_required_keys(self, simple_bot, base_state):
        from engine.decision_trace import trace_decision

        _, trace = trace_decision(simple_bot, base_state)
        assert "conditions_checked" in trace
        assert "branch_taken" in trace
        assert "state_snapshot" in trace

    def test_conditions_are_readable_strings(self, simple_bot, base_state):
        from engine.decision_trace import trace_decision

        _, trace = trace_decision(simple_bot, base_state)
        for cond in trace["conditions_checked"]:
            assert isinstance(cond, str)
            assert len(cond) > 0

    def test_healthy_bot_checks_hp_and_energy(self, simple_bot, base_state):
        """With hp=100, energy=50: both conditions checked, neither taken."""
        from engine.decision_trace import trace_decision

        action, trace = trace_decision(simple_bot, base_state)
        assert action == ("attack", "north")
        checked = trace["conditions_checked"]
        assert any("hp" in c for c in checked)
        assert any("energy" in c for c in checked)

    def test_low_hp_takes_rest_branch(self, simple_bot, base_state):
        """With hp=10: first condition fires, returns rest."""
        from engine.decision_trace import trace_decision

        base_state["me"]["hp"] = 10
        action, trace = trace_decision(simple_bot, base_state)
        assert action == ("rest",)
        assert "hp" in trace["branch_taken"]

    def test_low_energy_takes_energy_branch(self, simple_bot, base_state):
        """With hp=100, energy=5: second condition fires."""
        from engine.decision_trace import trace_decision

        base_state["me"]["energy"] = 5
        action, trace = trace_decision(simple_bot, base_state)
        assert action == ("rest",)
        assert "energy" in trace["branch_taken"]

    def test_state_snapshot_captures_key_values(self, simple_bot, base_state):
        from engine.decision_trace import trace_decision

        _, trace = trace_decision(simple_bot, base_state)
        snap = trace["state_snapshot"]
        assert snap["hp"] == 100
        assert snap["energy"] == 50
        assert snap["round"] == 5


class TestComplexBot:
    """Bot with helper functions and callbacks."""

    def test_traces_across_helper_functions(self, complex_bot, base_state):
        from engine.decision_trace import trace_decision

        action, trace = trace_decision(complex_bot, base_state)
        # hp=100 so _should_flee returns False, then _pick_combat with energy=50
        assert action == ("attack", "south")
        assert trace is not None
        assert len(trace["conditions_checked"]) >= 1

    def test_flee_branch_when_low_hp(self, complex_bot, base_state):
        from engine.decision_trace import trace_decision

        base_state["me"]["hp"] = 10
        action, trace = trace_decision(complex_bot, base_state)
        assert action == ("move", "north")
        assert any("hp" in c for c in trace["conditions_checked"])


class TestOptIn:
    """BOT_TRACE = True opt-in flag."""

    def test_bot_trace_false_skips(self, tmp_path, base_state):
        from engine.decision_trace import trace_decision

        bot = _make_bot_module(tmp_path, "_test_trace_false", """\
            BOT_NAME = "Off"
            BOT_EMOJI = "O"
            BOT_TRACE = False

            def decide(state):
                return ("defend",)
        """)
        action, trace = trace_decision(bot, base_state)
        assert action == ("defend",)
        assert trace is None

    def test_missing_bot_trace_skips(self, no_trace_bot, base_state):
        from engine.decision_trace import trace_decision

        _, trace = trace_decision(no_trace_bot, base_state)
        assert trace is None


class TestStateIsolation:
    """Tracing must not mutate the caller's state dict."""

    def test_state_not_mutated(self, simple_bot, base_state):
        from engine.decision_trace import trace_decision
        import copy

        original = copy.deepcopy(base_state)
        trace_decision(simple_bot, base_state)
        assert base_state == original


class TestBuiltinBots:
    """Trace works with all builtin bot modules."""

    @pytest.fixture()
    def full_state(self):
        """Realistic state dict that satisfies bot helper DSL."""
        return {
            "me": {
                "hp": 80, "energy": 60, "x": 5, "y": 5,
                "attack_power": 25, "defense": 0,
                "power": 25, "speed": 25, "armor": 25, "mind": 25,
                "max_hp": 100, "max_energy": 100,
                "min_damage": 20, "max_damage": 30,
                "dodge_chance": 0.0, "damage_reduction": 0.0,
                "unlocked_actions": ["move", "attack", "rest", "defend", "trap"],
                "score": 10, "momentum_tier": 0, "momentum_name": "neutral",
                "is_leader": False, "kills": 0, "passive_rounds": 0,
                "traps": [], "trap_cooldown": 0, "tactical_cooldown": 0,
                "callbacks": [], "equipment": {},
                "equipment_bonuses": {},
                "ability": None,
                "on_terrain": None,
                "terrain": {"map": "arena", "walls": [], "water": [],
                            "high_ground": [], "cover": [], "crystals": []},
                "hit_chance_vs": {}, "incoming_threat": [],
                "glyph": "X",
            },
            "enemies": [
                {"name": "Rival", "emoji": "R", "glyph": "R",
                 "x": 7, "y": 5, "hp": 50, "score": 5,
                 "momentum_tier": 0, "is_leader": False,
                 "max_hp": 100, "speed_class": "normal",
                 "has_traps": False, "trap_count": 0,
                 "weapon": "fists", "armor": "none",
                 "has_ability": False, "on_terrain": None},
            ],
            "round": 5,
            "grid_size": 12,
            "storm_border": 0,
            "bumps_last_round": [],
        }

    @pytest.mark.parametrize("bot_file", [
        "starter", "example_aggro", "example_random", "example_tank",
        "example_kiter", "example_trapper", "example_vibes",
        "reaper", "shadow_dancer", "viper", "goose_loose",
    ])
    def test_trace_produces_output_for_builtin(self, bot_file, full_state):
        """Each builtin bot can be traced without errors."""
        from engine.decision_trace import trace_decision
        import importlib

        mod = importlib.import_module(f"bots.{bot_file}")
        # Temporarily enable tracing
        original = getattr(mod, "BOT_TRACE", None)
        mod.BOT_TRACE = True
        try:
            action, trace = trace_decision(mod, full_state)
            assert isinstance(action, tuple)
            assert trace is not None
            assert "conditions_checked" in trace
            assert "branch_taken" in trace
            assert "state_snapshot" in trace
        finally:
            if original is None:
                delattr(mod, "BOT_TRACE")
            else:
                mod.BOT_TRACE = original
