"""Tests for TV Discord channel posting logic."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from discord_bot.commands.tv_posting import get_tv_channel_id, post_match_tv


# ---------------------------------------------------------------------------
# Sample data builders
# ---------------------------------------------------------------------------

def _ks_episode() -> dict:
    return {
        "metadata": {"game": "kill_switch", "winner": "A", "participants": ["A", "B", "C"]},
        "cold_open": {"text": "Previously on Agent Grounds...", "rivalries": []},
        "pre_match": {"intros": []},
        "match_commentary": {"lines": []},
        "post_match": {
            "winner": "A",
            "stat_diffs": [
                {"emoji": "A", "kills": 3, "damage_dealt": 150, "damage_taken": 50},
                {"emoji": "B", "kills": 1, "damage_dealt": 80, "damage_taken": 120},
            ],
            "highlights": [
                {"round": 5, "trigger_type": "kill", "participants": ["A", "B"],
                 "drama_score": 8},
            ],
            "standings": [
                {"participant": "A", "points": 45, "tier": "Diamond"},
                {"participant": "B", "points": 30, "tier": "Gold"},
            ],
        },
    }


def _cc_episode() -> dict:
    return {
        "metadata": {
            "game": "code_circuit", "winner": "FastCar",
            "participants": ["FastCar", "SlowCar"],
        },
        "cold_open": {"text": "A fresh start...", "rivalries": []},
        "pre_match": {"intros": []},
        "match_commentary": {"lines": []},
        "post_match": {
            "winner": "FastCar",
            "stat_diffs": [
                {"emoji": "FastCar", "position": 1, "fastest_lap": True},
                {"emoji": "SlowCar", "position": 2, "fastest_lap": False},
            ],
            "highlights": [
                {"round": 10, "trigger_type": "overtake",
                 "participants": ["FastCar", "SlowCar"], "drama_score": 6},
            ],
            "standings": [
                {"participant": "FastCar", "points": 25, "tier": "Diamond"},
            ],
        },
    }


def _watcher_dossiers() -> dict:
    return {
        "A": {
            "player_id": "A", "sync_score": 65.3, "predictability_change": 0.72,
            "predictions": [{"context": "low_hp",
                             "actions": [{"action": "rest", "probability": 0.6}],
                             "counter": "attack"}],
            "text_summary": "Dossier: A\nSync: 65.3%",
        },
    }


def _config() -> dict:
    return {"ks_tv_channel_id": 111, "cc_tv_channel_id": 222}


def _mock_channel():
    channel = MagicMock()
    main_msg = MagicMock(id=1001)
    thread = MagicMock()
    thread.send = AsyncMock()
    main_msg.create_thread = AsyncMock(return_value=thread)
    channel.send = AsyncMock(return_value=main_msg)
    return channel, main_msg, thread


# ---------------------------------------------------------------------------
# get_tv_channel_id
# ---------------------------------------------------------------------------

class TestGetTvChannelId:
    def test_kill_switch_channel(self) -> None:
        assert get_tv_channel_id("kill_switch", _config()) == 111

    def test_code_circuit_channel(self) -> None:
        assert get_tv_channel_id("code_circuit", _config()) == 222

    def test_unknown_game_returns_none(self) -> None:
        assert get_tv_channel_id("unknown_game", _config()) is None


# ---------------------------------------------------------------------------
# post_match_tv — KS posting
# ---------------------------------------------------------------------------

class TestPostMatchTvKillSwitch:
    @pytest.mark.asyncio
    async def test_posts_video_to_channel(self, tmp_path) -> None:
        mp4 = tmp_path / "match.mp4"
        mp4.write_bytes(b"\x00" * 100)

        bot = MagicMock()
        channel, _, _ = _mock_channel()
        bot.get_channel = MagicMock(return_value=channel)

        await post_match_tv(bot, _ks_episode(), str(mp4), _config())
        first_call = channel.send.call_args_list[0]
        assert "file" in first_call.kwargs

    @pytest.mark.asyncio
    async def test_sends_thread_reply(self, tmp_path) -> None:
        mp4 = tmp_path / "match.mp4"
        mp4.write_bytes(b"\x00" * 100)

        bot = MagicMock()
        channel, main_msg, thread = _mock_channel()
        bot.get_channel = MagicMock(return_value=channel)

        await post_match_tv(bot, _ks_episode(), str(mp4), _config())
        main_msg.create_thread.assert_called_once()
        assert thread.send.call_count >= 1

    @pytest.mark.asyncio
    async def test_ks_thread_includes_watcher_dossier(self, tmp_path) -> None:
        mp4 = tmp_path / "match.mp4"
        mp4.write_bytes(b"\x00" * 100)

        bot = MagicMock()
        channel, _, thread = _mock_channel()
        bot.get_channel = MagicMock(return_value=channel)

        ep = _ks_episode()
        ep["watcher_dossiers"] = _watcher_dossiers()
        await post_match_tv(bot, ep, str(mp4), _config())

        # Stats + watcher dossier = 2 thread sends
        assert thread.send.call_count == 2

    @pytest.mark.asyncio
    async def test_missing_channel_skips(self) -> None:
        bot = MagicMock()
        bot.get_channel = MagicMock(return_value=None)
        await post_match_tv(bot, _ks_episode(), "/tmp/match.mp4", _config())


# ---------------------------------------------------------------------------
# post_match_tv — CC posting
# ---------------------------------------------------------------------------

class TestPostMatchTvCodeCircuit:
    @pytest.mark.asyncio
    async def test_posts_to_cc_channel(self, tmp_path) -> None:
        mp4 = tmp_path / "race.mp4"
        mp4.write_bytes(b"\x00" * 100)

        bot = MagicMock()
        channel, _, _ = _mock_channel()
        bot.get_channel = MagicMock(return_value=channel)

        await post_match_tv(bot, _cc_episode(), str(mp4), _config())
        bot.get_channel.assert_called_with(222)

    @pytest.mark.asyncio
    async def test_cc_no_watcher_dossier_in_thread(self, tmp_path) -> None:
        mp4 = tmp_path / "race.mp4"
        mp4.write_bytes(b"\x00" * 100)

        bot = MagicMock()
        channel, _, thread = _mock_channel()
        bot.get_channel = MagicMock(return_value=channel)

        await post_match_tv(bot, _cc_episode(), str(mp4), _config())
        assert thread.send.call_count == 1


# ---------------------------------------------------------------------------
# Large video handling (>25MB)
# ---------------------------------------------------------------------------

class TestLargeVideoHandling:
    @pytest.mark.asyncio
    async def test_large_video_no_file_attachment(self) -> None:
        bot = MagicMock()
        channel, _, _ = _mock_channel()
        bot.get_channel = MagicMock(return_value=channel)

        with patch("os.path.getsize", return_value=26 * 1024 * 1024):
            await post_match_tv(bot, _ks_episode(), "/tmp/big.mp4", _config())

        first_call = channel.send.call_args_list[0]
        assert "file" not in first_call.kwargs

    @pytest.mark.asyncio
    async def test_large_video_still_sends_embed(self) -> None:
        bot = MagicMock()
        channel, _, _ = _mock_channel()
        bot.get_channel = MagicMock(return_value=channel)

        with patch("os.path.getsize", return_value=30 * 1024 * 1024):
            await post_match_tv(bot, _ks_episode(), "/tmp/big.mp4", _config())

        first_call = channel.send.call_args_list[0]
        assert "embed" in first_call.kwargs
