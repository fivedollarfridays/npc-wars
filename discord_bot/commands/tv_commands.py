"""TV command group: /tv highlights <game>."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import discord
from discord import app_commands

from discord_bot.embeds import to_embed
from discord_bot.formatters import format_highlights

__all__ = ["register_commands"]

log = logging.getLogger(__name__)

_GAME_KEYS = {"kill_switch", "code_circuit"}


def _load_recent_matches(
    results_dir: str, game: str, limit: int = 5,
) -> list[dict[str, Any]]:
    """Load the most recent match JSON files for a given game."""
    if not os.path.isdir(results_dir):
        return []
    files = sorted(
        (f for f in os.listdir(results_dir) if f.endswith(".json")),
        reverse=True,
    )
    matches: list[dict[str, Any]] = []
    for fname in files:
        if len(matches) >= limit:
            break
        path = os.path.join(results_dir, fname)
        try:
            with open(path) as fh:
                data = json.load(fh)
            if data.get("game", "kill_switch") == game:
                matches.append(data)
        except (json.JSONDecodeError, OSError):
            continue
    return matches


def _collect_highlights(
    matches: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Extract highlights from matches, falling back to TV-enriched data."""
    all_highlights: list[dict[str, Any]] = []
    for match in matches:
        hl = match.get("highlights", [])
        all_highlights.extend(hl)
    return all_highlights


async def _handle_highlights(
    interaction: discord.Interaction,
    results_dir: str,
    game: str,
) -> None:
    """Show recent highlights for a game."""
    matches = _load_recent_matches(results_dir, game)
    highlights = _collect_highlights(matches)
    embed_data = format_highlights(game, highlights)
    embed = to_embed(embed_data)
    await interaction.response.send_message(embed=embed)


def register_commands(
    tree: app_commands.CommandTree,
    guild: discord.Object,
    results_dir: str = "results",
) -> None:
    """Register /tv command group."""
    tv_group = app_commands.Group(
        name="tv", description="Agent Grounds TV commands",
    )

    @tv_group.command(name="highlights", description="Show recent highlights")
    @app_commands.describe(game="Game: kill_switch or code_circuit")
    async def tv_highlights(
        interaction: discord.Interaction, game: str = "kill_switch",
    ) -> None:
        if game not in _GAME_KEYS:
            await interaction.response.send_message(
                f"Unknown game: {game!r}. Use kill_switch or code_circuit.",
                ephemeral=True,
            )
            return
        await _handle_highlights(interaction, results_dir, game)

    tree.add_command(tv_group, guild=guild)
