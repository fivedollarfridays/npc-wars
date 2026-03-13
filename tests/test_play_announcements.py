"""Tests for engine.discord_integration — wiring announcements into match runner."""

import os
from typing import Any
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_PLAYERS: list[dict[str, Any]] = [
    {"name": "AlphaBot", "emoji": "\U0001f600", "bio": "Grins", "author": "alice"},
    {"name": "BravoBot", "emoji": "\U0001f525", "bio": "Fire", "author": "bob"},
]

SAMPLE_MATCH_DATA: dict[str, Any] = {
    "match_id": 1,
    "winner": "\U0001f600",
    "players": SAMPLE_PLAYERS,
    "eliminations": [],
    "duration_rounds": 5,
    "seed": 42,
    "grid_size": 8,
    "rounds": [],
    "stats": {},
}


# ---------------------------------------------------------------------------
# notify_match_start / notify_match_end — graceful degradation
# ---------------------------------------------------------------------------


class TestGracefulDegradation:
    """Announcements skip silently when discord is not available."""

    def test_notify_start_noop_when_discord_missing(self) -> None:
        """No crash when discord.py is not installed."""
        with patch.dict("sys.modules", {"discord": None}):
            # Re-import to pick up the missing module
            import importlib
            import engine.discord_integration as mod
            importlib.reload(mod)
            # Should return without error
            mod.notify_match_start(match_id=1, players=SAMPLE_PLAYERS, seed=42)

    def test_notify_end_noop_when_discord_missing(self) -> None:
        """No crash when discord.py is not installed."""
        with patch.dict("sys.modules", {"discord": None}):
            import importlib
            import engine.discord_integration as mod
            importlib.reload(mod)
            mod.notify_match_end(SAMPLE_MATCH_DATA)

    def test_notify_start_noop_when_no_bot_token(self) -> None:
        """Skip silently when BOT_TOKEN env var is not set."""
        from engine.discord_integration import _reset_cache, notify_match_start
        _reset_cache()
        env = {k: v for k, v in os.environ.items() if k != "BOT_TOKEN"}
        with patch.dict(os.environ, env, clear=True):
            notify_match_start(match_id=1, players=SAMPLE_PLAYERS, seed=42)

    def test_notify_end_noop_when_no_bot_token(self) -> None:
        """Skip silently when BOT_TOKEN env var is not set."""
        from engine.discord_integration import _reset_cache, notify_match_end
        _reset_cache()
        env = {k: v for k, v in os.environ.items() if k != "BOT_TOKEN"}
        with patch.dict(os.environ, env, clear=True):
            notify_match_end(SAMPLE_MATCH_DATA)

    def test_notify_start_noop_when_no_channel_id(self) -> None:
        """Skip silently when ANNOUNCEMENT_CHANNEL_ID is not set."""
        from engine.discord_integration import _reset_cache, notify_match_start
        _reset_cache()
        env = {"BOT_TOKEN": "fake-token"}
        with patch.dict(os.environ, env, clear=True):
            notify_match_start(match_id=1, players=SAMPLE_PLAYERS, seed=42)

    def test_notify_end_noop_when_no_channel_id(self) -> None:
        """Skip silently when ANNOUNCEMENT_CHANNEL_ID is not set."""
        from engine.discord_integration import _reset_cache, notify_match_end
        _reset_cache()
        env = {"BOT_TOKEN": "fake-token"}
        with patch.dict(os.environ, env, clear=True):
            notify_match_end(SAMPLE_MATCH_DATA)


# ---------------------------------------------------------------------------
# notify_match_start / notify_match_end — calls announcements when configured
# ---------------------------------------------------------------------------


