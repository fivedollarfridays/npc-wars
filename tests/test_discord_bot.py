"""Tests for Discord bot scaffold — connection, config, slash commands."""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

class TestConfig:
    def test_config_reads_bot_token_from_env(self):
        from discord_bot.config import load_config
        with patch.dict(os.environ, {"BOT_TOKEN": "tok123", "GUILD_ID": "999"}):
            cfg = load_config()
        assert cfg["bot_token"] == "tok123"

    def test_config_reads_guild_id_from_env(self):
        from discord_bot.config import load_config
        with patch.dict(os.environ, {"BOT_TOKEN": "tok", "GUILD_ID": "42"}):
            cfg = load_config()
        assert cfg["guild_id"] == 42

    def test_config_missing_token_raises(self):
        from discord_bot.config import load_config
        env = {"GUILD_ID": "1"}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValueError, match="BOT_TOKEN"):
                load_config()

    def test_config_missing_guild_raises(self):
        from discord_bot.config import load_config
        env = {"BOT_TOKEN": "tok"}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValueError, match="GUILD_ID"):
                load_config()

    def test_config_optional_channel_ids_default_empty(self):
        from discord_bot.config import load_config
        with patch.dict(os.environ, {"BOT_TOKEN": "t", "GUILD_ID": "1"}, clear=True):
            cfg = load_config()
        assert cfg["announcement_channel_id"] is None
        assert cfg["results_channel_id"] is None

    def test_config_reads_channel_ids(self):
        from discord_bot.config import load_config
        env = {
            "BOT_TOKEN": "t", "GUILD_ID": "1",
            "ANNOUNCEMENT_CHANNEL_ID": "100",
            "RESULTS_CHANNEL_ID": "200",
        }
        with patch.dict(os.environ, env, clear=True):
            cfg = load_config()
        assert cfg["announcement_channel_id"] == 100
        assert cfg["results_channel_id"] == 200


# ---------------------------------------------------------------------------
# Bot class structure
# ---------------------------------------------------------------------------

class TestBotStructure:
    def test_bot_module_exists(self):
        import discord_bot.bot  # noqa: F401

    def test_npc_wars_bot_class_exists(self):
        from discord_bot.bot import NpcWarsBot
        assert NpcWarsBot is not None

    def test_bot_is_discord_client_subclass(self):
        import discord
        from discord_bot.bot import NpcWarsBot
        assert issubclass(NpcWarsBot, discord.Client)

    def test_bot_has_tree(self):
        from discord_bot.bot import NpcWarsBot
        cfg = {"bot_token": "t", "guild_id": 1,
               "announcement_channel_id": None, "results_channel_id": None}
        bot = NpcWarsBot(cfg)
        import discord
        assert isinstance(bot.tree, discord.app_commands.CommandTree)

    def test_bot_stores_config(self):
        from discord_bot.bot import NpcWarsBot
        cfg = {"bot_token": "tok", "guild_id": 7,
               "announcement_channel_id": None, "results_channel_id": None}
        bot = NpcWarsBot(cfg)
        assert bot.config is cfg


# ---------------------------------------------------------------------------
# /ping command
# ---------------------------------------------------------------------------

class TestPingCommand:
    def test_ping_command_registered(self):
        from discord_bot.commands.general import register_commands
        assert callable(register_commands)

    @pytest.mark.asyncio
    async def test_ping_responds_with_pong(self):
        from discord_bot.commands.general import ping_callback
        interaction = MagicMock()
        interaction.response = MagicMock()
        interaction.response.send_message = AsyncMock()
        await ping_callback(interaction)
        interaction.response.send_message.assert_called_once()
        msg = interaction.response.send_message.call_args[0][0]
        assert "pong" in msg.lower() or "🏓" in msg


# ---------------------------------------------------------------------------
# /help command
# ---------------------------------------------------------------------------

class TestHelpCommand:
    @pytest.mark.asyncio
    async def test_help_responds_with_embed_or_text(self):
        from discord_bot.commands.general import help_callback
        interaction = MagicMock()
        interaction.response = MagicMock()
        interaction.response.send_message = AsyncMock()
        await help_callback(interaction)
        interaction.response.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_help_mentions_available_commands(self):
        from discord_bot.commands.general import help_callback
        interaction = MagicMock()
        interaction.response = MagicMock()
        interaction.response.send_message = AsyncMock()
        await help_callback(interaction)
        call_kwargs = interaction.response.send_message.call_args
        # Either positional text or embed kwarg
        content = ""
        if call_kwargs[0]:
            content = str(call_kwargs[0][0])
        if call_kwargs[1].get("embed"):
            emb = call_kwargs[1]["embed"]
            content = emb.description or "" + " ".join(f.value for f in emb.fields)
        assert "/ping" in content or "ping" in content.lower()


# ---------------------------------------------------------------------------
# /status command
# ---------------------------------------------------------------------------

class TestStatusCommand:
    @pytest.mark.asyncio
    async def test_status_responds(self):
        from discord_bot.commands.general import status_callback
        interaction = MagicMock()
        interaction.response = MagicMock()
        interaction.response.send_message = AsyncMock()
        await status_callback(interaction)
        interaction.response.send_message.assert_called_once()


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_on_command_error_sends_message(self):
        from discord_bot.bot import NpcWarsBot
        cfg = {"bot_token": "t", "guild_id": 1,
               "announcement_channel_id": None, "results_channel_id": None}
        bot = NpcWarsBot(cfg)
        interaction = MagicMock()
        interaction.response = MagicMock()
        interaction.response.send_message = AsyncMock()
        interaction.response.is_done = MagicMock(return_value=False)
        error = Exception("boom")
        await bot.on_command_error(interaction, error)
        interaction.response.send_message.assert_called_once()
