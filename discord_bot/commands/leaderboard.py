"""Discord /leaderboard command -- bot rankings with pagination and sort options."""

import discord
from discord import app_commands
from typing import Any

from discord_bot.embeds import to_embed
from discord_bot.formatters import format_leaderboard

__all__ = ["build_leaderboard_embed", "leaderboard_callback", "register_commands"]


def build_leaderboard_embed(
    rankings: list[dict[str, Any]], page: int = 1, sort_by: str = "wins",
) -> discord.Embed:
    """Build a Discord embed showing ranked bots with pagination."""
    return to_embed(format_leaderboard(rankings, page=page, sort_by=sort_by))


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
