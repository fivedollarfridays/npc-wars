"""Tests for unified Discord bot — command routing and multi-game formatting.

Covers T67.1 acceptance criteria:
- Single bot binary serves both games
- /killswitch and /circuit command groups
- /tv highlights <game> shows recent highlights
- /season standings <game> shows current season
- Unified formatters for stats, standings, and episode summaries
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from tests.conftest import make_bot_config


# ---------------------------------------------------------------------------
# Command routing: /killswitch and /circuit groups
# ---------------------------------------------------------------------------

class TestGameCommandGroups:
    """Verify /killswitch and /circuit command groups register correctly."""

    def test_game_commands_module_exists(self) -> None:
        import discord_bot.commands.game_commands  # noqa: F401

    def test_register_returns_two_groups(self) -> None:
        from discord_bot.commands.game_commands import register_commands
        tree = MagicMock()
        guild = MagicMock()
        register_commands(tree, guild, bots_dir="bots", results_dir="results")
        group_names = [call.args[0].name for call in tree.add_command.call_args_list]
        assert "killswitch" in group_names
        assert "circuit" in group_names

    def test_killswitch_group_has_play_subcommand(self) -> None:
        from discord_bot.commands.game_commands import register_commands
        tree = MagicMock()
        guild = MagicMock()
        register_commands(tree, guild, bots_dir="bots", results_dir="results")
        ks_group = next(
            call.args[0] for call in tree.add_command.call_args_list
            if call.args[0].name == "killswitch"
        )
        cmd_names = [c.name for c in ks_group.commands]
        assert "play" in cmd_names

    def test_circuit_group_has_race_subcommand(self) -> None:
        from discord_bot.commands.game_commands import register_commands
        tree = MagicMock()
        guild = MagicMock()
        register_commands(tree, guild, bots_dir="bots", results_dir="results")
        cc_group = next(
            call.args[0] for call in tree.add_command.call_args_list
            if call.args[0].name == "circuit"
        )
        cmd_names = [c.name for c in cc_group.commands]
        assert "race" in cmd_names


# ---------------------------------------------------------------------------
# /tv command group
# ---------------------------------------------------------------------------

class TestTvCommandGroup:
    """Verify /tv highlights <game> command."""

    def test_tv_commands_module_exists(self) -> None:
        import discord_bot.commands.tv_commands  # noqa: F401

    def test_register_creates_tv_group(self) -> None:
        from discord_bot.commands.tv_commands import register_commands
        tree = MagicMock()
        guild = MagicMock()
        register_commands(tree, guild, results_dir="results")
        group_names = [call.args[0].name for call in tree.add_command.call_args_list]
        assert "tv" in group_names

    def test_tv_group_has_highlights_subcommand(self) -> None:
        from discord_bot.commands.tv_commands import register_commands
        tree = MagicMock()
        guild = MagicMock()
        register_commands(tree, guild, results_dir="results")
        tv_group = next(
            call.args[0] for call in tree.add_command.call_args_list
            if call.args[0].name == "tv"
        )
        cmd_names = [c.name for c in tv_group.commands]
        assert "highlights" in cmd_names


# ---------------------------------------------------------------------------
# /season standings <game> — game-based lookup
# ---------------------------------------------------------------------------

class TestSeasonStandingsByGame:
    """Verify /season standings accepts game parameter."""

    def test_season_commands_register(self) -> None:
        from discord_bot.commands.season_commands import register_commands
        assert callable(register_commands)

    def test_format_game_standings_ks(self) -> None:
        from discord_bot.formatters import format_game_standings
        standings = [
            {"participant": "A", "points": 45, "tier": "Diamond"},
            {"participant": "B", "points": 30, "tier": "Gold"},
        ]
        result = format_game_standings("kill_switch", "Season 1", standings)
        assert "Kill Switch" in result["title"]
        assert "Diamond" in str(result)

    def test_format_game_standings_cc(self) -> None:
        from discord_bot.formatters import format_game_standings
        standings = [
            {"participant": "FastCar", "points": 25, "tier": "Diamond"},
        ]
        result = format_game_standings("code_circuit", "Season 1", standings)
        assert "Code Circuit" in result["title"]

    def test_format_game_standings_empty(self) -> None:
        from discord_bot.formatters import format_game_standings
        result = format_game_standings("kill_switch", "Season 1", [])
        assert "No results" in result["description"]


# ---------------------------------------------------------------------------
# Highlight formatting
# ---------------------------------------------------------------------------

class TestHighlightFormatting:
    """Verify formatters for highlight display."""

    def test_format_highlights_exists(self) -> None:
        from discord_bot.formatters import format_highlights
        assert callable(format_highlights)

    def test_format_highlights_ks(self) -> None:
        from discord_bot.formatters import format_highlights
        highlights = [
            {"round_range": (3, 6), "trigger_type": "kill",
             "participants": ["A", "B"], "drama_score": 8,
             "commentary": ["A eliminates B"]},
        ]
        result = format_highlights("kill_switch", highlights)
        assert "Kill Switch" in result["title"]
        assert "kill" in str(result).lower()

    def test_format_highlights_cc(self) -> None:
        from discord_bot.formatters import format_highlights
        highlights = [
            {"round_range": (5, 8), "trigger_type": "overtake",
             "participants": ["FastCar", "SlowCar"], "drama_score": 6,
             "commentary": ["FastCar overtakes SlowCar"]},
        ]
        result = format_highlights("code_circuit", highlights)
        assert "Code Circuit" in result["title"]

    def test_format_highlights_empty(self) -> None:
        from discord_bot.formatters import format_highlights
        result = format_highlights("kill_switch", [])
        assert "No highlights" in result["description"]

    def test_format_highlights_limits_to_five(self) -> None:
        from discord_bot.formatters import format_highlights
        highlights = [
            {"round_range": (i, i + 1), "trigger_type": "kill",
             "participants": ["A"], "drama_score": i, "commentary": [f"Event {i}"]}
            for i in range(10)
        ]
        result = format_highlights("kill_switch", highlights)
        hl_field = next(f for f in result["fields"] if f["name"] == "Recent Highlights")
        lines = hl_field["value"].strip().split("\n")
        assert len(lines) <= 5


# ---------------------------------------------------------------------------
# Bot wiring — single binary serves both games
# ---------------------------------------------------------------------------

class TestUnifiedBot:
    """Verify bot registers game command groups in setup_hook."""

    def test_bot_module_imports_game_commands(self) -> None:
        from discord_bot import bot
        src = open(bot.__file__).read()
        assert "game_commands" in src

    def test_bot_module_imports_tv_commands(self) -> None:
        from discord_bot import bot
        src = open(bot.__file__).read()
        assert "tv_commands" in src

    @pytest.mark.asyncio
    async def test_setup_hook_registers_game_commands(self) -> None:
        from discord_bot.bot import NpcWarsBot
        cfg = make_bot_config()
        bot = NpcWarsBot(cfg)
        with patch.object(bot.tree, "sync", new_callable=AsyncMock):
            await bot.setup_hook()
        guild = discord.Object(id=cfg["guild_id"])
        cmd_names = [c.name for c in bot.tree.get_commands(guild=guild)]
        assert "killswitch" in cmd_names
        assert "circuit" in cmd_names
        assert "tv" in cmd_names


# ---------------------------------------------------------------------------
# Multi-game formatting consistency
# ---------------------------------------------------------------------------

class TestMultiGameFormatting:
    """Ensure formatters produce consistent structures across games."""

    def test_highlights_dict_shape(self) -> None:
        from discord_bot.formatters import format_highlights
        for game in ("kill_switch", "code_circuit"):
            result = format_highlights(game, [])
            assert "title" in result
            assert "description" in result
            assert "color" in result
            assert "fields" in result

    def test_game_standings_dict_shape(self) -> None:
        from discord_bot.formatters import format_game_standings
        standings = [{"participant": "X", "points": 10, "tier": "Gold"}]
        for game in ("kill_switch", "code_circuit"):
            result = format_game_standings(game, "S1", standings)
            assert "title" in result
            assert "description" in result
            assert "color" in result
            assert "fields" in result

    def test_format_highlights_returns_plain_dict(self) -> None:
        from discord_bot.formatters import format_highlights
        result = format_highlights("kill_switch", [])
        assert isinstance(result, dict)

    def test_format_game_standings_returns_plain_dict(self) -> None:
        from discord_bot.formatters import format_game_standings
        result = format_game_standings("kill_switch", "S1", [])
        assert isinstance(result, dict)
