"""Tests for /leaderboard Discord slash command."""

import discord
import pytest
from unittest.mock import AsyncMock, MagicMock

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

STATS = {
    "\U0001f986": {
        "wins": 5, "losses": 2, "kills": 12, "damage_dealt": 450,
        "damage_taken": 200, "matches_played": 7,
        "win_rate": 0.71, "avg_placement": 1.4, "_placement_sum": 9.8,
    },
    "\U0001fab3": {
        "wins": 3, "losses": 4, "kills": 8, "damage_dealt": 280,
        "damage_taken": 320, "matches_played": 7,
        "win_rate": 0.43, "avg_placement": 2.1, "_placement_sum": 14.7,
    },
}

MATCH_DATA = {
    "match_id": 1,
    "date": "2026-03-01",
    "winner": "\U0001f986",
    "seed": 42,
    "duration_rounds": 30,
    "players": [
        {"name": "DuckBot", "emoji": "\U0001f986", "bio": "quack", "author": "alice"},
        {"name": "GooseBot", "emoji": "\U0001fab3", "bio": "honk", "author": "bob"},
    ],
    "eliminations": [
        {"round": 25, "emoji": "\U0001fab3", "cause": "attack", "killed_by": "\U0001f986"},
    ],
    "rounds": [],
    "stats": {
        "\U0001f986": {"kills": 12, "damage_dealt": 450, "damage_taken": 200},
        "\U0001fab3": {"kills": 8, "damage_dealt": 280, "damage_taken": 320},
    },
}


def _make_interaction() -> MagicMock:
    """Create a mock Discord interaction."""
    interaction = MagicMock(spec=discord.Interaction)
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    return interaction


def _many_rankings(n: int) -> list[dict]:
    """Generate n ranking entries for pagination tests."""
    return [
        {"emoji": f"bot_{i}", "wins": n - i, "kills": (n - i) * 2,
         "losses": i, "damage_dealt": 100, "win_rate": 0.5,
         "avg_placement": 2.0, "matches_played": 10}
        for i in range(n)
    ]


# ---------------------------------------------------------------------------
# build_leaderboard_embed
# ---------------------------------------------------------------------------


class TestBuildLeaderboardEmbed:
    def test_shows_rankings_in_order(self):
        """Embed lists bots in rank order with stats."""
        from data.leaderboard import get_rankings
        from discord_bot.commands.leaderboard import build_leaderboard_embed

        rankings = get_rankings(STATS, sort_by="wins")
        embed = build_leaderboard_embed(rankings, page=1, sort_by="wins")

        assert isinstance(embed, discord.Embed)
        lines = embed.description.split("\n")
        assert len(lines) == 2
        # Duck has more wins, should be first
        assert "\U0001f986" in lines[0]
        assert "\U0001fab3" in lines[1]
        assert lines[0].startswith("1.")
        assert lines[1].startswith("2.")

    def test_shows_page_info(self):
        """Footer shows 'Page 1/N'."""
        from data.leaderboard import get_rankings
        from discord_bot.commands.leaderboard import build_leaderboard_embed

        rankings = get_rankings(STATS, sort_by="wins")
        embed = build_leaderboard_embed(rankings, page=1, sort_by="wins")
        assert embed.footer.text == "Page 1/1"

    def test_page_2_shows_bots_11_to_20(self):
        """Passing page=2 shows bots 11-20."""
        from discord_bot.commands.leaderboard import build_leaderboard_embed

        rankings = _many_rankings(25)
        embed = build_leaderboard_embed(rankings, page=2, sort_by="wins")

        lines = embed.description.split("\n")
        assert len(lines) == 10
        # First line on page 2 should start with "11."
        assert lines[0].startswith("11.")
        assert lines[9].startswith("20.")
        assert embed.footer.text == "Page 2/3"

    def test_empty_stats(self):
        """No stats -> embed says 'No data yet'."""
        from discord_bot.commands.leaderboard import build_leaderboard_embed

        embed = build_leaderboard_embed([], page=1, sort_by="wins")
        assert "No data yet" in embed.description
        assert embed.footer.text == "Page 1/1"

    def test_page_beyond_range_clamps_to_last(self):
        """Page beyond total pages clamps to last page."""
        from discord_bot.commands.leaderboard import build_leaderboard_embed

        rankings = _many_rankings(5)
        embed = build_leaderboard_embed(rankings, page=99, sort_by="wins")
        assert embed.footer.text == "Page 1/1"
        assert "bot_0" in embed.description


# ---------------------------------------------------------------------------
# leaderboard_callback
# ---------------------------------------------------------------------------


class TestLeaderboardCallback:
    @pytest.mark.asyncio
    async def test_no_matches_response(self):
        """Empty match_data_list -> 'No match data' response."""
        from discord_bot.commands.leaderboard import leaderboard_callback

        interaction = _make_interaction()
        await leaderboard_callback(
            interaction, "/fake/results", match_data_list=[],
        )
        msg = interaction.response.send_message.call_args[0][0]
        assert "No match data" in msg

    @pytest.mark.asyncio
    async def test_default_sort_sends_embed(self):
        """Default sort (wins) sends an embed with rankings."""
        from discord_bot.commands.leaderboard import leaderboard_callback

        interaction = _make_interaction()
        await leaderboard_callback(
            interaction, "/fake/results",
            match_data_list=[MATCH_DATA],
        )
        call_kwargs = interaction.response.send_message.call_args[1]
        embed = call_kwargs["embed"]
        assert isinstance(embed, discord.Embed)
        assert "by wins" in embed.title
        # Duck won, should appear first
        assert "\U0001f986" in embed.description

    @pytest.mark.asyncio
    async def test_sort_by_kills(self):
        """sort_by='kills' works and title reflects it."""
        from discord_bot.commands.leaderboard import leaderboard_callback

        interaction = _make_interaction()
        await leaderboard_callback(
            interaction, "/fake/results",
            sort_by="kills",
            match_data_list=[MATCH_DATA],
        )
        call_kwargs = interaction.response.send_message.call_args[1]
        embed = call_kwargs["embed"]
        assert "by kills" in embed.title
