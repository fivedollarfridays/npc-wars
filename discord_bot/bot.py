"""NPC Wars Discord bot — main bot class."""

import logging

import discord

from discord_bot.commands.general import register_commands

log = logging.getLogger(__name__)


class NpcWarsBot(discord.Client):
    """Discord client for NPC Wars with slash command support."""

    def __init__(self, config: dict) -> None:
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.config = config
        self.tree = discord.app_commands.CommandTree(self)
        self.tree.on_error = self._on_tree_error  # type: ignore[method-assign]

    async def setup_hook(self) -> None:
        """Register commands and sync with Discord."""
        guild = discord.Object(id=self.config["guild_id"])
        register_commands(self.tree, guild)
        await self.tree.sync(guild=guild)

    async def on_ready(self) -> None:
        """Log when the bot connects."""
        log.info("Logged in as %s", self.user)

    async def _on_tree_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        """Handle slash command errors by notifying the user."""
        msg = f"❌ Error: {error}"
        if not interaction.response.is_done():
            await interaction.response.send_message(msg, ephemeral=True)
        else:
            await interaction.followup.send(msg, ephemeral=True)
