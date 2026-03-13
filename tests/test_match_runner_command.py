"""Tests for /run_match Discord slash command."""

import ast
import inspect
from unittest.mock import AsyncMock, patch

import pytest

from tests.conftest import make_mock_interaction


FAKE_MATCH_DATA = {
    "match_id": 1,
    "winner": "A",
    "duration_rounds": 10,
    "players": [
        {"name": "BotA", "emoji": "A"},
        {"name": "BotB", "emoji": "B"},
    ],
    "eliminations": [],
    "stats": {},
}


# ---------------------------------------------------------------------------
# Cycle 1-2: run_match_callback triggers match in thread pool
# ---------------------------------------------------------------------------


class TestRunMatchCallback:
    @pytest.mark.asyncio
    async def test_triggers_match(self):
        """run_match_callback loads bots and calls run_match."""
        from discord_bot.commands.match_runner import run_match_callback

        interaction = make_mock_interaction(with_defer=True)
        fake_bots = [{"name": "A", "emoji": "A"}, {"name": "B", "emoji": "B"}]

        with patch("discord_bot.commands.match_runner.load_bots", return_value=fake_bots) as mock_load, \
             patch("discord_bot.commands.match_runner.run_match", return_value=FAKE_MATCH_DATA) as mock_run, \
             patch("discord_bot.commands.match_runner.write_match"), \
             patch("discord_bot.commands.match_runner.next_match_id", return_value=1):
            await run_match_callback(interaction, bots_dir="/bots", results_dir="/results")
            mock_load.assert_called_once_with("/bots")
            mock_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_defers_before_load_bots(self):
        """Defer is called before load_bots to avoid Discord timeout."""
        from discord_bot.commands.match_runner import run_match_callback

        interaction = make_mock_interaction(with_defer=True)
        fake_bots = [{"name": "A", "emoji": "A"}, {"name": "B", "emoji": "B"}]
        call_order: list[str] = []

        async def track_defer() -> None:
            call_order.append("defer")

        def track_load_bots(_dir: str) -> list[dict]:
            call_order.append("load_bots")
            return fake_bots

        interaction.response.defer = AsyncMock(side_effect=track_defer)

        with patch("discord_bot.commands.match_runner.load_bots", side_effect=track_load_bots), \
             patch("discord_bot.commands.match_runner.run_match", return_value=FAKE_MATCH_DATA), \
             patch("discord_bot.commands.match_runner.write_match"), \
             patch("discord_bot.commands.match_runner.next_match_id", return_value=1):
            await run_match_callback(interaction, bots_dir="/bots", results_dir="/results")
            assert call_order == ["defer", "load_bots"]

    @pytest.mark.asyncio
    async def test_defers_response(self):
        """Interaction is deferred since match takes time."""
        from discord_bot.commands.match_runner import run_match_callback

        interaction = make_mock_interaction(with_defer=True)
        fake_bots = [{"name": "A", "emoji": "A"}, {"name": "B", "emoji": "B"}]

        with patch("discord_bot.commands.match_runner.load_bots", return_value=fake_bots), \
             patch("discord_bot.commands.match_runner.run_match", return_value=FAKE_MATCH_DATA), \
             patch("discord_bot.commands.match_runner.write_match"), \
             patch("discord_bot.commands.match_runner.next_match_id", return_value=1):
            await run_match_callback(interaction, bots_dir="/bots", results_dir="/results")
            interaction.response.defer.assert_called_once()


# ---------------------------------------------------------------------------
# Cycle 3: Result saved and announcement posted
# ---------------------------------------------------------------------------


class TestResultSavingAndAnnouncement:
    @pytest.mark.asyncio
    async def test_result_saved_via_write_match(self):
        """Match result is saved to disk via write_match."""
        from discord_bot.commands.match_runner import run_match_callback

        interaction = make_mock_interaction(with_defer=True)
        fake_bots = [{"name": "A", "emoji": "A"}, {"name": "B", "emoji": "B"}]

        with patch("discord_bot.commands.match_runner.load_bots", return_value=fake_bots), \
             patch("discord_bot.commands.match_runner.run_match", return_value=FAKE_MATCH_DATA), \
             patch("discord_bot.commands.match_runner.write_match") as mock_write, \
             patch("discord_bot.commands.match_runner.next_match_id", return_value=1):
            await run_match_callback(interaction, bots_dir="/bots", results_dir="/results")
            mock_write.assert_called_once_with(FAKE_MATCH_DATA, "/results")

    @pytest.mark.asyncio
    async def test_announcement_posted(self):
        """A followup message is sent after match completes."""
        from discord_bot.commands.match_runner import run_match_callback

        interaction = make_mock_interaction(with_defer=True)
        fake_bots = [{"name": "A", "emoji": "A"}, {"name": "B", "emoji": "B"}]

        with patch("discord_bot.commands.match_runner.load_bots", return_value=fake_bots), \
             patch("discord_bot.commands.match_runner.run_match", return_value=FAKE_MATCH_DATA), \
             patch("discord_bot.commands.match_runner.write_match"), \
             patch("discord_bot.commands.match_runner.next_match_id", return_value=1):
            await run_match_callback(interaction, bots_dir="/bots", results_dir="/results")
            interaction.followup.send.assert_called_once()
            call_kwargs = interaction.followup.send.call_args
            # Should contain winner info
            content = str(call_kwargs)
            assert "A" in content  # winner emoji


# ---------------------------------------------------------------------------
# Cycle 4: Optional seed parameter
# ---------------------------------------------------------------------------


