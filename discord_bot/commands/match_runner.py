"""Slash command /run_match: trigger a match from Discord."""

import asyncio
import logging

import discord
from discord import app_commands

from data.match_history import next_match_id
from engine.game import run_match
from engine.loader import load_bots
from engine.match_writer import write_match

__all__ = ["run_match_callback", "register_commands"]

log = logging.getLogger(__name__)

COOLDOWN_SECONDS = 60.0


async def run_match_callback(
    interaction: discord.Interaction,
    *,
    bots_dir: str,
    results_dir: str,
    seed: int | None = None,
) -> None:
    """Load bots, run a match in a thread pool, save and announce result."""
    await interaction.response.defer()

    bot_configs = await asyncio.to_thread(load_bots, bots_dir)
    if len(bot_configs) < 2:
        await interaction.followup.send(
            "Not enough bots to run a match (need at least 2).", ephemeral=True,
        )
        return

    match_id = next_match_id(results_dir)
    match_data = await asyncio.to_thread(
        run_match, bot_configs, match_id=match_id, seed=seed,
    )

    write_match(match_data, results_dir)

    winner = match_data.get("winner", "unknown")
    rounds = match_data.get("duration_rounds", "?")
    await interaction.followup.send(
        f"Match #{match_id} complete! Winner: {winner} ({rounds} rounds)",
    )


def register_commands(
    tree: app_commands.CommandTree,
    guild: discord.Object,
    bots_dir: str,
    results_dir: str,
) -> None:
    """Register /run_match on the command tree."""

    @tree.command(
        name="run_match",
        description="Trigger a bot match",
        guild=guild,
    )
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(seed="Optional RNG seed for reproducibility")
    @app_commands.checks.cooldown(1, COOLDOWN_SECONDS)
    async def _run_match(
        interaction: discord.Interaction, seed: int | None = None,
    ) -> None:
        await run_match_callback(
            interaction, bots_dir=bots_dir, results_dir=results_dir, seed=seed,
        )
