"""NPC Wars Discord bot — main bot class."""

import logging
import sqlite3
from dataclasses import dataclass, field

import discord

from data.seasons import init_seasons_tables
from discord_bot.commands.general import register_commands as general_register
from discord_bot.commands.claims import register_commands as claims_register
from discord_bot.commands.results import register_commands as results_register
from discord_bot.commands.leaderboard import register_commands as leaderboard_register
from discord_bot.commands.match_runner import register_commands as match_runner_register
from discord_bot.commands.challenge import register_commands as challenge_register
from discord_bot.commands.season_commands import register_commands as season_register
from discord_bot.commands.game_commands import register_commands as game_register
from discord_bot.commands.tv_commands import register_commands as tv_register
from discord_bot.commands.submissions import setup_submission_listener

log = logging.getLogger(__name__)


@dataclass
class BotDeps:
    """Dependencies for NpcWarsBot command modules."""

    results_dir: str = "results"
    bots_dir: str = "bots"
    claims_state: dict[str, str] = field(default_factory=dict)
    claims_path: str | None = None
    db_path: str = "data/npcwars.db"


class NpcWarsBot(discord.Client):
    """Discord client for NPC Wars with slash command support."""

    def __init__(self, config: dict, deps: BotDeps | None = None) -> None:
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.config = config
        self.deps = deps or BotDeps()
        self.tree = discord.app_commands.CommandTree(self)
        self.tree.on_error = self._on_tree_error  # type: ignore[method-assign]
        self._db_conn = self._init_db()

    def _init_db(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.deps.db_path)
        conn.row_factory = sqlite3.Row
        init_seasons_tables(conn)
        return conn

    @property
    def db_conn(self) -> sqlite3.Connection:
        return self._db_conn

    @property
    def submissions_channel_id(self) -> int | None:
        return self.config.get("submissions_channel_id")

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
        challenge_register(self.tree, guild)
        season_register(self.tree, guild, self._db_conn)
        game_register(
            self.tree, guild,
            bots_dir=self.deps.bots_dir,
            results_dir=self.deps.results_dir,
        )
        tv_register(self.tree, guild, results_dir=self.deps.results_dir)
        if self.submissions_channel_id:
            setup_submission_listener(
                self, channel_id=self.submissions_channel_id,
            )
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
