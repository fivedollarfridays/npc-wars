"""Discord /results command — show match results as an embed."""

import discord
from discord import app_commands
from typing import Any

from data.match_history import get_latest_match, get_match

__all__ = ["build_results_embed", "results_callback", "register_commands"]


def build_results_embed(match_data: dict[str, Any]) -> discord.Embed:
    """Build a Discord embed showing match results with winner and placements."""
    winner = match_data["winner"]
    duration = match_data["duration_rounds"]
    match_id = match_data["match_id"]
    eliminations: list[dict[str, Any]] = match_data.get("eliminations", [])

    embed = discord.Embed(
        title=f"\U0001f4ca Match #{match_id} Results",
        description=f"\U0001f3c6 Winner: **{winner}**",
        color=discord.Color.gold(),
    )
    embed.add_field(name="Duration", value=f"{duration} rounds", inline=True)

    # Placements: winner first, then reverse elimination order
    elim_emojis = [e["emoji"] for e in eliminations]
    ordered = [winner] + [e for e in reversed(elim_emojis) if e != winner]
    lines = [f"{i + 1}. {emoji}" for i, emoji in enumerate(ordered)]
    embed.add_field(name="Placements", value="\n".join(lines) or "\u2014", inline=False)

    return embed


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
