"""Slash commands for emoji claims: /claim, /unclaim, /roster."""

import discord
from discord import app_commands

from data.emoji_claims import claim_emoji, unclaim_emoji, get_claims


async def claim_callback(
    interaction: discord.Interaction, emoji: str, state: dict
) -> None:
    """Claim an emoji as the user's bot identifier."""
    user_id = str(interaction.user.id)
    new_state, ok, reason = claim_emoji(state, user_id, emoji)
    if ok:
        state.update(new_state)
        # Remove keys no longer in new_state (not needed for claim, but safe)
        embed = discord.Embed(
            title="Emoji Claimed",
            description=f"{emoji} is now yours!",
            color=discord.Color.green(),
        )
    else:
        embed = discord.Embed(
            title="Claim Failed",
            description=reason,
            color=discord.Color.red(),
        )
    await interaction.response.send_message(embed=embed)


async def unclaim_callback(
    interaction: discord.Interaction, emoji: str, state: dict
) -> None:
    """Release an emoji claim."""
    user_id = str(interaction.user.id)
    new_state, ok, reason = unclaim_emoji(state, user_id, emoji)
    if ok:
        # Sync state dict in-place: remove unclaimed key
        for key in list(state.keys()):
            if key not in new_state:
                del state[key]
        state.update(new_state)
        embed = discord.Embed(
            title="Emoji Released",
            description=f"{emoji} unclaimed.",
            color=discord.Color.green(),
        )
    else:
        embed = discord.Embed(
            title="Unclaim Failed",
            description=reason,
            color=discord.Color.red(),
        )
    await interaction.response.send_message(embed=embed)


async def roster_callback(
    interaction: discord.Interaction, state: dict
) -> None:
    """Show all claimed emojis."""
    claims = get_claims(state)
    if not claims:
        embed = discord.Embed(
            title="Roster",
            description="No emojis claimed yet.",
            color=discord.Color.blue(),
        )
    else:
        lines = [f"{emoji} -> <@{uid}>" for emoji, uid in claims.items()]
        embed = discord.Embed(
            title="Roster",
            description="\n".join(lines),
            color=discord.Color.blue(),
        )
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
