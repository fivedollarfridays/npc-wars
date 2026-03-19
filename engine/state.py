"""Build the state dict that each bot's decide() function receives."""

from typing import Any

from engine.combat import Bot
from engine.combat_rolls import calculate_hit_probability

__all__ = ["build_state"]


def _compute_incoming_threats(
    bot: Bot, alive_enemies: list[Bot],
) -> list[dict[str, Any]]:
    """Compute incoming threat from each alive enemy, sorted by danger."""
    threats = []
    for enemy in alive_enemies:
        prob = calculate_hit_probability(enemy.derived, bot.derived)
        threats.append({
            "emoji": enemy.emoji,
            "hit_chance": prob["hit_chance"],
            "expected_damage": prob["expected_damage"],
        })
    threats.sort(key=lambda t: t["expected_damage"], reverse=True)
    return threats


def build_state(
    bot: Bot, all_bots: list[Bot], round_num: int, grid_size: int,
    storm_border: int, bumps_last_round: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build the state dict for a specific bot."""
    alive_enemies = [b for b in all_bots if b.alive and b.emoji != bot.emoji]

    hit_chance_vs: dict[str, dict[str, float]] = {}
    for enemy in alive_enemies:
        hit_chance_vs[enemy.emoji] = calculate_hit_probability(
            bot.derived, enemy.derived,
        )

    # Incoming threats: how dangerous each enemy is TO this bot
    incoming_threat = _compute_incoming_threats(bot, alive_enemies)

    me_dict = bot.to_self_dict()
    me_dict["hit_chance_vs"] = hit_chance_vs
    me_dict["incoming_threat"] = incoming_threat

    return {
        "me": me_dict,
        "enemies": [e.to_enemy_dict() for e in alive_enemies],
        "round": round_num,
        "grid_size": grid_size,
        "storm_border": storm_border,
        "bumps_last_round": bumps_last_round or [],
    }
