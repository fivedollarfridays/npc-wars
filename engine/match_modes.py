"""Match mode configurations for NPC Wars."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["MatchMode", "STANDARD", "EXTENDED", "MODES", "get_mode", "get_storm_border_for_mode"]


@dataclass(frozen=True)
class MatchMode:
    """Immutable match mode configuration."""

    name: str
    max_rounds: int
    starting_hp: int
    storm_delay_multiplier: float  # 1.0 = normal, 1.5 = 50% slower


STANDARD = MatchMode(name="standard", max_rounds=200, starting_hp=100, storm_delay_multiplier=1.0)
EXTENDED = MatchMode(name="extended", max_rounds=400, starting_hp=200, storm_delay_multiplier=1.5)

MODES: dict[str, MatchMode] = {"standard": STANDARD, "extended": EXTENDED}


def get_mode(name: str = "standard") -> MatchMode:
    """Look up a match mode by name, defaulting to standard."""
    return MODES.get(name, STANDARD)


def get_storm_border_for_mode(
    round_num: int, mode: MatchMode, grid_size: int | None = None
) -> int:
    """Get storm border adjusted for match mode's storm delay multiplier.

    When *grid_size* is provided it is forwarded to ``get_storm_border`` so the
    border is clamped to keep the safe zone at least 2x2.
    """
    from engine.grid import get_storm_border

    if mode.storm_delay_multiplier == 1.0:
        return get_storm_border(round_num, grid_size)
    adjusted_round = int(round_num / mode.storm_delay_multiplier)
    return get_storm_border(adjusted_round, grid_size)
