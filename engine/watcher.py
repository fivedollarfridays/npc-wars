"""The Watcher — adaptive AI boss bot for NPC Wars."""

from __future__ import annotations

from typing import Any

from engine.combat import Bot

WATCHER_EMOJI = "\U0001f346"
WATCHER_NAME = "The Watcher"
WATCHER_ACTIONS = ["attack", "dash", "defend", "move", "ranged_attack", "rest", "taunt"]

__all__ = ["WATCHER_EMOJI", "WATCHER_NAME", "WATCHER_ACTIONS", "WatcherBot"]


def _watcher_decide_placeholder(state: dict[str, Any]) -> tuple[str, ...]:
    """Placeholder decide function — always rests."""
    return ("rest",)


class WatcherBot(Bot):
    """The Watcher: a special boss bot with full action access.

    Attributes:
        is_watcher: Always True for Watcher instances.
        is_player_bot: Always False — the Watcher is an NPC boss.
    """

    is_watcher: bool = True
    is_player_bot: bool = False

    def __init__(self, *, x: int, y: int) -> None:
        super().__init__(
            name=WATCHER_NAME,
            emoji=WATCHER_EMOJI,
            bio="Observes. Adapts. Punishes.",
            author="system",
            decide_func=_watcher_decide_placeholder,
            x=x,
            y=y,
        )
        self.unlocked_actions = list(WATCHER_ACTIONS)

    def decide(self, state: dict[str, Any]) -> tuple[str, ...]:
        """Choose an action based on game state. Placeholder: always rests."""
        return ("rest",)
