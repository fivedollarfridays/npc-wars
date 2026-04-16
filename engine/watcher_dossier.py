"""Watcher dossier — human-readable pattern intelligence report.

Surfaces the Watcher's PatternTable as a dossier showing per-context
predictions, sync score, and predictability metrics.
"""

from __future__ import annotations

import math
from typing import Any

__all__ = ["build_dossier", "format_dossier_text"]

from server.rival_patterns import (
    compact_for_embed,
    get_pattern_summary,
    load_player_patterns,
)
# Action → best counter action
_COUNTERS: dict[str, str] = {
    "rest": "attack",
    "attack": "move",
    "move": "attack",
    "ranged": "move",
    "trap": "move",
    "use_ability": "attack",
}

_SYNC_SCALE = 30  # observations needed for ~95% sync


def build_dossier(
    player_id: str,
    patterns_dir: str,
    watcher_stats_path: str,
) -> dict[str, Any]:
    """Build a dossier dict for *player_id* from pattern and stats data."""
    table = load_player_patterns(player_id, base_dir=patterns_dir)
    summary = get_pattern_summary(table, player_id)
    compact = compact_for_embed(summary)

    total_obs = _total_observations(table, player_id)
    sync_score = _compute_sync_score(total_obs)
    predictability = _compute_predictability(summary)

    predictions = _build_predictions(compact)

    dossier: dict[str, Any] = {
        "player_id": player_id,
        "sync_score": round(sync_score, 1),
        "predictability_change": round(predictability, 3),
        "predictions": predictions,
    }
    dossier["text_summary"] = format_dossier_text(dossier)
    return dossier


def format_dossier_text(dossier: dict[str, Any]) -> str:
    """Generate a human-readable text summary from a dossier dict."""
    pid = dossier["player_id"]
    sync = dossier["sync_score"]
    preds = dossier["predictions"]

    if not preds:
        return (
            f"Dossier: {pid}\n"
            f"The Watcher has not yet learned your patterns. Play more matches."
        )

    lines = [
        f"Dossier: {pid}",
        f"How well does the Watcher know you? {sync}%",
        "",
    ]
    for pred in preds:
        ctx = pred["context"]
        actions_str = ", ".join(
            f"{a['action']} ({a['probability']:.0%})" for a in pred["actions"]
        )
        lines.append(
            f"Context: {ctx} → Predicted action: {actions_str}. "
            f"Expected counter: {pred['counter']}"
        )

    predictability = dossier["predictability_change"]
    if predictability >= 0.7:
        lines.append("\nYou are highly predictable. Mix up your actions.")
    elif predictability <= 0.4:
        lines.append("\nYour behavior is hard to read. The Watcher is still learning.")

    return "\n".join(lines)


def _build_predictions(
    compact: dict[str, dict[str, float]],
) -> list[dict[str, Any]]:
    """Convert compact summary into prediction entries with counters."""
    predictions = []
    for ctx, actions in compact.items():
        sorted_actions = sorted(actions.items(), key=lambda x: x[1], reverse=True)
        action_list = [
            {"action": a, "probability": round(p, 3)} for a, p in sorted_actions
        ]
        top_action = sorted_actions[0][0] if sorted_actions else "rest"
        predictions.append({
            "context": ctx,
            "actions": action_list,
            "counter": _COUNTERS.get(top_action, "attack"),
        })
    return predictions


def _total_observations(table: Any, player_id: str) -> int:
    """Count total observations across all contexts for a player."""
    data = table.to_dict()
    player_data = data.get(player_id, {})
    return sum(
        int(count) for actions in player_data.values()
        for count in actions.values()
    )


def _compute_sync_score(total_obs: int) -> float:
    """Map observation count to a 0-100 sync score (exponential saturation)."""
    if total_obs <= 0:
        return 0.0
    return 100.0 * (1 - math.exp(-total_obs / _SYNC_SCALE))


def _compute_predictability(
    summary: dict[str, dict[str, float]],
) -> float:
    """Compute average max-probability across contexts (0-1 scale)."""
    if not summary:
        return 0.0
    max_probs = [max(actions.values()) for actions in summary.values() if actions]
    if not max_probs:
        return 0.0
    return sum(max_probs) / len(max_probs)
