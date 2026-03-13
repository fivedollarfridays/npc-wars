"""Slash commands for emoji claims: /claim, /unclaim, /roster."""

from typing import Any, Callable

import discord
from discord import app_commands

from data.emoji_claims import claim_emoji, unclaim_emoji, get_claims, save_claims
from discord_bot.embeds import to_embed
from discord_bot.formatters import format_claim_response, format_unclaim_response, format_roster


def _sync_state(state: dict, new_state: dict) -> None:
    """Sync state dict in-place: add new keys, remove deleted keys.

    Note: safe from concurrency issues because asyncio is single-threaded and
    claim_emoji/unclaim_emoji are synchronous — no await between read and write.
    """
    for key in list(state.keys()):
        if key not in new_state:
            del state[key]
    state.update(new_state)


async def _mutate_and_respond(
    interaction: discord.Interaction,
    emoji: str,
    state: dict,
    mutate_fn: Callable[[dict, str, str], tuple[dict, bool, str]],
    format_fn: Callable[[str, bool, str], dict[str, Any]],
    claims_path: str | None = None,
) -> None:
    """Apply a claim mutation, persist if successful, and send formatted response."""
    user_id = str(interaction.user.id)
    new_state, ok, reason = mutate_fn(state, user_id, emoji)
    if ok:
        _sync_state(state, new_state)
        if claims_path is not None:
            save_claims(state, claims_path)
    embed = to_embed(format_fn(emoji, ok, reason))
    await interaction.response.send_message(embed=embed)


async def claim_callback(
    interaction: discord.Interaction,
    emoji: str,
    state: dict,
    claims_path: str | None = None,
) -> None:
    """Claim an emoji as the user's bot identifier."""
    await _mutate_and_respond(
        interaction, emoji, state, claim_emoji, format_claim_response, claims_path,
    )


async def unclaim_callback(
    interaction: discord.Interaction,
    emoji: str,
    state: dict,
    claims_path: str | None = None,
) -> None:
    """Release an emoji claim."""
    await _mutate_and_respond(
        interaction, emoji, state, unclaim_emoji, format_unclaim_response, claims_path,
    )


async def roster_callback(
    interaction: discord.Interaction, state: dict
) -> None:
    """Show all claimed emojis."""
    embed = to_embed(format_roster(get_claims(state)))
    await interaction.response.send_message(embed=embed)


def register_commands(
    tree: app_commands.CommandTree,
    guild: discord.Object,
    state: dict,
    claims_path: str | None = None,
) -> None:
    """Register /claim, /unclaim, /roster on the command tree."""

    @tree.command(
        name="claim",
        description="Claim an emoji as your bot identifier",
        guild=guild,
    )
    @app_commands.describe(emoji="The emoji to claim")
    @app_commands.checks.cooldown(1, 5.0)
    async def claim(interaction: discord.Interaction, emoji: str) -> None:
        await claim_callback(interaction, emoji, state, claims_path=claims_path)

    @tree.command(
        name="unclaim",
        description="Release an emoji claim",
        guild=guild,
    )
    @app_commands.describe(emoji="The emoji to release")
    @app_commands.checks.cooldown(1, 5.0)
    async def unclaim(interaction: discord.Interaction, emoji: str) -> None:
        await unclaim_callback(interaction, emoji, state, claims_path=claims_path)

    @tree.command(
        name="roster",
        description="Show all claimed emojis",
        guild=guild,
    )
    async def roster(interaction: discord.Interaction) -> None:
        await roster_callback(interaction, state)
