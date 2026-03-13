"""Tests for /claim, /unclaim, /roster Discord slash commands."""

import ast
import inspect

import discord
import pytest
from unittest.mock import patch

from tests.conftest import make_mock_interaction
from discord_bot.commands.claims import (
    claim_callback,
    unclaim_callback,
    roster_callback,
    register_commands,
)


# ---------------------------------------------------------------------------
# _mutate_and_respond helper
# ---------------------------------------------------------------------------


class TestMutateAndRespond:
    @pytest.mark.asyncio
    async def test_calls_mutate_fn_and_sends_embed(self):
        """Helper applies mutation, syncs state, and sends formatted embed."""
        from data.emoji_claims import claim_emoji
        from discord_bot.commands.claims import _mutate_and_respond
        from discord_bot.formatters import format_claim_response

        state: dict = {}
        interaction = make_mock_interaction(user_id=1001)
        await _mutate_and_respond(
            interaction, "X", state, claim_emoji, format_claim_response,
        )
        interaction.response.send_message.assert_called_once()
        embed = interaction.response.send_message.call_args[1]["embed"]
        assert isinstance(embed, discord.Embed)
        assert embed.color == discord.Color.green()
        assert state == {"X": "1001"}

    @pytest.mark.asyncio
    async def test_failed_mutation_does_not_sync_state(self):
        """Helper does not sync state when mutation fails."""
        from data.emoji_claims import claim_emoji
        from discord_bot.commands.claims import _mutate_and_respond
        from discord_bot.formatters import format_claim_response

        state = {"X": "9999"}
        interaction = make_mock_interaction(user_id=1001)
        await _mutate_and_respond(
            interaction, "X", state, claim_emoji, format_claim_response,
        )
        embed = interaction.response.send_message.call_args[1]["embed"]
        assert embed.color == discord.Color.red()
        assert state == {"X": "9999"}

    @pytest.mark.asyncio
    async def test_saves_when_claims_path_provided(self):
        """Helper calls save_claims when claims_path is set and mutation succeeds."""
        from data.emoji_claims import claim_emoji
        from discord_bot.commands.claims import _mutate_and_respond
        from discord_bot.formatters import format_claim_response

        state: dict = {}
        interaction = make_mock_interaction(user_id=1001)
        with patch("discord_bot.commands.claims.save_claims") as mock_save:
            await _mutate_and_respond(
                interaction, "X", state, claim_emoji, format_claim_response,
                claims_path="/tmp/test.json",
            )
            mock_save.assert_called_once_with(state, "/tmp/test.json")


# ---------------------------------------------------------------------------
# /claim
# ---------------------------------------------------------------------------


class TestClaimCommand:
    @pytest.mark.asyncio
    async def test_claim_success(self):
        """Valid emoji, user has <3 claims -> success embed."""
        state: dict = {}
        interaction = make_mock_interaction(user_id=1001)
        await claim_callback(interaction, "X", state)
        interaction.response.send_message.assert_called_once()
        embed = interaction.response.send_message.call_args[1]["embed"]
        assert isinstance(embed, discord.Embed)
        assert embed.color == discord.Color.green()
        assert "X" in embed.description
        assert state == {"X": "1001"}

    @pytest.mark.asyncio
    async def test_claim_already_taken(self):
        """Emoji owned by another user -> error response."""
        state = {"X": "9999"}
        interaction = make_mock_interaction(user_id=1001)
        await claim_callback(interaction, "X", state)
        embed = interaction.response.send_message.call_args[1]["embed"]
        assert embed.color == discord.Color.red()
        assert state == {"X": "9999"}

    @pytest.mark.asyncio
    async def test_claim_user_limit(self):
        """User already has 3 claims -> error response."""
        state = {"A": "1001", "B": "1001", "C": "1001"}
        interaction = make_mock_interaction(user_id=1001)
        await claim_callback(interaction, "D", state)
        embed = interaction.response.send_message.call_args[1]["embed"]
        assert embed.color == discord.Color.red()
        assert "D" not in state

    @pytest.mark.asyncio
    async def test_claim_own_emoji_again(self):
        """User tries to claim emoji they already own -> error."""
        state = {"X": "1001"}
        interaction = make_mock_interaction(user_id=1001)
        await claim_callback(interaction, "X", state)
        embed = interaction.response.send_message.call_args[1]["embed"]
        assert embed.color == discord.Color.red()


# ---------------------------------------------------------------------------
# /unclaim
# ---------------------------------------------------------------------------


class TestUnclaimCommand:
    @pytest.mark.asyncio
    async def test_unclaim_success(self):
        """User owns emoji -> releases it, success response."""
        state = {"X": "1001"}
        interaction = make_mock_interaction(user_id=1001)
        await unclaim_callback(interaction, "X", state)
        embed = interaction.response.send_message.call_args[1]["embed"]
        assert embed.color == discord.Color.green()
        assert "X" not in state

    @pytest.mark.asyncio
    async def test_unclaim_not_owned(self):
        """User doesn't own that emoji -> error response."""
        state = {"X": "9999"}
        interaction = make_mock_interaction(user_id=1001)
        await unclaim_callback(interaction, "X", state)
        embed = interaction.response.send_message.call_args[1]["embed"]
        assert embed.color == discord.Color.red()
        assert state == {"X": "9999"}


