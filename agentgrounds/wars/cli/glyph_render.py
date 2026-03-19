"""Glyph rendering with HP-dependent ANSI coloring."""
from __future__ import annotations

__all__ = ["render_glyph", "get_primary_stat"]

_RST = "\033[0m"
_BRIGHT_WHITE = "\033[97m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RED = "\033[31m"


_STAT_BACKGROUNDS: dict[str, str] = {
    "power": "\033[41m",
    "speed": "\033[46m",
    "armor": "\033[44m",
    "mind": "\033[45m",
}

_THRESHOLD = 35


def get_primary_stat(
    power: int, speed: int, armor: int, mind: int,
) -> str | None:
    """Return the dominant stat name if any stat >= threshold, else None."""
    stats = {"power": power, "speed": speed, "armor": armor, "mind": mind}
    candidates = {k: v for k, v in stats.items() if v >= _THRESHOLD}
    if not candidates:
        return None
    return max(candidates, key=candidates.__getitem__)


def render_glyph(
    glyph: str, hp: int, max_hp: int, primary_stat: str | None = None,
) -> str:
    """Return ANSI-colored glyph based on HP percentage.

    Color thresholds:
        >75%  bright white (full health)
        50-75%  green (healthy)
        25-50%  yellow (wounded)
        <=25%  red (critical)
    """
    pct = hp / max(1, max_hp)
    if pct > 0.75:
        color = _BRIGHT_WHITE
    elif pct > 0.50:
        color = _GREEN
    elif pct > 0.25:
        color = _YELLOW
    else:
        color = _RED
    bg = _STAT_BACKGROUNDS.get(primary_stat or "", "")
    return f"{bg}{color}{glyph}{_RST}"
