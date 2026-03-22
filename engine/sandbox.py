"""Sandbox for executing bot decide() functions safely.

Uses multiprocessing for OS-level isolation: bots run in a separate process
with a deep-copied state dict. Timed-out processes are killed (not abandoned).
"""

import logging
import multiprocessing
from typing import Any, Callable

from engine.combat import DEFAULT_UNLOCKED_ACTIONS

log = logging.getLogger(__name__)

__all__ = [
    "BotExecutionError", "execute_decide",
    "VALID_DIRECTIONS", "VALID_ACTIONS", "validate_action",
    "BASE_ACTIONS", "ACTION_UNLOCK_THRESHOLDS",
]

_STATUS_OK = "ok"
_STATUS_ERROR = "error"


class BotExecutionError(Exception):
    pass


def _run_decide(queue: multiprocessing.Queue, decide_func: Callable[..., Any], state: dict[str, Any]) -> None:  # type: ignore[type-arg]
    """Worker: call decide on state, put result on queue.

    State is already an independent copy (deserialized from pickle by
    the multiprocessing boundary), so no deepcopy is needed.
    """
    try:
        result = decide_func(state)
        queue.put((_STATUS_OK, result))
    except Exception as e:
        queue.put((_STATUS_ERROR, str(e)))


def execute_decide(decide_func: Callable[..., Any], state: dict[str, Any], timeout: float = 1.0) -> tuple[str, ...] | None:
    """Execute a bot's decide() function with timeout.

    Returns the action tuple, or None if the bot failed/timed out.
    """
    queue: multiprocessing.Queue = multiprocessing.Queue()  # type: ignore[type-arg]
    process = multiprocessing.Process(target=_run_decide, args=(queue, decide_func, state))
    process.start()
    try:
        process.join(timeout)

        if process.is_alive():
            process.kill()
            process.join()
            log.warning("Bot decide() timeout after %.1fs", timeout)
            return None

        if queue.empty():
            log.warning("Bot decide() process died without returning a result")
            return None

        status, value = queue.get_nowait()
        if status == _STATUS_ERROR:
            log.warning("Bot decide() raised an exception: %s", value)
            return None

        rv: tuple[str, ...] | None = value
        return rv
    finally:
        queue.close()
        queue.join_thread()


BASE_ACTIONS = DEFAULT_UNLOCKED_ACTIONS

ACTION_UNLOCK_THRESHOLDS = {
    "ranged_attack": 3,
    "dash": 5,
    "taunt": 10,
}

VALID_DIRECTIONS = {"north", "south", "east", "west"}

VALID_ACTIONS = {
    "move": 1,      # expects 1 extra arg (direction)
    "attack": 1,    # expects 1 extra arg (direction)
    "rest": 0,      # no extra args
    "defend": 0,    # no extra args
    "ranged_attack": 1,  # expects 1 extra arg (direction)
    "taunt": 0,          # no extra args
    "dash": 1,           # expects 1 extra arg (direction)
    "trap": 1,           # expects 1 extra arg (direction)
    "use_tactical": -1,  # 0 args (battle_cry/fortify) or 1 arg (teleport direction)
    "use_ability": -1,   # 0 args (self-target) or 1 arg (direction for targeted)
}


def validate_action(action: Any, unlocked_actions: set[str] | None = None) -> tuple[str, ...] | None:
    """Validate an action tuple returned by decide().

    If unlocked_actions is provided, non-base actions must be in the set.
    Returns normalized action tuple or None if invalid/locked.
    """
    if not isinstance(action, (tuple, list)):
        return None

    if len(action) == 0:
        return None

    action_type = action[0]
    if action_type not in VALID_ACTIONS:
        return None

    # Unlock gating: non-base actions must be explicitly unlocked
    if unlocked_actions is not None and action_type not in BASE_ACTIONS:
        if action_type not in unlocked_actions:
            return None

    expected_args = VALID_ACTIONS[action_type]

    if expected_args == 0:
        return (action_type,)

    # Variable args: 0 or 1 (use_tactical)
    if expected_args == -1:
        if len(action) >= 2:
            direction = action[1]
            if direction not in VALID_DIRECTIONS:
                return None
            return (action_type, direction)
        return (action_type,)

    if len(action) < 2:
        return None

    if action_type in ("move", "attack", "ranged_attack", "dash", "trap"):
        direction = action[1]
        if direction not in VALID_DIRECTIONS:
            return None
        return (action_type, direction)

    return None
