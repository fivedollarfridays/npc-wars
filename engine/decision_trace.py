"""Instrument bot decide() to capture which branch fired each round.

Records execution path (conditions evaluated, branch taken, key state values)
without exposing source code. Opt-in per bot via BOT_TRACE = True.
"""

from __future__ import annotations

import ast
import copy
import inspect
import sys
import types
from typing import Any

__all__ = ["trace_decision", "collect_round_traces"]

_Condition = tuple[int, str]  # (line_number, condition_source)


def _extract_conditions(source: str) -> list[_Condition]:
    """Parse module source and extract if/elif condition strings with line numbers."""
    tree = ast.parse(source)
    conditions: list[_Condition] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            try:
                cond_text = ast.unparse(node.test)
            except Exception:
                cond_text = f"<condition at line {node.lineno}>"
            conditions.append((node.lineno, cond_text))
    return conditions


def _snapshot_state(state: dict[str, Any]) -> dict[str, Any]:
    """Extract key state values for the trace."""
    me = state.get("me", {})
    return {
        "hp": me.get("hp"),
        "energy": me.get("energy"),
        "x": me.get("x"),
        "y": me.get("y"),
        "round": state.get("round"),
        "enemies_alive": len(state.get("enemies", [])),
        "storm_border": state.get("storm_border"),
    }


def _build_trace(
    conditions: list[_Condition],
    executed_lines: set[int],
    state: dict[str, Any],
) -> dict[str, Any]:
    """Build trace dict from conditions and executed lines."""
    checked: list[str] = []
    branch_taken = "default"

    for lineno, cond_text in conditions:
        if lineno in executed_lines:
            checked.append(cond_text)
            # If the line after the condition was also executed, the branch was taken
            # Use lineno+1 as heuristic for body entry
            if (lineno + 1) in executed_lines:
                branch_taken = cond_text

    return {
        "conditions_checked": checked,
        "branch_taken": branch_taken,
        "state_snapshot": _snapshot_state(state),
    }


def trace_decision(
    bot_module: types.ModuleType,
    state: dict[str, Any],
) -> tuple[tuple[str, ...], dict[str, Any] | None]:
    """Execute bot's decide() with execution tracing.

    Returns (action, trace_dict). If BOT_TRACE is not set or False,
    returns (action, None) with no tracing overhead.
    """
    if not getattr(bot_module, "BOT_TRACE", False):
        action = bot_module.decide(state)
        return action, None

    # Deep-copy state so tracing doesn't mutate the caller's dict
    traced_state = copy.deepcopy(state)

    # Parse source for conditions
    source = inspect.getsource(bot_module)
    source_file = inspect.getfile(bot_module)
    conditions = _extract_conditions(source)

    # Track executed lines via sys.settrace
    executed_lines: set[int] = set()

    def tracer(frame: Any, event: str, arg: Any) -> Any:
        if frame.f_code.co_filename == source_file and event == "line":
            executed_lines.add(frame.f_lineno)
        return tracer

    old_trace = sys.gettrace()
    sys.settrace(tracer)
    try:
        action = bot_module.decide(traced_state)
    finally:
        sys.settrace(old_trace)

    trace = _build_trace(conditions, executed_lines, state)
    return action, trace


def collect_round_traces(
    alive_bots: list[Any],
    all_bots: list[Any],
    round_num: int,
    grid_size: int,
    storm_border: int,
    bumps_last_round: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Collect decision traces for all opted-in bots in a round."""
    from engine.state import build_state

    traces: dict[str, Any] = {}
    for bot in alive_bots:
        module = getattr(bot, "module", None)
        if module is not None and getattr(module, "BOT_TRACE", False):
            state = build_state(bot, all_bots, round_num, grid_size, storm_border,
                                bumps_last_round=bumps_last_round)
            _, trace = trace_decision(module, state)
            if trace is not None:
                traces[bot.emoji] = trace
    return traces
