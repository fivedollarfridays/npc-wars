"""Build the state dict that each bot's decide() function receives."""

from typing import Any

from engine.combat import Bot

__all__ = ["build_state"]


def build_state(bot: Bot, all_bots: list[Bot], round_num: int, grid_size: int, storm_border: int) -> dict[str, Any]:
    """Build the state dict for a specific bot."""
    enemies = [
        b.to_enemy_dict()
        for b in all_bots
        if b.alive and b.emoji != bot.emoji
    ]

    return {
        "me": bot.to_self_dict(),
        "enemies": enemies,
        "round": round_num,
        "grid_size": grid_size,
        "storm_border": storm_border,
    }
