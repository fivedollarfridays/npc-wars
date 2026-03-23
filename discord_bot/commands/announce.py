"""Post match results to a Discord channel."""

import discord
from typing import Any

__all__ = ["build_match_embed", "announce_match"]


def build_match_embed(
    match_data: dict[str, Any], server_url: str = "",
) -> discord.Embed:
    """Build a Discord embed for match results."""
    winner = match_data.get("winner", "none")
    duration = match_data.get("duration_rounds", 0)
    match_id = match_data.get("match_id", 0)
    stats = match_data.get("stats", {})

    # Resolve winner name from players list
    players = match_data.get("players", [])
    winner_name = next(
        (p["name"] for p in players if p["emoji"] == winner), winner,
    )

    embed = discord.Embed(
        title=f"Match #{match_id} Complete",
        description=f"**{winner_name}** wins in {duration} rounds!",
        color=discord.Color.gold(),
    )

    # Kill feed summary (max 5 entries)
    elims = match_data.get("eliminations", [])
    feed = "\n".join(
        f"R{e['round']}: {e.get('killed_by', '?')} -> {e['emoji']}"
        for e in elims[:5]
    )
    if feed:
        embed.add_field(name="Kill Feed", value=feed, inline=False)

    # Top stats
    if stats:
        top_kills = max(stats.items(), key=lambda x: x[1].get("kills", 0))
        top_dmg = max(
            stats.items(), key=lambda x: x[1].get("damage_dealt", 0),
        )
        embed.add_field(
            name="Most Kills",
            value=f"{top_kills[0]} ({top_kills[1]['kills']})",
            inline=True,
        )
        embed.add_field(
            name="Most Damage",
            value=f"{top_dmg[0]} ({top_dmg[1]['damage_dealt']})",
            inline=True,
        )

    # Replay link
    if server_url:
        embed.add_field(
            name="Watch Replay",
            value=f"[View Match]({server_url}/m/{match_id})",
            inline=False,
        )

    return embed


async def announce_match(
    bot: discord.Client,
    channel_id: int,
    match_data: dict[str, Any],
    server_url: str = "",
) -> None:
    """Post match results to a Discord channel."""
    channel = bot.get_channel(channel_id)
    if not channel:
        return
    embed = build_match_embed(match_data, server_url)
    await channel.send(embed=embed)
