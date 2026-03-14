"""The Cringe's brain — sync rating and pattern tracking."""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass

from engine.grid import direction_toward
from engine.watcher_memory import GLOBAL_PROFILE, PatternTable

__all__ = [
    "COUNTER_MAP",
    "HumanPerformance",
    "SyncTracker",
    "apply_accuracy_cap",
    "get_accuracy_cap",
    "select_counter_action",
    "select_target",
]


@dataclass(frozen=True)
class HumanPerformance:
    """Snapshot of a human player's current match performance."""

    hp_ratio: float
    kills: int
    rounds_survived: int


def get_accuracy_cap(performance: HumanPerformance) -> float:
    """Return accuracy cap based on how well the human is doing.

    Tiers (checked top-to-bottom, first match wins):
    - Dominating: hp_ratio >= 0.7 and kills >= 3 -> 0.95
    - Winning:    hp_ratio >= 0.5 and kills >= 2 -> 0.90
    - Losing:     hp_ratio < 0.3 and kills == 0  -> 0.60
    - Even (default):                             -> 0.75
    """
    if performance.hp_ratio >= 0.7 and performance.kills >= 3:
        return 0.95
    if performance.hp_ratio >= 0.5 and performance.kills >= 2:
        return 0.90
    if performance.hp_ratio < 0.3 and performance.kills == 0:
        return 0.60
    return 0.75


def apply_accuracy_cap(
    counter_action: tuple[str, ...],
    cap: float,
    all_actions: list[str],
    rng: random.Random,
) -> tuple[str, ...]:
    """Apply accuracy cap probabilistically.

    If rng.random() > cap, return a random action instead of the counter.
    """
    if rng.random() > cap:
        return (rng.choice(all_actions),)
    return counter_action


COUNTER_MAP: dict[str, str] = {
    "move": "move",              # intercept: move toward target
    "attack": "defend",
    "rest": "move",              # rush: move toward (attack if adjacent)
    "defend": "ranged_attack",
    "ranged_attack": "dash",     # close distance
    "dash": "taunt",
}


def select_counter_action(
    pattern_table: PatternTable,
    target_id: str,
    watcher_x: int,
    watcher_y: int,
    target_x: int,
    target_y: int,
    contexts: list[str],
    all_actions: set[str],
) -> tuple[str, ...]:
    """Select a counter-action based on predicted human behavior.

    Queries predict() for each context, picks the one with the
    highest-confidence prediction, looks up the counter from COUNTER_MAP,
    and resolves direction based on positions.
    """
    predicted_action = _predict_best(pattern_table, target_id, contexts)
    counter = COUNTER_MAP.get(predicted_action, "move")
    return _resolve_action(counter, watcher_x, watcher_y, target_x, target_y, all_actions)


def _predict_best(
    table: PatternTable, target_id: str, contexts: list[str],
) -> str:
    """Find the predicted action with highest confidence across contexts.

    Checks the target player first; falls back to the global profile if
    no data exists for the target.
    """
    best_action = "move"
    best_conf = 0.0

    for pid in (target_id, GLOBAL_PROFILE):
        for ctx in contexts:
            probs = table.predict(pid, ctx)
            if not probs:
                continue
            top_action = max(probs, key=lambda a: probs[a])
            if probs[top_action] > best_conf:
                best_conf = probs[top_action]
                best_action = top_action
        if best_conf > 0.0:
            break

    return best_action


def _resolve_action(
    action_type: str,
    watcher_x: int, watcher_y: int,
    target_x: int, target_y: int,
    all_actions: set[str],
) -> tuple[str, ...]:
    """Convert an action type into a valid action tuple with direction."""
    if action_type not in all_actions:
        action_type = "move"

    direction = direction_toward(watcher_x, watcher_y, target_x, target_y)

    # Actions that need a direction argument
    directional = {"move", "attack", "ranged_attack", "dash"}
    if action_type in directional:
        return (action_type, direction)
    return (action_type,)


def select_target(
    sync_tracker: SyncTracker,
    human_emojis: list[str],
) -> str | None:
    """Return the player_id of the human with the highest sync rating.

    Ties are broken by sorted order (earliest emoji alphabetically).
    Returns None if human_emojis is empty.
    """
    if not human_emojis:
        return None
    return max(
        sorted(human_emojis),
        key=lambda pid: sync_tracker.get_sync(pid),
    )


class SyncTracker:
    """Tracks how accurately The Cringe predicts each player's actions.

    Maintains a rolling window of the last 10 prediction outcomes per player
    and computes a sync rating (0.0-100.0) as the accuracy percentage.
    """

    _WINDOW = 10

    def __init__(self) -> None:
        self._history: dict[str, deque[bool]] = {}

    def get_sync(self, player_id: str) -> float:
        """Return sync rating (0.0-100.0) for a player."""
        outcomes = self._history.get(player_id)
        if not outcomes:
            return 0.0
        return (sum(outcomes) / len(outcomes)) * 100.0

    def record_prediction(
        self, player_id: str, predicted_action: str, actual_action: str
    ) -> None:
        """Record whether a prediction was correct (rolling window of 10)."""
        correct = predicted_action == actual_action
        if player_id not in self._history:
            self._history[player_id] = deque(maxlen=self._WINDOW)
        self._history[player_id].append(correct)