class TestSeedParameter:
    @pytest.mark.asyncio
    async def test_seed_passed_to_run_match(self):
        """Optional seed parameter is forwarded to run_match."""
        from discord_bot.commands.match_runner import run_match_callback

        interaction = make_mock_interaction(with_defer=True)
        fake_bots = [{"name": "A", "emoji": "A"}, {"name": "B", "emoji": "B"}]

        with patch("discord_bot.commands.match_runner.load_bots", return_value=fake_bots), \
             patch("discord_bot.commands.match_runner.run_match", return_value=FAKE_MATCH_DATA) as mock_run, \
             patch("discord_bot.commands.match_runner.write_match"), \
             patch("discord_bot.commands.match_runner.next_match_id", return_value=1):
            await run_match_callback(
                interaction, bots_dir="/bots", results_dir="/results", seed=42,
            )
            _, kwargs = mock_run.call_args
            assert kwargs.get("seed") == 42

    @pytest.mark.asyncio
    async def test_no_seed_defaults_to_none(self):
        """When no seed given, run_match gets seed=None."""
        from discord_bot.commands.match_runner import run_match_callback

        interaction = make_mock_interaction(with_defer=True)
        fake_bots = [{"name": "A", "emoji": "A"}, {"name": "B", "emoji": "B"}]

        with patch("discord_bot.commands.match_runner.load_bots", return_value=fake_bots), \
             patch("discord_bot.commands.match_runner.run_match", return_value=FAKE_MATCH_DATA) as mock_run, \
             patch("discord_bot.commands.match_runner.write_match"), \
             patch("discord_bot.commands.match_runner.next_match_id", return_value=1):
            await run_match_callback(
                interaction, bots_dir="/bots", results_dir="/results",
            )
            _, kwargs = mock_run.call_args
            assert kwargs.get("seed") is None


# ---------------------------------------------------------------------------
# Cycle 5: Match ID auto-increments
# ---------------------------------------------------------------------------


class TestMatchIdAutoIncrement:
    @pytest.mark.asyncio
    async def test_match_id_increments_from_existing(self):
        """match_id should be max existing + 1."""
        from discord_bot.commands.match_runner import run_match_callback

        interaction = make_mock_interaction(with_defer=True)
        fake_bots = [{"name": "A", "emoji": "A"}, {"name": "B", "emoji": "B"}]
        with patch("discord_bot.commands.match_runner.load_bots", return_value=fake_bots), \
             patch("discord_bot.commands.match_runner.run_match", return_value=FAKE_MATCH_DATA) as mock_run, \
             patch("discord_bot.commands.match_runner.write_match"), \
             patch("discord_bot.commands.match_runner.next_match_id", return_value=4):
            await run_match_callback(interaction, bots_dir="/bots", results_dir="/results")
            args, kwargs = mock_run.call_args
            assert kwargs.get("match_id") == 4 or (len(args) > 1 and args[1] == 4)

    @pytest.mark.asyncio
    async def test_match_id_starts_at_1_when_empty(self):
        """First match gets match_id=1."""
        from discord_bot.commands.match_runner import run_match_callback

        interaction = make_mock_interaction(with_defer=True)
        fake_bots = [{"name": "A", "emoji": "A"}, {"name": "B", "emoji": "B"}]

        with patch("discord_bot.commands.match_runner.load_bots", return_value=fake_bots), \
             patch("discord_bot.commands.match_runner.run_match", return_value=FAKE_MATCH_DATA) as mock_run, \
             patch("discord_bot.commands.match_runner.write_match"), \
             patch("discord_bot.commands.match_runner.next_match_id", return_value=1):
            await run_match_callback(interaction, bots_dir="/bots", results_dir="/results")
            args, kwargs = mock_run.call_args
            assert kwargs.get("match_id") == 1 or (len(args) > 1 and args[1] == 1)


# ---------------------------------------------------------------------------
# Cycle 6: register_commands + not enough bots error
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Cycle 7: Authorization — default_permissions on /run_match
# ---------------------------------------------------------------------------


class TestRunMatchAuthorization:
    def test_default_permissions_decorator_present(self):
        """register_commands applies default_permissions to /run_match."""
        from discord_bot.commands import match_runner

        source = inspect.getsource(match_runner)
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Attribute) and func.attr == "default_permissions":
                    return  # Found it
        pytest.fail("default_permissions decorator not found in match_runner.py")

    def test_default_permissions_requires_manage_guild(self):
        """default_permissions decorator requires manage_guild=True."""
        from discord_bot.commands import match_runner

        source = inspect.getsource(match_runner)
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Attribute) and func.attr == "default_permissions":
                    for kw in node.keywords:
                        if kw.arg == "manage_guild":
                            assert isinstance(kw.value, ast.Constant)
                            assert kw.value.value is True
                            return
                    pytest.fail("manage_guild keyword not found in default_permissions")
        pytest.fail("default_permissions decorator not found in match_runner.py")


class TestRegisterAndEdgeCases:
    def test_register_commands_callable(self):
        """register_commands function exists and is callable."""
        from discord_bot.commands.match_runner import register_commands
        assert callable(register_commands)

    @pytest.mark.asyncio
    async def test_not_enough_bots_sends_error(self):
        """If fewer than 2 bots loaded, send error via followup after defer."""
        from discord_bot.commands.match_runner import run_match_callback

        interaction = make_mock_interaction(with_defer=True)
        fake_bots = [{"name": "A", "emoji": "A"}]  # only 1 bot

        with patch("discord_bot.commands.match_runner.load_bots", return_value=fake_bots), \
             patch("discord_bot.commands.match_runner.run_match") as mock_run, \
             patch("discord_bot.commands.match_runner.next_match_id", return_value=1):
            await run_match_callback(interaction, bots_dir="/bots", results_dir="/results")
            mock_run.assert_not_called()
            interaction.response.defer.assert_called_once()
            interaction.followup.send.assert_called_once()
            msg = interaction.followup.send.call_args[0][0]
            assert "Not enough bots" in msg
