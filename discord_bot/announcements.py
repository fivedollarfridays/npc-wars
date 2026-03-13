"""Match announcement embeds and send helpers for NPC Wars."""

import discord
from typing import Any

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
    embed = discord.Embed(
        title=f"\u2694\ufe0f Match #{match_id} \u2014 FIGHT!",
        description="The battle begins!",
        color=discord.Color.orange(),
    )
    roster = " ".join(p["emoji"] for p in players)
    embed.add_field(name="Players", value=roster or "none", inline=False)
    embed.add_field(name="Competitors", value=str(len(players)), inline=True)
    if seed is not None:
        embed.add_field(name="Seed", value=str(seed), inline=True)
    return embed


def build_match_end_embed(match_data: dict[str, Any]) -> discord.Embed:
    """Build embed for match end announcement."""
    winner = match_data["winner"]
    duration = match_data["duration_rounds"]
    eliminations: list[dict[str, Any]] = match_data.get("eliminations", [])

    embed = discord.Embed(
        title=f"\U0001f3c6 Match #{match_data['match_id']} Complete!",
        description=f"Winner: **{winner}**",
        color=discord.Color.gold(),
    )
    embed.add_field(name="Rounds", value=str(duration), inline=True)

    if eliminations:
        tail = eliminations[-3:]
        lines = [
            f"R{e['round']}: {e.get('killed_by', '?')} \u2192 {e['emoji']} ({e['cause']})"
            for e in tail
        ]
        embed.add_field(name="Final Kills", value="\n".join(lines), inline=False)
    return embed


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
