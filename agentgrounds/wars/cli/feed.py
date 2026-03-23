"""Kill-feed event formatting for the terminal renderer."""
from __future__ import annotations

from .feed_formatters import FORMATTERS as _FORMATTERS

__all__ = ["format_feed_event"]


def format_feed_event(evt: dict, rnd: int) -> str | None:
    """Format a single event into a kill-feed line, or None if unrecognised."""
    etype = evt.get("type")
    formatter = _FORMATTERS.get(etype)
    if formatter is not None:
        return formatter(evt, rnd)
    return None