class TestAnnouncementsWired:
    """When discord is available and env is configured, announcements fire."""

    def test_notify_start_calls_dispatch(self) -> None:
        """_dispatch_start is called via _safe_announce with correct params."""
        from engine.discord_integration import _reset_cache
        _reset_cache()
        with (
            patch.dict(os.environ, {"BOT_TOKEN": "tok", "ANNOUNCEMENT_CHANNEL_ID": "123"}),
            patch("engine.discord_integration._dispatch_start") as mock_dispatch,
        ):
            from engine.discord_integration import notify_match_start
            notify_match_start(match_id=1, players=SAMPLE_PLAYERS, seed=42)
            mock_dispatch.assert_called_once_with(123, 1, SAMPLE_PLAYERS, 42)

    def test_notify_end_calls_dispatch(self) -> None:
        """_dispatch_end is called via _safe_announce with correct params."""
        from engine.discord_integration import _reset_cache
        _reset_cache()
        with (
            patch.dict(os.environ, {"BOT_TOKEN": "tok", "ANNOUNCEMENT_CHANNEL_ID": "123"}),
            patch("engine.discord_integration._dispatch_end") as mock_dispatch,
        ):
            from engine.discord_integration import notify_match_end
            notify_match_end(SAMPLE_MATCH_DATA)
            mock_dispatch.assert_called_once_with(123, SAMPLE_MATCH_DATA)

    def test_notify_start_swallows_exceptions(self) -> None:
        """Any exception during announcement is swallowed, not raised."""
        from engine.discord_integration import _reset_cache
        _reset_cache()
        with (
            patch.dict(os.environ, {"BOT_TOKEN": "tok", "ANNOUNCEMENT_CHANNEL_ID": "123"}),
            patch("engine.discord_integration._dispatch_start", side_effect=RuntimeError("boom")),
        ):
            from engine.discord_integration import notify_match_start
            notify_match_start(match_id=1, players=SAMPLE_PLAYERS, seed=42)

    def test_notify_end_swallows_exceptions(self) -> None:
        """Any exception during announcement is swallowed, not raised."""
        from engine.discord_integration import _reset_cache
        _reset_cache()
        with (
            patch.dict(os.environ, {"BOT_TOKEN": "tok", "ANNOUNCEMENT_CHANNEL_ID": "123"}),
            patch("engine.discord_integration._dispatch_end", side_effect=RuntimeError("boom")),
        ):
            from engine.discord_integration import notify_match_end
            notify_match_end(SAMPLE_MATCH_DATA)


# ---------------------------------------------------------------------------
# Integration: run_match calls notifications
# ---------------------------------------------------------------------------


class TestRunMatchIntegration:
    """run_match in engine/game.py calls notify_match_start/end."""

    def test_run_match_calls_notify_start_and_end(self) -> None:
        """run_match triggers both notification hooks."""
        with (
            patch("engine.game.notify_match_start") as mock_start,
            patch("engine.game.notify_match_end") as mock_end,
        ):
            from engine.game import run_match
            # Minimal bot configs for a quick match
            configs = [
                {"name": "A", "emoji": "A", "bio": "", "author": "x",
                 "decide_func": lambda state: ("rest",)},
                {"name": "B", "emoji": "B", "bio": "", "author": "x",
                 "decide_func": lambda state: ("rest",)},
            ]
            run_match(configs, match_id=1, seed=99)
            mock_start.assert_called_once()
            mock_end.assert_called_once()

    def test_run_match_passes_correct_params_to_notify_start(self) -> None:
        """notify_match_start receives match_id, players, and seed."""
        with (
            patch("engine.game.notify_match_start") as mock_start,
            patch("engine.game.notify_match_end"),
        ):
            from engine.game import run_match
            configs = [
                {"name": "A", "emoji": "A", "bio": "", "author": "x",
                 "decide_func": lambda state: ("rest",)},
                {"name": "B", "emoji": "B", "bio": "", "author": "x",
                 "decide_func": lambda state: ("rest",)},
            ]
            run_match(configs, match_id=7, seed=123)
            call_kwargs = mock_start.call_args
            # Check match_id, players list, and seed
            assert call_kwargs.kwargs.get("match_id") == 7 or call_kwargs[1].get("match_id") == 7

    def test_run_match_passes_match_data_to_notify_end(self) -> None:
        """notify_match_end receives the full match data dict."""
        with (
            patch("engine.game.notify_match_start"),
            patch("engine.game.notify_match_end") as mock_end,
        ):
            from engine.game import run_match
            configs = [
                {"name": "A", "emoji": "A", "bio": "", "author": "x",
                 "decide_func": lambda state: ("rest",)},
                {"name": "B", "emoji": "B", "bio": "", "author": "x",
                 "decide_func": lambda state: ("rest",)},
            ]
            result = run_match(configs, match_id=7, seed=123)
            mock_end.assert_called_once_with(result)
