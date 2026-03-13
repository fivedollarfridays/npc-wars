"""Discord /results command — show match results as an embed."""

import discord
from discord import app_commands
from typing import Any

from data.match_history import get_latest_match, get_match
from discord_bot.embeds import to_embed
from discord_bot.formatters import format_results

__all__ = ["build_results_embed", "results_callback", "register_commands"]


def build_results_embed(match_data: dict[str, Any]) -> discord.Embed:
    """Build a Discord embed showing match results with winner and placements."""
    return to_embed(format_results(match_data))


async def results_callback(
    interaction: discord.Interaction,
    results_dir: str,
    match_id: int | None = None,
) -> None:
    """Handle the /results command interaction."""
    if match_id is not None:
        match_data = get_match(results_dir, match_id)
        if match_data is None:
            await interaction.response.send_message(
                "\u274c Match not found.", ephemeral=True,
            )
            return
    else:
        match_data = get_latest_match(results_dir)
        if match_data is None:
            await interaction.response.send_message(
                "\u274c No matches found.", ephemeral=True,
            )
            return

    embed = build_results_embed(match_data)
    await interaction.response.send_message(embed=embed)


def register_commands(
    tree: app_commands.CommandTree,
    guild: discord.Object,
    results_dir: str,
) -> None:
    """Register the /results slash command on the command tree."""

    @tree.command(name="results", description="Show match results", guild=guild)
    @app_commands.describe(match_id="Match ID (optional, defaults to latest)")
    async def results(
        interaction: discord.Interaction, match_id: int | None = None,
    ) -> None:
        await results_callback(interaction, results_dir, match_id)
