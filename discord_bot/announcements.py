"""Match announcement embeds and send helpers for NPC Wars."""

import discord
from typing import Any

from discord_bot.embeds import to_embed
from discord_bot.formatters import format_match_start, format_match_end

__all__ = [
    "build_match_start_embed",
    "build_match_end_embed",
    "announce_match_start",
    "announce_match_end",
]


def build_match_start_embed(
    match_id: int, players: list[dict[str, Any]], seed: int | None,
) -> discord.Embed:
    """Build embed for match start announcement."""
    return to_embed(format_match_start(match_id, players, seed))


def build_match_end_embed(match_data: dict[str, Any]) -> discord.Embed:
    """Build embed for match end announcement."""
    return to_embed(format_match_end(match_data))


async def announce_match_start(
    channel: discord.TextChannel,
    match_id: int,
    players: list[dict[str, Any]],
    seed: int | None,
) -> None:
    """Send a match-start embed to the given channel."""
    embed = build_match_start_embed(match_id, players, seed)
    await channel.send(embed=embed)


async def announce_match_end(
    channel: discord.TextChannel, match_data: dict[str, Any],
) -> None:
    """Send a match-end embed to the given channel."""
    embed = build_match_end_embed(match_data)
    await channel.send(embed=embed)
