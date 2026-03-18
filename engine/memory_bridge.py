"""Bridge between match engine and bot memory persistence.

Thin helpers called by game.py to load memories before a match
and save them after.  Keeps game.py under its line-count limit.
"""

from __future__ import annotations

import logging
from typing import Any

from data.bot_memory import MemoryLimitExceeded, load_all_memories, save_bot_memory

__all__ = ["inject_memories", "persist_memories"]

_log = logging.getLogger(__name__)


def inject_memories(
    bot_configs: list[dict[str, Any]], memory_dir: str,
) -> None:
    """Load memories from *memory_dir* and attach to each bot config."""
    memories = load_all_memories(memory_dir)
    for cfg in bot_configs:
        cfg["memory"] = memories.get(cfg["emoji"], {})


def persist_memories(
    bots: list[Any], winner_emoji: str, memory_dir: str,
) -> None:
    """Save each bot's memory to *memory_dir* after a match.

    Sets ``_last_match_won`` on each bot's memory before saving.
    Errors are logged but never bubble up — a save failure must not
    crash the match result.
    """
    for bot in bots:
        bot.memory["_last_match_won"] = (bot.emoji == winner_emoji)
        try:
            save_bot_memory(bot.emoji, bot.memory, memory_dir)
        except MemoryLimitExceeded:
            _log.warning(
                "Memory limit exceeded for %s — memory not saved", bot.emoji,
            )
        except Exception:
            _log.warning("Failed to save memory for %s", bot.emoji, exc_info=True)
