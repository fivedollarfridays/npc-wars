"""Thin adapter: convert a formatter dict to a discord.Embed."""

import discord
from typing import Any


def to_embed(data: dict[str, Any]) -> discord.Embed:
    """Convert a plain formatter dict to a discord.Embed."""
    embed = discord.Embed(
        title=data.get("title"),
        description=data.get("description"),
        color=data.get("color"),
    )
    for field in data.get("fields", []):
        embed.add_field(**field)
    if data.get("footer"):
        embed.set_footer(text=data["footer"])
    return embed
