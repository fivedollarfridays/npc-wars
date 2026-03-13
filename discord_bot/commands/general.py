"""General slash commands: /ping, /help, /status."""

import discord
from discord import app_commands


async def ping_callback(interaction: discord.Interaction) -> None:
    """Respond with pong."""
    await interaction.response.send_message("🏓 Pong!")


async def help_callback(interaction: discord.Interaction) -> None:
    """Show available commands."""
    embed = discord.Embed(
        title="NPC Wars Bot — Commands",
        description="Available slash commands: /ping, /help, /status",
        color=discord.Color.blue(),
    )
    embed.add_field(name="/ping", value="Check if the bot is alive", inline=False)
    embed.add_field(name="/help", value="Show this help message", inline=False)
    embed.add_field(name="/status", value="Show bot status", inline=False)
    await interaction.response.send_message(embed=embed)


async def status_callback(interaction: discord.Interaction) -> None:
    """Report bot status."""
    await interaction.response.send_message("NPC Wars bot is online ✅")


def register_commands(tree: app_commands.CommandTree, guild: discord.Object) -> None:
    """Register general slash commands on the command tree."""
    ping_cmd = app_commands.Command(
        name="ping",
        description="Check if the bot is alive",
        callback=ping_callback,
    )
    help_cmd = app_commands.Command(
        name="help",
        description="Show available commands",
        callback=help_callback,
    )
    status_cmd = app_commands.Command(
        name="status",
        description="Show bot status",
        callback=status_callback,
    )
    tree.add_command(ping_cmd, guild=guild)
    tree.add_command(help_cmd, guild=guild)
    tree.add_command(status_cmd, guild=guild)
