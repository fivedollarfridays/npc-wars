"""Tests for discord_bot.announcements — match start/end embeds and sending."""

from unittest.mock import AsyncMock

import discord
import pytest

from discord_bot.announcements import (
    announce_match_end,
    announce_match_start,
    build_match_end_embed,
    build_match_start_embed,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_PLAYERS = [
    {"name": "AlphaBot", "emoji": "\U0001f600", "bio": "Grins a lot", "author": "alice"},
    {"name": "BravoBot", "emoji": "\U0001f525", "bio": "On fire", "author": "bob"},
    {"name": "CharlieBot", "emoji": "\U0001f47b", "bio": "Spooky", "author": "carol"},
]

SAMPLE_ELIMINATIONS = [
    {"round": 3, "emoji": "\U0001f47b", "cause": "melee", "killed_by": "\U0001f600"},
    {"round": 5, "emoji": "\U0001f525", "cause": "storm", "killed_by": "storm"},
    {"round": 7, "emoji": "\U0001f600", "cause": "melee", "killed_by": "\U0001f47b"},
]

SAMPLE_MATCH_DATA: dict = {
    "match_id": 42,
    "winner": "\U0001f600",
    "players": SAMPLE_PLAYERS,
    "eliminations": SAMPLE_ELIMINATIONS,
    "duration_rounds": 7,
    "seed": 12345,
    "date": "2026-03-12T00:00:00+00:00",
    "grid_size": 10,
    "rounds": [],
    "stats": {},
}


# ---------------------------------------------------------------------------
# build_match_start_embed
# ---------------------------------------------------------------------------


class TestBuildMatchStartEmbed:
    """Tests for the match-start embed builder."""

    def test_has_title_with_match_id(self) -> None:
        embed = build_match_start_embed(42, SAMPLE_PLAYERS, seed=99)
        assert embed.title is not None
        assert "42" in embed.title

    def test_lists_player_emojis(self) -> None:
        embed = build_match_start_embed(1, SAMPLE_PLAYERS, seed=None)
        # All player emojis must appear somewhere in the embed fields
        field_values = " ".join(f.value for f in embed.fields)
        for player in SAMPLE_PLAYERS:
            assert player["emoji"] in field_values

    def test_shows_seed_when_provided(self) -> None:
        embed = build_match_start_embed(1, SAMPLE_PLAYERS, seed=12345)
        field_text = " ".join(f"{f.name} {f.value}" for f in embed.fields)
        assert "12345" in field_text

    def test_omits_seed_when_none(self) -> None:
        embed = build_match_start_embed(1, SAMPLE_PLAYERS, seed=None)
        field_names = [f.name for f in embed.fields]
        assert "Seed" not in field_names


# ---------------------------------------------------------------------------
# build_match_end_embed
# ---------------------------------------------------------------------------


class TestBuildMatchEndEmbed:
    """Tests for the match-end embed builder."""

    def test_has_winner_emoji(self) -> None:
        embed = build_match_end_embed(SAMPLE_MATCH_DATA)
        assert embed.description is not None
        assert SAMPLE_MATCH_DATA["winner"] in embed.description

    def test_shows_duration_rounds(self) -> None:
        embed = build_match_end_embed(SAMPLE_MATCH_DATA)
        field_text = " ".join(f"{f.name} {f.value}" for f in embed.fields)
        assert "7" in field_text

    def test_lists_eliminations(self) -> None:
        embed = build_match_end_embed(SAMPLE_MATCH_DATA)
        field_text = " ".join(f.value for f in embed.fields)
        # At least the last 3 eliminations should appear
        for elim in SAMPLE_ELIMINATIONS[-3:]:
            assert elim["emoji"] in field_text


# ---------------------------------------------------------------------------
# Async announce functions
# ---------------------------------------------------------------------------


class TestAnnounceSending:
    """Tests for the async announce helpers that send embeds to a channel."""

    @pytest.mark.asyncio
    async def test_announce_match_start_sends_embed(self) -> None:
        channel = AsyncMock(spec=discord.TextChannel)
        await announce_match_start(channel, 42, SAMPLE_PLAYERS, seed=99)
        channel.send.assert_awaited_once()
        _, kwargs = channel.send.call_args
        assert isinstance(kwargs["embed"], discord.Embed)

    @pytest.mark.asyncio
    async def test_announce_match_end_sends_embed(self) -> None:
        channel = AsyncMock(spec=discord.TextChannel)
        await announce_match_end(channel, SAMPLE_MATCH_DATA)
        channel.send.assert_awaited_once()
        _, kwargs = channel.send.call_args
        assert isinstance(kwargs["embed"], discord.Embed)
