"""Tests for /claim, /unclaim, /roster Discord slash commands."""

import discord
import pytest
from unittest.mock import AsyncMock, MagicMock

from discord_bot.commands.claims import (
    claim_callback,
    unclaim_callback,
    roster_callback,
    register_commands,
)


def _make_interaction(user_id: int = 1001) -> MagicMock:
    """Create a mock Discord interaction with a fake user."""
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = MagicMock()
    interaction.user.id = user_id
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    return interaction


# ---------------------------------------------------------------------------
# /claim
# ---------------------------------------------------------------------------


class TestClaimCommand:
    @pytest.mark.asyncio
    async def test_claim_success(self):
        """Valid emoji, user has <3 claims -> success embed."""
        state: dict = {}
        interaction = _make_interaction(user_id=1001)
        await claim_callback(interaction, "🐉", state)
        interaction.response.send_message.assert_called_once()
        embed = interaction.response.send_message.call_args[1]["embed"]
        assert isinstance(embed, discord.Embed)
        assert embed.color == discord.Color.green()
        assert "🐉" in embed.description
        assert state == {"🐉": "1001"}

    @pytest.mark.asyncio
    async def test_claim_already_taken(self):
        """Emoji owned by another user -> error response."""
        state = {"🐉": "9999"}
        interaction = _make_interaction(user_id=1001)
        await claim_callback(interaction, "🐉", state)
        embed = interaction.response.send_message.call_args[1]["embed"]
        assert embed.color == discord.Color.red()
        assert state == {"🐉": "9999"}

    @pytest.mark.asyncio
    async def test_claim_user_limit(self):
        """User already has 3 claims -> error response."""
        state = {"🐉": "1001", "🦊": "1001", "🐍": "1001"}
        interaction = _make_interaction(user_id=1001)
        await claim_callback(interaction, "🎯", state)
        embed = interaction.response.send_message.call_args[1]["embed"]
        assert embed.color == discord.Color.red()
        assert "🎯" not in state

    @pytest.mark.asyncio
    async def test_claim_own_emoji_again(self):
        """User tries to claim emoji they already own -> error."""
        state = {"🐉": "1001"}
        interaction = _make_interaction(user_id=1001)
        await claim_callback(interaction, "🐉", state)
        embed = interaction.response.send_message.call_args[1]["embed"]
        assert embed.color == discord.Color.red()


# ---------------------------------------------------------------------------
# /unclaim
# ---------------------------------------------------------------------------


class TestUnclaimCommand:
    @pytest.mark.asyncio
    async def test_unclaim_success(self):
        """User owns emoji -> releases it, success response."""
        state = {"🐉": "1001"}
        interaction = _make_interaction(user_id=1001)
        await unclaim_callback(interaction, "🐉", state)
        embed = interaction.response.send_message.call_args[1]["embed"]
        assert embed.color == discord.Color.green()
        assert "🐉" not in state

    @pytest.mark.asyncio
    async def test_unclaim_not_owned(self):
        """User doesn't own that emoji -> error response."""
        state = {"🐉": "9999"}
        interaction = _make_interaction(user_id=1001)
        await unclaim_callback(interaction, "🐉", state)
        embed = interaction.response.send_message.call_args[1]["embed"]
        assert embed.color == discord.Color.red()
        assert state == {"🐉": "9999"}


# ---------------------------------------------------------------------------
# /roster
# ---------------------------------------------------------------------------


class TestRosterCommand:
    @pytest.mark.asyncio
    async def test_roster_empty(self):
        """No claims -> embed says no claims yet."""
        state: dict = {}
        interaction = _make_interaction()
        await roster_callback(interaction, state)
        embed = interaction.response.send_message.call_args[1]["embed"]
        assert isinstance(embed, discord.Embed)
        assert "no" in embed.description.lower() or "empty" in embed.description.lower()

    @pytest.mark.asyncio
    async def test_roster_with_claims(self):
        """Two claims -> embed lists them."""
        state = {"🐉": "1001", "🦊": "2002"}
        interaction = _make_interaction()
        await roster_callback(interaction, state)
        embed = interaction.response.send_message.call_args[1]["embed"]
        assert "🐉" in embed.description
        assert "🦊" in embed.description
        assert "1001" in embed.description
        assert "2002" in embed.description


# ---------------------------------------------------------------------------
# register_commands
# ---------------------------------------------------------------------------


class TestRegisterCommands:
    def test_register_commands_callable(self):
        """register_commands is importable and callable."""
        assert callable(register_commands)
