"""Sandbox for executing bot decide() functions safely.

Uses multiprocessing for OS-level isolation: bots run in a separate process
with a deep-copied state dict. Timed-out processes are killed (not abandoned).
"""

import logging
import multiprocessing
import zlib
from typing import Any, Callable

from engine.combat import DEFAULT_UNLOCKED_ACTIONS

log = logging.getLogger(__name__)

__all__ = [
    "BotExecutionError", "execute_decide",
    "VALID_DIRECTIONS", "VALID_ACTIONS", "validate_action",
    "classify_action", "LOCKED",
    "BASE_ACTIONS", "ACTION_UNLOCK_THRESHOLDS",
]


class _Locked:
    """Sentinel for a well-formed action that the bot has not unlocked yet.

    Distinct from None (malformed). Only the resolve_decisions caller checks
    for this; validate_action's contract (valid tuple / None) is unchanged.
    """

    __slots__ = ()

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return "LOCKED"


LOCKED = _Locked()

_STATUS_OK = "ok"
_STATUS_ERROR = "error"


class BotExecutionError(Exception):
    pass


def _deterministic_seed(state: dict[str, Any]) -> int:
    """Derive a reproducible RNG seed from observable game state.

    Forked decide() children do NOT inherit the parent's seeded global
    ``random`` state, so a bot using ``import random`` is otherwise
    non-reproducible (breaking byte-stable balance baselines). We seed the
    child's global RNG from the round + the bot's own position/vitals so the
    decision is a deterministic function of identical inputs. CRC32 over a
    string key keeps the value independent of PYTHONHASHSEED.
    """
    me = state.get("me", {}) if isinstance(state, dict) else {}
    key = "|".join(
        str(v)
        for v in (
            state.get("round", 0) if isinstance(state, dict) else 0,
            me.get("x", 0), me.get("y", 0),
            me.get("hp", 0), me.get("energy", 0),
            me.get("emoji", ""),
        )
    )
    return zlib.crc32(key.encode("utf-8"))


def _run_decide(queue: multiprocessing.Queue, decide_func: Callable[..., Any], state: dict[str, Any]) -> None:  # type: ignore[type-arg]
    """Worker: call decide on state, put result on queue.

    State is already an independent copy (deserialized from pickle by
    the multiprocessing boundary), so no deepcopy is needed.
    """
    try:
        import random

        random.seed(_deterministic_seed(state))
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


def classify_action(action: Any, unlocked_actions: set[str]) -> tuple[str, ...] | None | _Locked:
    """Three-way classification of a decide() action.

    Returns one of:
      * a normalized action tuple -- valid and unlocked,
      * ``LOCKED`` -- well-formed but the bot has not unlocked this action,
      * ``None`` -- malformed (bad type/shape/direction).

    Malformed takes precedence over locked: a locked action with bad args is
    still ``None``. This is a sibling of :func:`validate_action`; the latter's
    contract is left untouched so existing callers keep working.
    """
    # Normalize ignoring unlock gating; None here means genuinely malformed.
    normalized = validate_action(action, unlocked_actions=None)
    if normalized is None:
        return None
    action_type = normalized[0]
    if action_type not in BASE_ACTIONS and action_type not in unlocked_actions:
        return LOCKED
    return normalized
