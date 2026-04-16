"""Season management slash commands: /season create, standings, schedule."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

import discord
from discord import app_commands

from data.seasons import create_season as db_create_season, get_standings
from discord_bot.commands.season_helpers import (
    check_season_finale,
    format_season_created,
    format_season_standings,
    format_weekly_summary,
    record_match_to_season,
)
from discord_bot.embeds import to_embed
from discord_bot.formatters import COLOR_BLUE

__all__ = [
    "format_season_created",
    "format_season_standings",
    "format_weekly_summary",
    "check_season_finale",
    "record_match_to_season",
    "register_commands",
]

_DEFAULT_KS_SCORING: dict[str, Any] = {
    "type": "kill_switch",
    "kill_points": 3,
    "placement_points": {1: 10, 2: 7, 3: 5, 4: 3},
}

_DEFAULT_CC_SCORING: dict[str, Any] = {
    "type": "code_circuit",
    "position_points": {
        1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1,
    },
}


def _get_scoring(game: str) -> dict[str, Any]:
    if game == "code_circuit":
        return dict(_DEFAULT_CC_SCORING)
    return dict(_DEFAULT_KS_SCORING)


async def _handle_create(
    interaction: discord.Interaction, conn: sqlite3.Connection,
    name: str, game: str, total_rounds: int,
) -> None:
    scoring = _get_scoring(game)
    config = {"total_rounds": total_rounds, "game": game}
    sid = db_create_season(conn, name, config, scoring)
    embed = to_embed(format_season_created(name, sid, game))
    await interaction.response.send_message(embed=embed)


async def _handle_standings(
    interaction: discord.Interaction, conn: sqlite3.Connection,
    season_id: int,
) -> None:
    row = conn.execute(
        "SELECT name FROM seasons WHERE id = ?", (season_id,),
    ).fetchone()
    if row is None:
        await interaction.response.send_message(
            f"Season #{season_id} not found.", ephemeral=True,
        )
        return
    standings = get_standings(season_id, conn=conn)
    embed = to_embed(format_season_standings(row["name"], standings))
    await interaction.response.send_message(embed=embed)


async def _handle_schedule(
    interaction: discord.Interaction, conn: sqlite3.Connection,
    season_id: int,
) -> None:
    row = conn.execute(
        "SELECT name, config_json FROM seasons WHERE id = ?", (season_id,),
    ).fetchone()
    if row is None:
        await interaction.response.send_message(
            f"Season #{season_id} not found.", ephemeral=True,
        )
        return
    config = json.loads(row["config_json"])
    total = config.get("total_rounds", "unlimited")
    count = conn.execute(
        "SELECT COUNT(*) as cnt FROM season_results WHERE season_id = ?",
        (season_id,),
    ).fetchone()["cnt"]
    is_finale = check_season_finale(season_id, conn=conn)
    status = "COMPLETE" if is_finale else "In Progress"
    embed = to_embed({
        "title": f"\U0001f4c5 {row['name']} \u2014 Schedule",
        "description": f"Status: **{status}**",
        "color": COLOR_BLUE,
        "fields": [
            {"name": "Total Rounds", "value": str(total), "inline": True},
            {"name": "Results Recorded", "value": str(count), "inline": True},
        ],
    })
    await interaction.response.send_message(embed=embed)


def register_commands(
    tree: app_commands.CommandTree,
    guild: discord.Object,
    conn: sqlite3.Connection,
) -> None:
    """Register /season command group on the tree."""
    group = app_commands.Group(
        name="season", description="Season management commands",
    )

    @group.command(name="create", description="Create a new season")
    @app_commands.describe(
        name="Season name",
        game="Game type (kill_switch or code_circuit)",
        total_rounds="Number of rounds in the season",
    )
    async def season_create(
        interaction: discord.Interaction,
        name: str, game: str = "kill_switch", total_rounds: int = 10,
    ) -> None:
        await _handle_create(interaction, conn, name, game, total_rounds)

    @group.command(name="standings", description="Show season standings")
    @app_commands.describe(season_id="Season ID to show standings for")
    async def season_standings(
        interaction: discord.Interaction, season_id: int,
    ) -> None:
        await _handle_standings(interaction, conn, season_id)

    @group.command(name="schedule", description="Show season schedule")
    @app_commands.describe(season_id="Season ID")
    async def season_schedule(
        interaction: discord.Interaction, season_id: int,
    ) -> None:
        await _handle_schedule(interaction, conn, season_id)

    tree.add_command(group, guild=guild)
