"""NPC Wars Discord bot — main bot class."""

import logging
from dataclasses import dataclass, field

import discord

from discord_bot.commands.general import register_commands as general_register
from discord_bot.commands.claims import register_commands as claims_register
from discord_bot.commands.results import register_commands as results_register
from discord_bot.commands.leaderboard import register_commands as leaderboard_register
from discord_bot.commands.match_runner import register_commands as match_runner_register

log = logging.getLogger(__name__)


@dataclass
class BotDeps:
    """Dependencies for NpcWarsBot command modules."""

    results_dir: str = "results"
    bots_dir: str = "bots"
    claims_state: dict[str, str] = field(default_factory=dict)
    claims_path: str | None = None


class NpcWarsBot(discord.Client):
    """Discord client for NPC Wars with slash command support."""

    def __init__(self, config: dict, deps: BotDeps | None = None) -> None:
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.config = config
        self.deps = deps or BotDeps()
        self.tree = discord.app_commands.CommandTree(self)
        self.tree.on_error = self._on_tree_error  # type: ignore[method-assign]

    @property
    def results_dir(self) -> str:
        return self.deps.results_dir

    @property
    def bots_dir(self) -> str:
        return self.deps.bots_dir

    @property
    def claims_state(self) -> dict[str, str]:
        return self.deps.claims_state

    @property
    def claims_path(self) -> str | None:
        return self.deps.claims_path

    async def setup_hook(self) -> None:
        """Register all command modules and sync with Discord."""
        guild = discord.Object(id=self.config["guild_id"])
        general_register(self.tree, guild)
        claims_register(
            self.tree, guild, self.deps.claims_state,
            claims_path=self.deps.claims_path,
        )
        results_register(self.tree, guild, self.deps.results_dir)
        leaderboard_register(self.tree, guild, self.deps.results_dir)
        match_runner_register(self.tree, guild, self.deps.bots_dir, self.deps.results_dir)
        await self.tree.sync(guild=guild)

    async def on_ready(self) -> None:
        """Log when the bot connects."""
        log.info("Logged in as %s", self.user)

    async def _on_tree_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        """Handle slash command errors with a generic user message."""
        log.exception("Slash command error", exc_info=error)
        msg = "An internal error occurred."
        if not interaction.response.is_done():
            await interaction.response.send_message(msg, ephemeral=True)
        else:
            await interaction.followup.send(msg, ephemeral=True)
