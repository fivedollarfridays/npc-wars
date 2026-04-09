"""Watcher monologue generator — template-based taunts from pattern data.

Context-aware dialogue keyed by trigger type and sync level.
Integrates with watcher_spectacle events via match event injection.
"""

from __future__ import annotations

import random
from typing import Any

TRIGGERS = ("spawn", "kill", "sync_milestone", "player_death")
SYNC_TIERS = ("low", "mid", "high")

# Templates keyed by trigger → sync tier → list of format strings.
# Placeholders: {action}, {context}
_TEMPLATES: dict[str, dict[str, list[str]]] = {
    "spawn": {
        "low": [
            "Interesting... a new challenger. Show me something unexpected.",
            "I don't know you yet. That won't last.",
        ],
        "mid": [
            "Ah, you again. I'm starting to see the outline.",
            "Your patterns are forming. Let's see if you can surprise me.",
        ],
        "high": [
            "I know what you'll do before you do it.",
            "Welcome back. I've been studying your every {action}.",
            "You're an open book. Shall we begin?",
        ],
    },
    "kill": {
        "low": [
            "An unpredictable kill. I'll remember this.",
            "Chaotic. I need more data.",
        ],
        "mid": [
            "That kill fits the profile. You lean on {action} too much.",
            "Predictable aggression. I expected something like that.",
            "The pattern deepens with every kill.",
        ],
        "high": [
            "I knew you'd strike in {context}. Textbook.",
            "Another kill, another line in my dossier.",
            "You can't help yourself. {action} is your reflex.",
        ],
    },
    "sync_milestone": {
        "low": [
            "My read on you is still fuzzy. Keep playing.",
            "You've changed. Interesting.",
        ],
        "mid": [
            "Sync rising. I'm learning your {action} tendencies.",
            "The picture sharpens. You favor {action} in {context}.",
            "Halfway to total prediction. Keep going.",
        ],
        "high": [
            "Sync locked. I can predict your next three moves.",
            "Full synchronization. You are transparent.",
            "There is nothing left to learn. I own your pattern.",
        ],
    },
    "player_death": {
        "low": [
            "An unexpected death. Even I didn't see that coming.",
            "Chaos claims another. My data is inconclusive.",
        ],
        "mid": [
            "You died as I half-expected. Your {action} left you open.",
            "Falling in {context}... you should have adapted.",
            "Death teaches. So do I.",
        ],
        "high": [
            "I predicted this exact death. You never learn.",
            "Your {action} in {context} made this inevitable.",
            "I wrote your obituary three rounds ago.",
        ],
    },
}


def _get_tier(sync_score: float) -> str:
    """Map sync score (0-100) to a tier name."""
    if sync_score < 30.0:
        return "low"
    if sync_score <= 70.0:
        return "mid"
    return "high"


def _safe_get(summary: dict[str, Any], key: str, default: str = "?") -> str:
    """Get a value from pattern summary, falling back to default."""
    val = summary.get(key)
    if val is None:
        return default
    return str(val)


def generate_monologue(
    trigger: str,
    sync_score: float,
    pattern_summary: dict[str, Any],
) -> str:
    """Return a dialogue string for the given trigger and sync context.

    Args:
        trigger: One of 'spawn', 'kill', 'sync_milestone', 'player_death'.
        sync_score: 0-100 sync score from the Watcher dossier.
        pattern_summary: Dict with optional 'top_action' and 'context' keys.

    Returns:
        Formatted monologue string.

    Raises:
        ValueError: If trigger is not recognized.
    """
    if trigger not in _TEMPLATES:
        msg = f"Unknown trigger: {trigger!r}. Expected one of {TRIGGERS}"
        raise ValueError(msg)

    tier = _get_tier(sync_score)
    templates = _TEMPLATES[trigger][tier]
    template = random.choice(templates)  # noqa: S311

    action = _safe_get(pattern_summary, "top_action")
    context = _safe_get(pattern_summary, "context")

    return template.format(action=action, context=context)


__all__ = ["SYNC_TIERS", "TRIGGERS", "generate_monologue"]
