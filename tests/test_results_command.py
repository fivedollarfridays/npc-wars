"""Tests for /results Discord slash command."""

import discord
import pytest
from unittest.mock import patch

from tests.conftest import make_mock_interaction

MATCH = {
    "match_id": 1,
    "winner": "\U0001f986",
    "duration_rounds": 42,
    "seed": 99,
    "players": [
        {"name": "DuckBot", "emoji": "\U0001f986", "bio": "quack", "author": "alice"},
        {"name": "GooseBot", "emoji": "\U0001fab3", "bio": "honk", "author": "bob"},
    ],
    "eliminations": [
        {"round": 10, "emoji": "\U0001fab3", "cause": "attack", "killed_by": "\U0001f986"},
    ],
    "rounds": [],
}


# ---------------------------------------------------------------------------
# results_callback
# ---------------------------------------------------------------------------


class TestResultsCallback:
    @pytest.mark.asyncio
    async def test_results_callback_latest_match(self):
        """No match_id given -> loads latest match, sends embed with winner."""
        from discord_bot.commands.results import results_callback

        interaction = make_mock_interaction()
        with patch("discord_bot.commands.results.get_latest_match", return_value=MATCH) as mock_latest, \
             patch("discord_bot.commands.results.get_match") as mock_get:
            await results_callback(interaction, "/fake/results")
            mock_latest.assert_called_once_with("/fake/results")
            mock_get.assert_not_called()
        interaction.response.send_message.assert_called_once()
        embed = interaction.response.send_message.call_args[1]["embed"]
        assert isinstance(embed, discord.Embed)
        assert "\U0001f986" in embed.description

    @pytest.mark.asyncio
    async def test_results_callback_specific_match(self):
        """match_id=1 -> loads that match, shows it."""
        from discord_bot.commands.results import results_callback

        interaction = make_mock_interaction()
        with patch("discord_bot.commands.results.get_match", return_value=MATCH) as mock_get, \
             patch("discord_bot.commands.results.get_latest_match") as mock_latest:
            await results_callback(interaction, "/fake/results", match_id=1)
            mock_get.assert_called_once_with("/fake/results", 1)
            mock_latest.assert_not_called()
        embed = interaction.response.send_message.call_args[1]["embed"]
        assert isinstance(embed, discord.Embed)

    @pytest.mark.asyncio
    async def test_results_callback_no_matches(self):
        """results_dir has no matches -> 'no matches found' response."""
        from discord_bot.commands.results import results_callback

        interaction = make_mock_interaction()
        with patch("discord_bot.commands.results.get_latest_match", return_value=None):
            await results_callback(interaction, "/fake/results")
        msg = interaction.response.send_message.call_args[0][0]
        assert "no matches" in msg.lower() or "No matches" in msg

    @pytest.mark.asyncio
    async def test_results_callback_invalid_id(self):
        """match_id that doesn't exist -> 'match not found' response."""
        from discord_bot.commands.results import results_callback

        interaction = make_mock_interaction()
        with patch("discord_bot.commands.results.get_match", return_value=None):
            await results_callback(interaction, "/fake/results", match_id=999)
        msg = interaction.response.send_message.call_args[0][0]
        assert "not found" in msg.lower()


# ---------------------------------------------------------------------------
# build_results_embed
# ---------------------------------------------------------------------------


class TestBuildResultsEmbed:
    def test_build_results_embed_has_winner(self):
        """Embed title/desc contains winner emoji."""
        from discord_bot.commands.results import build_results_embed

        embed = build_results_embed(MATCH)
        assert "\U0001f986" in embed.description
        assert "Match #1" in embed.title

    def test_build_results_embed_has_placements(self):
        """Embed field lists bots by placement."""
        from discord_bot.commands.results import build_results_embed

        embed = build_results_embed(MATCH)
        fields = {f.name: f.value for f in embed.fields}
        assert "Placements" in fields
        placement_text = fields["Placements"]
        # Winner should be first
        assert placement_text.startswith("1.")
        assert "\U0001f986" in placement_text
        assert "\U0001fab3" in placement_text

    def test_build_results_embed_has_duration(self):
        """Rounds count appears in embed."""
        from discord_bot.commands.results import build_results_embed

        embed = build_results_embed(MATCH)
        fields = {f.name: f.value for f in embed.fields}
        assert "Duration" in fields
        assert "42" in fields["Duration"]
