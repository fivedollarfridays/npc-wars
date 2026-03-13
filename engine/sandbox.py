"""Sandbox for executing bot decide() functions safely.

For local play, this uses threading-based timeout.
For production (community PRs), upgrade to subprocess isolation.
"""

import threading
import traceback

__all__ = [
    "BotExecutionError", "execute_decide",
    "VALID_DIRECTIONS", "VALID_ACTIONS", "validate_action",
]


class BotExecutionError(Exception):
    pass


def execute_decide(decide_func, state: dict, timeout: float = 1.0) -> tuple | None:
    """Execute a bot's decide() function with timeout.
    
    Returns the action tuple, or None if the bot failed/timed out.
    """
    result = [None]
    error = [None]

    def run():
        try:
            result[0] = decide_func(state)
        except Exception as e:
            error[0] = str(e)

    thread = threading.Thread(target=run)
    thread.daemon = True
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        return None  # Timeout

    if error[0] is not None:
        return None  # Exception

    return result[0]


VALID_DIRECTIONS = {"north", "south", "east", "west"}

VALID_ACTIONS = {
    "move": 1,      # expects 1 extra arg (direction)
    "attack": 1,    # expects 1 extra arg (direction)
    "rest": 0,      # no extra args
    "defend": 0,    # no extra args
}


def validate_action(action) -> tuple | None:
    """Validate an action tuple returned by decide().
    
    Returns normalized action tuple or None if invalid.
    """
    if not isinstance(action, (tuple, list)):
        return None

    if len(action) == 0:
        return None

    action_type = action[0]
    if action_type not in VALID_ACTIONS:
        return None

    expected_args = VALID_ACTIONS[action_type]

    if expected_args == 0:
        return (action_type,)

    if len(action) < 2:
        return None

    if action_type in ("move", "attack"):
        direction = action[1]
        if direction not in VALID_DIRECTIONS:
            return None
        return (action_type, direction)

    return None
