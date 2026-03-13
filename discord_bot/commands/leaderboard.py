"""Discord /leaderboard command -- bot rankings with pagination and sort options."""

import discord
from discord import app_commands
from typing import Any

__all__ = ["build_leaderboard_embed", "leaderboard_callback", "register_commands"]

PAGE_SIZE = 10


def build_leaderboard_embed(
    rankings: list[dict[str, Any]], page: int = 1, sort_by: str = "wins",
) -> discord.Embed:
    """Build a Discord embed showing ranked bots with pagination."""
    total_pages = max(1, (len(rankings) + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(1, min(page, total_pages))
    start = (page - 1) * PAGE_SIZE
    page_slice = rankings[start:start + PAGE_SIZE]

    if not page_slice:
        embed = discord.Embed(
            title="\U0001f3c6 Leaderboard",
            description="No data yet.",
            color=discord.Color.blue(),
        )
        embed.set_footer(text="Page 1/1")
        return embed

    lines = []
    for i, entry in enumerate(page_slice, start=start + 1):
        emoji = entry["emoji"]
        wins = entry.get("wins", 0)
        kills = entry.get("kills", 0)
        lines.append(f"{i}. {emoji} \u2014 {wins}W / {kills}K")

    embed = discord.Embed(
        title=f"\U0001f3c6 Leaderboard (by {sort_by})",
        description="\n".join(lines),
        color=discord.Color.blue(),
    )
    embed.set_footer(text=f"Page {page}/{total_pages}")
    return embed


async def leaderboard_callback(
    interaction: discord.Interaction,
    results_dir: str,
    sort_by: str = "wins",
    page: int = 1,
    match_data_list: list[dict[str, Any]] | None = None,
) -> None:
    """Handle the /leaderboard command interaction."""
    from data.match_history import list_matches, get_match
    from data.leaderboard import aggregate_stats, get_rankings

    if match_data_list is None:
        index = list_matches(results_dir)
        match_data_list = [
            m for entry in index
            if (m := get_match(results_dir, entry["match_id"])) is not None
        ]

    if not match_data_list:
        await interaction.response.send_message(
            "\u274c No match data available.", ephemeral=True,
        )
        return

    stats = aggregate_stats(match_data_list)
    rankings = get_rankings(stats, sort_by=sort_by)
    embed = build_leaderboard_embed(rankings, page=page, sort_by=sort_by)
    await interaction.response.send_message(embed=embed)


def register_commands(
    tree: app_commands.CommandTree, guild: discord.Object, results_dir: str,
) -> None:
    """Register the /leaderboard slash command on the command tree."""
    sort_choices = [
        app_commands.Choice(name=s, value=s)
        for s in ["wins", "kills", "win_rate", "avg_placement"]
    ]

    @tree.command(
        name="leaderboard", description="Show bot rankings", guild=guild,
    )
    @app_commands.describe(sort_by="Sort by (default: wins)", page="Page number")
    @app_commands.choices(sort_by=sort_choices)
    async def leaderboard(
        interaction: discord.Interaction,
        sort_by: str = "wins",
        page: int = 1,
    ) -> None:
        await leaderboard_callback(
            interaction, results_dir, sort_by=sort_by, page=page,
        )
