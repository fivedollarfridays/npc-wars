"""Award coins to players after match completion."""

from __future__ import annotations

import sqlite3
from typing import Any

from server.cosmetic_db import award_coins
from server.cosmetics import MATCH_COIN_REWARD, WIN_COIN_BONUS

RIVAL_TIER_CLEAR_COINS = 50
RIVAL_GRADUATION_COINS = 200


def award_rival_clear(
    conn: sqlite3.Connection,
    player_id: str,
    *,
    graduated: bool = False,
) -> None:
    """Award coins for rival tier clear and optional graduation."""
    award_coins(conn, player_id, RIVAL_TIER_CLEAR_COINS)
    if graduated:
        award_coins(conn, player_id, RIVAL_GRADUATION_COINS)


def award_match_coins(
    conn: sqlite3.Connection,
    match_data: dict[str, Any],
    bot_configs: list[dict[str, Any]],
) -> None:
    """Award participation + win bonus coins to human players."""
    winner_emoji = match_data.get("winner", "none")

    for cfg in bot_configs:
        player_id = cfg.get("player_id")
        if not player_id:
            continue  # skip fill bots

        award_coins(conn, player_id, MATCH_COIN_REWARD)

        if cfg.get("emoji") == winner_emoji:
            award_coins(conn, player_id, WIN_COIN_BONUS)
