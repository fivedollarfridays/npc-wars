"""Tests for Discord match announcements and challenge command."""

import discord
import pytest
from unittest.mock import AsyncMock, MagicMock


# ---------------------------------------------------------------------------
# Sample match data
# ---------------------------------------------------------------------------

def _sample_match() -> dict:
    return {
        "match_id": 42,
        "winner": "A",
        "duration_rounds": 15,
        "players": [
            {"name": "AlphaBot", "emoji": "A"},
            {"name": "BetaBot", "emoji": "B"},
        ],
        "eliminations": [
            {"round": 5, "emoji": "B", "killed_by": "AlphaBot"},
        ],
        "stats": {
            "AlphaBot": {"kills": 3, "damage_dealt": 120},
            "BetaBot": {"kills": 1, "damage_dealt": 80},
        },
    }


# ---------------------------------------------------------------------------
# build_match_embed
# ---------------------------------------------------------------------------

class TestBuildMatchEmbed:
    def test_returns_discord_embed(self):
        from discord_bot.commands.announce import build_match_embed
        embed = build_match_embed(_sample_match())
        assert isinstance(embed, discord.Embed)

    def test_title_contains_match_id(self):
        from discord_bot.commands.announce import build_match_embed
        embed = build_match_embed(_sample_match())
        assert "42" in embed.title

    def test_description_contains_winner_name(self):
        from discord_bot.commands.announce import build_match_embed
        embed = build_match_embed(_sample_match())
        assert "AlphaBot" in embed.description

    def test_description_contains_round_count(self):
        from discord_bot.commands.announce import build_match_embed
        embed = build_match_embed(_sample_match())
        assert "15" in embed.description

    def test_has_gold_color(self):
        from discord_bot.commands.announce import build_match_embed
        embed = build_match_embed(_sample_match())
        assert embed.color == discord.Color.gold()

    def test_kill_feed_field_present(self):
        from discord_bot.commands.announce import build_match_embed
        embed = build_match_embed(_sample_match())
        field_names = [f.name for f in embed.fields]
        assert "Kill Feed" in field_names

    def test_most_kills_field_present(self):
        from discord_bot.commands.announce import build_match_embed
        embed = build_match_embed(_sample_match())
        field_names = [f.name for f in embed.fields]
        assert "Most Kills" in field_names

    def test_most_damage_field_present(self):
        from discord_bot.commands.announce import build_match_embed
        embed = build_match_embed(_sample_match())
        field_names = [f.name for f in embed.fields]
        assert "Most Damage" in field_names


class TestBuildMatchEmbedEdgeCases:
    def test_empty_stats(self):
        from discord_bot.commands.announce import build_match_embed
        data = _sample_match()
        data["stats"] = {}
        embed = build_match_embed(data)
        assert isinstance(embed, discord.Embed)
        # No Most Kills/Damage fields when stats empty
        field_names = [f.name for f in embed.fields]
        assert "Most Kills" not in field_names

    def test_no_eliminations(self):
        from discord_bot.commands.announce import build_match_embed
        data = _sample_match()
        data["eliminations"] = []
        embed = build_match_embed(data)
        field_names = [f.name for f in embed.fields]
        assert "Kill Feed" not in field_names

    def test_replay_link_when_server_url(self):
        from discord_bot.commands.announce import build_match_embed
        embed = build_match_embed(_sample_match(), server_url="https://example.com")
        field_names = [f.name for f in embed.fields]
        assert "Watch Replay" in field_names
        replay_field = next(f for f in embed.fields if f.name == "Watch Replay")
        assert "https://example.com/m/42" in replay_field.value

    def test_no_replay_link_without_server_url(self):
        from discord_bot.commands.announce import build_match_embed
        embed = build_match_embed(_sample_match())
        field_names = [f.name for f in embed.fields]
        assert "Watch Replay" not in field_names

    def test_winner_fallback_when_no_matching_player(self):
        from discord_bot.commands.announce import build_match_embed
        data = _sample_match()
        data["winner"] = "Z"
        data["players"] = []
        embed = build_match_embed(data)
        assert "Z" in embed.description


# ---------------------------------------------------------------------------
# announce_match
# ---------------------------------------------------------------------------

class TestAnnounceMatch:
    @pytest.mark.asyncio
    async def test_sends_embed_to_channel(self):
        from discord_bot.commands.announce import announce_match
        bot = MagicMock()
        channel = MagicMock()
        channel.send = AsyncMock()
        bot.get_channel = MagicMock(return_value=channel)

        await announce_match(bot, 12345, _sample_match())
        channel.send.assert_called_once()
        kwargs = channel.send.call_args
        assert kwargs[1].get("embed") is not None or (
            kwargs[0] and isinstance(kwargs[0][0], discord.Embed)
        )

    @pytest.mark.asyncio
    async def test_handles_missing_channel(self):
        from discord_bot.commands.announce import announce_match
        bot = MagicMock()
        bot.get_channel = MagicMock(return_value=None)

        # Should not raise
        await announce_match(bot, 99999, _sample_match())


# ---------------------------------------------------------------------------
# challenge command
# ---------------------------------------------------------------------------

class TestChallengeCommand:
    def test_challenge_module_exists(self):
        from discord_bot.commands import challenge  # noqa: F401

    def test_register_commands_callable(self):
        from discord_bot.commands.challenge import register_commands
        assert callable(register_commands)

    @pytest.mark.asyncio
    async def test_challenge_callback_sends_embed(self):
        from discord_bot.commands.challenge import challenge_callback
        interaction = MagicMock()
        interaction.user = MagicMock()
        interaction.user.mention = "@challenger"
        interaction.response = MagicMock()
        interaction.response.send_message = AsyncMock()

        opponent = MagicMock()
        opponent.mention = "@opponent"

        await challenge_callback(interaction, opponent)
        interaction.response.send_message.assert_called_once()
        kwargs = interaction.response.send_message.call_args
        embed = kwargs[1].get("embed") if kwargs[1] else None
        assert embed is not None
        assert "@challenger" in embed.description
        assert "@opponent" in embed.description