# ---------------------------------------------------------------------------
# /roster
# ---------------------------------------------------------------------------


class TestRosterCommand:
    @pytest.mark.asyncio
    async def test_roster_empty(self):
        """No claims -> embed says no claims yet."""
        state: dict = {}
        interaction = make_mock_interaction()
        await roster_callback(interaction, state)
        embed = interaction.response.send_message.call_args[1]["embed"]
        assert isinstance(embed, discord.Embed)
        assert "no" in embed.description.lower() or "empty" in embed.description.lower()

    @pytest.mark.asyncio
    async def test_roster_with_claims(self):
        """Two claims -> embed lists them."""
        state = {"X": "1001", "Y": "2002"}
        interaction = make_mock_interaction()
        await roster_callback(interaction, state)
        embed = interaction.response.send_message.call_args[1]["embed"]
        assert "X" in embed.description
        assert "Y" in embed.description
        assert "1001" in embed.description
        assert "2002" in embed.description


# ---------------------------------------------------------------------------
# register_commands
# ---------------------------------------------------------------------------


class TestRegisterCommands:
    def test_register_commands_callable(self):
        """register_commands is importable and callable."""
        assert callable(register_commands)


# ---------------------------------------------------------------------------
# Persistence: save_claims called on mutation
# ---------------------------------------------------------------------------


class TestClaimPersistence:
    @pytest.mark.asyncio
    async def test_save_called_after_successful_claim(self):
        """save_claims is called after a successful claim."""
        state: dict = {}
        interaction = make_mock_interaction(user_id=1001)
        with patch("discord_bot.commands.claims.save_claims") as mock_save:
            await claim_callback(interaction, "X", state, claims_path="/tmp/c.json")
            mock_save.assert_called_once_with(state, "/tmp/c.json")

    @pytest.mark.asyncio
    async def test_save_not_called_on_failed_claim(self):
        """save_claims is NOT called when claim fails (duplicate)."""
        state = {"X": "9999"}
        interaction = make_mock_interaction(user_id=1001)
        with patch("discord_bot.commands.claims.save_claims") as mock_save:
            await claim_callback(interaction, "X", state, claims_path="/tmp/c.json")
            mock_save.assert_not_called()

    @pytest.mark.asyncio
    async def test_save_called_after_successful_unclaim(self):
        """save_claims is called after a successful unclaim."""
        state = {"X": "1001"}
        interaction = make_mock_interaction(user_id=1001)
        with patch("discord_bot.commands.claims.save_claims") as mock_save:
            await unclaim_callback(interaction, "X", state, claims_path="/tmp/c.json")
            mock_save.assert_called_once_with(state, "/tmp/c.json")

    @pytest.mark.asyncio
    async def test_save_not_called_on_failed_unclaim(self):
        """save_claims is NOT called when unclaim fails (not owned)."""
        state = {"X": "9999"}
        interaction = make_mock_interaction(user_id=1001)
        with patch("discord_bot.commands.claims.save_claims") as mock_save:
            await unclaim_callback(interaction, "X", state, claims_path="/tmp/c.json")
            mock_save.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_save_when_claims_path_is_none(self):
        """save_claims not called when claims_path is None (backward compat)."""
        state: dict = {}
        interaction = make_mock_interaction(user_id=1001)
        with patch("discord_bot.commands.claims.save_claims") as mock_save:
            await claim_callback(interaction, "X", state)
            mock_save.assert_not_called()


# ---------------------------------------------------------------------------
# Cooldown decorators on /claim and /unclaim
# ---------------------------------------------------------------------------


class TestClaimsCooldown:
    def test_claim_cooldown_decorator_present(self):
        """register_commands applies cooldown to /claim."""
        from discord_bot.commands import claims

        source = inspect.getsource(claims)
        count = source.count("cooldown(1, 5.0)")
        assert count >= 2, f"Expected at least 2 cooldown decorators, found {count}"

    def test_unclaim_cooldown_decorator_present(self):
        """register_commands applies cooldown to /unclaim via AST inspection."""
        from discord_bot.commands import claims

        source = inspect.getsource(claims)
        tree = ast.parse(source)
        cooldown_count = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Attribute) and func.attr == "cooldown":
                    cooldown_count += 1
        assert cooldown_count >= 2, (
            f"Expected >=2 cooldown decorators, found {cooldown_count}"
        )


class TestClaimsPersistenceRoundtrip:
    def test_claims_survive_save_reload(self, tmp_path):
        """Claims persisted to disk can be reloaded."""
        from data.emoji_claims import load_claims, save_claims

        path = str(tmp_path / "claims.json")
        state = {"X": "1001", "Y": "2002"}
        save_claims(state, path)
        reloaded = load_claims(path)
        assert reloaded == state
