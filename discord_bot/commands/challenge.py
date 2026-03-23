"""Challenge another player to a 1v1 match."""

import discord
from discord import app_commands

__all__ = ["challenge_callback", "register_commands"]


async def challenge_callback(
    interaction: discord.Interaction, opponent: discord.Member,
) -> None:
    """Handle the /challenge command interaction."""
    embed = discord.Embed(
        title="Challenge Issued!",
        description=(
            f"{interaction.user.mention} challenges {opponent.mention}!\n\n"
            f"Both players: upload your bot within 5 minutes.\n"
            f"`agentgrounds wars upload my_bot.py`"
        ),
        color=discord.Color.red(),
    )
    await interaction.response.send_message(embed=embed)


def register_commands(
    tree: app_commands.CommandTree, guild: discord.Object,
) -> None:
    """Register the /challenge slash command on the command tree."""

    @tree.command(
        name="challenge",
        description="Challenge a player to a 1v1",
        guild=guild,
    )
    async def challenge(
        interaction: discord.Interaction, opponent: discord.Member,
    ) -> None:
        await challenge_callback(interaction, opponent)
