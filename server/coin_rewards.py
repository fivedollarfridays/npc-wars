"""Award coins to players after match completion."""

from __future__ import annotations

import sqlite3
from typing import Any

from server.cosmetic_db import award_coins
from server.cosmetics import MATCH_COIN_REWARD, WIN_COIN_BONUS


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
