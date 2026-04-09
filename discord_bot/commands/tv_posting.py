"""Post TV episode videos and summaries to game-specific Discord channels."""

from __future__ import annotations

import logging
import os
from typing import Any

import discord

from discord_bot.embeds import to_embed
from discord_bot.formatters import (
    format_tv_main_message,
    format_tv_thread_stats,
    format_tv_thread_watcher,
)

__all__ = ["get_tv_channel_id", "post_match_tv"]

log = logging.getLogger(__name__)

_DISCORD_MAX_BYTES = 25 * 1024 * 1024

_CHANNEL_MAP = {
    "kill_switch": "ks_tv_channel_id",
    "code_circuit": "cc_tv_channel_id",
}


def get_tv_channel_id(game: str, config: dict[str, Any]) -> int | None:
    """Return the TV channel ID for a game type, or None if not configured."""
    key = _CHANNEL_MAP.get(game)
    if key is None:
        return None
    return config.get(key)


async def post_match_tv(
    bot: Any,
    episode: dict[str, Any],
    mp4_path: str,
    config: dict[str, Any],
) -> None:
    """Post video + embed to the game's TV channel, with threaded stats reply."""
    game = episode["metadata"]["game"]
    channel_id = get_tv_channel_id(game, config)
    if channel_id is None:
        log.warning("No TV channel configured for game=%s", game)
        return

    channel = bot.get_channel(channel_id)
    if channel is None:
        log.warning("TV channel %s not found", channel_id)
        return

    # Build main message embed
    main_embed = to_embed(format_tv_main_message(episode))

    # Check video size
    video_too_large = os.path.getsize(mp4_path) > _DISCORD_MAX_BYTES

    if video_too_large:
        main_embed.description += "\n\n*Video too large to attach (>25MB). Highlights above.*"
        main_msg = await channel.send(embed=main_embed)
    else:
        main_msg = await channel.send(
            embed=main_embed,
            file=discord.File(mp4_path),
        )

    # Create thread for detailed stats
    thread = await main_msg.create_thread(name="Match Details")

    # Post stats embed
    stats_embed = to_embed(format_tv_thread_stats(episode))
    await thread.send(embed=stats_embed)

    # Post watcher dossier for Kill Switch only
    if game == "kill_switch":
        dossiers = episode.get("watcher_dossiers", {})
        watcher_data = format_tv_thread_watcher(dossiers)
        if watcher_data is not None:
            watcher_embed = to_embed(watcher_data)
            await thread.send(embed=watcher_embed)
