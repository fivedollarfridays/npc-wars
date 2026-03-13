"""Slash commands for emoji claims: /claim, /unclaim, /roster."""

import discord
from discord import app_commands

from data.emoji_claims import claim_emoji, unclaim_emoji, get_claims
from discord_bot.embeds import to_embed
from discord_bot.formatters import format_claim_response, format_unclaim_response


def _sync_state(state: dict, new_state: dict) -> None:
    """Sync state dict in-place: add new keys, remove deleted keys."""
    for key in list(state.keys()):
        if key not in new_state:
            del state[key]
    state.update(new_state)


async def claim_callback(
    interaction: discord.Interaction, emoji: str, state: dict
) -> None:
    """Claim an emoji as the user's bot identifier."""
    user_id = str(interaction.user.id)
    new_state, ok, reason = claim_emoji(state, user_id, emoji)
    if ok:
        _sync_state(state, new_state)
    embed = to_embed(format_claim_response(emoji, ok, reason))
    await interaction.response.send_message(embed=embed)


async def unclaim_callback(
    interaction: discord.Interaction, emoji: str, state: dict
) -> None:
    """Release an emoji claim."""
    user_id = str(interaction.user.id)
    new_state, ok, reason = unclaim_emoji(state, user_id, emoji)
    if ok:
        _sync_state(state, new_state)
    embed = to_embed(format_unclaim_response(emoji, ok, reason))
    await interaction.response.send_message(embed=embed)


async def roster_callback(
    interaction: discord.Interaction, state: dict
) -> None:
    """Show all claimed emojis."""
    claims = get_claims(state)
    if not claims:
        description = "No emojis claimed yet."
    else:
        description = "\n".join(f"{emoji} -> <@{uid}>" for emoji, uid in claims.items())
    embed = discord.Embed(title="Roster", description=description, color=discord.Color.blue())
    await interaction.response.send_message(embed=embed)


def register_commands(
    tree: app_commands.CommandTree, guild: discord.Object, state: dict
) -> None:
    """Register /claim, /unclaim, /roster on the command tree."""

    @tree.command(
        name="claim",
        description="Claim an emoji as your bot identifier",
        guild=guild,
    )
    @app_commands.describe(emoji="The emoji to claim")
    async def claim(interaction: discord.Interaction, emoji: str) -> None:
        await claim_callback(interaction, emoji, state)

    @tree.command(
        name="unclaim",
        description="Release an emoji claim",
        guild=guild,
    )
    @app_commands.describe(emoji="The emoji to release")
    async def unclaim(interaction: discord.Interaction, emoji: str) -> None:
        await unclaim_callback(interaction, emoji, state)

    @tree.command(
        name="roster",
        description="Show all claimed emojis",
        guild=guild,
    )
    async def roster(interaction: discord.Interaction) -> None:
        await roster_callback(interaction, state)
