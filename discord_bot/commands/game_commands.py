"""Game command groups: /killswitch and /circuit slash commands."""

from __future__ import annotations

import logging
import os

import discord
from discord import app_commands

from discord_bot.embeds import to_embed
from discord_bot.formatters import COLOR_GREEN, COLOR_ORANGE

__all__ = ["register_commands"]

log = logging.getLogger(__name__)


async def _handle_ks_play(
    interaction: discord.Interaction,
    bots_dir: str,
    results_dir: str,
    seed: int | None,
) -> None:
    """Run a Kill Switch match and report the result."""
    await interaction.response.defer()
    try:
        from engine.game import run_match
        from engine.match_writer import write_match

        bot_files = _discover_bots(bots_dir)
        if len(bot_files) < 2:
            await interaction.followup.send("Need at least 2 bots in the bots directory.")
            return

        match_data = run_match(bot_files, seed=seed)
        path = write_match(match_data, results_dir)
        winner = match_data.get("winner", "???")
        duration = match_data.get("duration_rounds", 0)
        embed = to_embed({
            "title": "\u2694\ufe0f Kill Switch Match Complete",
            "description": f"\U0001f3c6 Winner: **{winner}** in {duration} rounds",
            "color": COLOR_ORANGE,
            "fields": [
                {"name": "Result saved", "value": os.path.basename(path), "inline": True},
            ],
        })
        await interaction.followup.send(embed=embed)
    except Exception:
        log.exception("Kill Switch play failed")
        await interaction.followup.send("Match failed — check bot files and try again.")


async def _handle_cc_race(
    interaction: discord.Interaction,
    results_dir: str,
    laps: int,
    seed: int | None,
) -> None:
    """Run a Code Circuit race and report the result."""
    await interaction.response.defer()
    try:
        from engine.circuit import run_race

        race_data = run_race(car_configs=None, laps=laps, seed=seed)
        winner = race_data.get("winner", "???")
        embed = to_embed({
            "title": "\U0001f3ce\ufe0f Code Circuit Race Complete",
            "description": f"\U0001f3c6 Winner: **{winner}** ({laps} laps)",
            "color": COLOR_GREEN,
            "fields": [],
        })
        await interaction.followup.send(embed=embed)
    except Exception:
        log.exception("Code Circuit race failed")
        await interaction.followup.send("Race failed — check configuration and try again.")


def _discover_bots(bots_dir: str) -> list[str]:
    """Find .py bot files in the bots directory."""
    if not os.path.isdir(bots_dir):
        return []
    return [
        os.path.join(bots_dir, f)
        for f in sorted(os.listdir(bots_dir))
        if f.endswith(".py") and not f.startswith("_")
    ]


def register_commands(
    tree: app_commands.CommandTree,
    guild: discord.Object,
    bots_dir: str = "bots",
    results_dir: str = "results",
) -> None:
    """Register /killswitch and /circuit command groups."""
    ks_group = app_commands.Group(
        name="killswitch", description="Kill Switch battle royale commands",
    )

    @ks_group.command(name="play", description="Run a Kill Switch match")
    @app_commands.describe(seed="Random seed for reproducible matches")
    async def ks_play(interaction: discord.Interaction, seed: int | None = None) -> None:
        await _handle_ks_play(interaction, bots_dir, results_dir, seed)

    cc_group = app_commands.Group(
        name="circuit", description="Code Circuit racing commands",
    )

    @cc_group.command(name="race", description="Run a Code Circuit race")
    @app_commands.describe(
        laps="Number of laps (default 5)",
        seed="Random seed for reproducible races",
    )
    async def cc_race(
        interaction: discord.Interaction, laps: int = 5, seed: int | None = None,
    ) -> None:
        await _handle_cc_race(interaction, results_dir, laps, seed)

    tree.add_command(ks_group, guild=guild)
    tree.add_command(cc_group, guild=guild)
