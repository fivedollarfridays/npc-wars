"""Thin integration layer to fire Discord announcements from the match runner.

Degrades gracefully when:
- discord.py is not installed
- BOT_TOKEN or ANNOUNCEMENT_CHANNEL_ID env vars are not set
- Any runtime error occurs during announcement dispatch
"""

import logging
import os
from typing import Any

__all__ = ["notify_match_start", "notify_match_end"]

log = logging.getLogger(__name__)


try:
    import discord  # noqa: F401
    _DISCORD_AVAILABLE = True
except ImportError:
    _DISCORD_AVAILABLE = False

_CHANNEL_ID_SENTINEL = object()
_cached_channel_id: int | None | object = _CHANNEL_ID_SENTINEL


def _get_channel_id() -> int | None:
    """Return the announcement channel ID from env, or None if not configured.

    Result is cached after first call since env vars don't change at runtime.
    """
    global _cached_channel_id
    if _cached_channel_id is not _CHANNEL_ID_SENTINEL:
        return _cached_channel_id  # type: ignore[return-value]
    bot_token = os.environ.get("BOT_TOKEN")
    channel_raw = os.environ.get("ANNOUNCEMENT_CHANNEL_ID")
    if not bot_token or not channel_raw:
        _cached_channel_id = None
        return None
    try:
        _cached_channel_id = int(channel_raw)
    except ValueError:
        _cached_channel_id = None
    return _cached_channel_id


def _reset_cache() -> None:
    """Reset cached config -- for testing only."""
    global _cached_channel_id, _DISCORD_AVAILABLE
    _cached_channel_id = _CHANNEL_ID_SENTINEL
    # Re-probe discord availability (may have been changed by reload)
    try:
        import discord  # noqa: F401
        _DISCORD_AVAILABLE = True
    except ImportError:
        _DISCORD_AVAILABLE = False


def _safe_announce(callback: Any, *args: Any) -> None:
    """Guard an announcement call with discord availability + config checks."""
    if not _DISCORD_AVAILABLE:
        return
    channel_id = _get_channel_id()
    if channel_id is None:
        return
    try:
        callback(channel_id, *args)
    except Exception:
        log.debug("Discord notification failed", exc_info=True)


def _dispatch_start(
    channel_id: int, match_id: int,
    players: list[dict[str, Any]], seed: int | None,
) -> None:
    """Build and log a match-start announcement (actual dispatch is a placeholder)."""
    log.info(
        "Match #%d starting with %d players (channel=%d)",
        match_id, len(players), channel_id,
    )


def _dispatch_end(channel_id: int, match_data: dict[str, Any]) -> None:
    """Build and log a match-end announcement (actual dispatch is a placeholder)."""
    log.info(
        "Match #%s ended, winner: %s (channel=%d)",
        match_data.get("match_id", "?"),
        match_data.get("winner", "?"),
        channel_id,
    )


def notify_match_start(
    match_id: int, players: list[dict[str, Any]], seed: int | None = None,
) -> None:
    """Announce match start to Discord. Skips silently on any failure."""
    _safe_announce(_dispatch_start, match_id, players, seed)


def notify_match_end(match_data: dict[str, Any]) -> None:
    """Announce match end to Discord. Skips silently on any failure."""
    _safe_announce(_dispatch_end, match_data)
