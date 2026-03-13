"""Tests for Discord bot launcher (run_bot.py) and NpcWarsBot wiring."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import make_bot_config


# ---------------------------------------------------------------------------
# NpcWarsBot accepts results_dir and claims_state via BotDeps
# ---------------------------------------------------------------------------


class TestBotAcceptsNewParams:
    def test_bot_stores_results_dir(self):
        from discord_bot.bot import BotDeps, NpcWarsBot

        cfg = make_bot_config()
        deps = BotDeps(results_dir="/tmp/results")
        bot = NpcWarsBot(cfg, deps=deps)
        assert bot.results_dir == "/tmp/results"

    def test_bot_stores_claims_state(self):
        from discord_bot.bot import BotDeps, NpcWarsBot

        cfg = make_bot_config()
        state = {"emoji1": "user1"}
        deps = BotDeps(claims_state=state)
        bot = NpcWarsBot(cfg, deps=deps)
        assert bot.claims_state is state

    def test_bot_defaults_results_dir_to_results(self):
        from discord_bot.bot import NpcWarsBot

        cfg = make_bot_config()
        bot = NpcWarsBot(cfg)
        assert bot.results_dir == "results"

    def test_bot_defaults_claims_state_to_empty_dict(self):
        from discord_bot.bot import NpcWarsBot

        cfg = make_bot_config()
        bot = NpcWarsBot(cfg)
        assert bot.claims_state == {}


# ---------------------------------------------------------------------------
# setup_hook wires all 5 command modules via deps
# ---------------------------------------------------------------------------


class TestSetupHookWiring:
    @pytest.mark.asyncio
    async def test_setup_hook_calls_general_register(self):
        from discord_bot.bot import BotDeps, NpcWarsBot

        deps = BotDeps(results_dir="/r")
        bot = NpcWarsBot(make_bot_config(), deps=deps)
        bot.tree.sync = AsyncMock()
        with patch("discord_bot.bot.general_register") as mock_gen:
            await bot.setup_hook()
            mock_gen.assert_called_once()

    @pytest.mark.asyncio
    async def test_setup_hook_calls_claims_register_with_state(self):
        from discord_bot.bot import BotDeps, NpcWarsBot

        state = {"e": "u"}
        deps = BotDeps(results_dir="/r", claims_state=state)
        bot = NpcWarsBot(make_bot_config(), deps=deps)
        bot.tree.sync = AsyncMock()
        with patch("discord_bot.bot.claims_register") as mock_cl:
            await bot.setup_hook()
            args = mock_cl.call_args
            assert args[0][2] is state  # third positional arg is claims_state

    @pytest.mark.asyncio
    async def test_setup_hook_calls_results_register_with_results_dir(self):
        from discord_bot.bot import BotDeps, NpcWarsBot

        deps = BotDeps(results_dir="/my/results")
        bot = NpcWarsBot(make_bot_config(), deps=deps)
        bot.tree.sync = AsyncMock()
        with patch("discord_bot.bot.results_register") as mock_res:
            await bot.setup_hook()
            args = mock_res.call_args
            assert args[0][2] == "/my/results"

    @pytest.mark.asyncio
    async def test_setup_hook_calls_leaderboard_register_with_results_dir(self):
        from discord_bot.bot import BotDeps, NpcWarsBot

        deps = BotDeps(results_dir="/my/results")
        bot = NpcWarsBot(make_bot_config(), deps=deps)
        bot.tree.sync = AsyncMock()
        with patch("discord_bot.bot.leaderboard_register") as mock_lb:
            await bot.setup_hook()
            args = mock_lb.call_args
            assert args[0][2] == "/my/results"

    @pytest.mark.asyncio
    async def test_setup_hook_syncs_tree(self):
        from discord_bot.bot import BotDeps, NpcWarsBot

        deps = BotDeps(results_dir="/r")
        bot = NpcWarsBot(make_bot_config(), deps=deps)
        bot.tree.sync = AsyncMock()
        with patch("discord_bot.bot.general_register"), \
             patch("discord_bot.bot.claims_register"), \
             patch("discord_bot.bot.results_register"), \
             patch("discord_bot.bot.leaderboard_register"):
            await bot.setup_hook()
        bot.tree.sync.assert_called_once()


# ---------------------------------------------------------------------------
# scripts/run_bot.py launcher
# ---------------------------------------------------------------------------


class TestCreateBot:
    """Test create_bot() builds NpcWarsBot with correct wiring."""

    def test_create_bot_returns_npc_wars_bot(self):
        from scripts.run_bot import create_bot
        from discord_bot.bot import NpcWarsBot

        cfg = make_bot_config()
        bot = create_bot(cfg, results_dir="/r", claims_state={})
        assert isinstance(bot, NpcWarsBot)

    def test_create_bot_passes_results_dir(self):
        from scripts.run_bot import create_bot

        cfg = make_bot_config()
        bot = create_bot(cfg, results_dir="/my/results", claims_state={})
        assert bot.results_dir == "/my/results"

    def test_create_bot_passes_claims_state(self):
        from scripts.run_bot import create_bot

        cfg = make_bot_config()
        state = {"x": "y"}
        bot = create_bot(cfg, results_dir="/r", claims_state=state)
        assert bot.claims_state is state


class TestMain:
    """Test main() wiring: loads config, claims, creates bot, runs it."""

    def test_main_loads_config_and_runs_bot(self):
        from scripts.run_bot import main

        fake_cfg = make_bot_config()
        fake_cfg["bot_token"] = "secret"
        mock_bot = MagicMock()

        with patch("scripts.run_bot.load_config", return_value=fake_cfg) as m_cfg, \
             patch("scripts.run_bot.load_claims", return_value={}) as m_claims, \
             patch("scripts.run_bot.create_bot", return_value=mock_bot) as m_create:
            main()
            m_cfg.assert_called_once()
            m_claims.assert_called_once()
            m_create.assert_called_once()
            mock_bot.run.assert_called_once_with("secret")

    def test_main_passes_claims_to_create_bot(self):
        from scripts.run_bot import main

        fake_cfg = make_bot_config()
        claims = {"emoji": "user"}
        mock_bot = MagicMock()

        with patch("scripts.run_bot.load_config", return_value=fake_cfg), \
             patch("scripts.run_bot.load_claims", return_value=claims), \
             patch("scripts.run_bot.create_bot", return_value=mock_bot) as m_create:
            main()
            _, kwargs = m_create.call_args
            assert kwargs["claims_state"] is claims
