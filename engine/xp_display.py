"""Post-match XP summary formatter — console display of XP awards."""

from __future__ import annotations

from typing import Any

from engine.levels import unlocks_at_level
from engine.xp import WIN_BONUS

__all__ = ["format_xp_summary"]

HEADER = "── XP Awards ──────────────────────────"
FOOTER = "────────────────────────────────────────"


def _placement_label(placement_xp: int) -> str:
    """Return 'win' for winner bonus, 'place' for runner-up, empty for 0."""
    if placement_xp == WIN_BONUS:
        return "win"
    if placement_xp > 0:
        return "place"
    return ""


def _format_breakdown(award: dict[str, Any]) -> str:
    """Format the parenthesized XP breakdown string."""
    parts = [
        f"{award['base']} base",
        f"{award['kills']} kills",
        f"{award['survival']} survival",
        f"{award['placement']} {_placement_label(award['placement'])}",
        f"{award['bonuses']} bonus",
    ]
    return f"({' + '.join(parts)})"


def _new_unlocks_at_level(new_level: int) -> list[str]:
    """Return actions/callbacks newly unlocked at exactly *new_level*.

    Compares cumulative unlocks at new_level vs new_level-1.
    """
    current = unlocks_at_level(new_level)
    previous = unlocks_at_level(new_level - 1) if new_level > 1 else unlocks_at_level(1)
    new_actions = sorted(current.actions - previous.actions)
    new_callbacks = sorted(current.callbacks - previous.callbacks)
    return new_actions + [f"{cb}()" for cb in new_callbacks]


def _format_level_up(award: dict[str, Any]) -> str:
    """Format a level-up indented line with unlocks."""
    new_level = award["new_level"]
    old_level = new_level - 1
    unlocks = _new_unlocks_at_level(new_level)
    line = f"    \u27f6 LEVEL UP! Level {old_level} \u2192 {new_level}"
    if unlocks:
        line += f"  \u2605 Unlocked: {', '.join(unlocks)}"
    return line


def format_xp_summary(
    xp_awards: dict[str, dict[str, Any]],
    players: list[dict[str, Any]] | None = None,
) -> str:
    """Format XP awards as a multi-line console summary string.

    Args:
        xp_awards: Dict keyed by emoji with XP breakdown + level info.
        players: Optional player list for emoji-to-name mapping.

    Returns:
        Formatted string ready for print().
    """
    if not xp_awards:
        return ""

    # Build emoji -> name lookup
    name_map: dict[str, str] = {}
    if players:
        for p in players:
            name_map[p["emoji"]] = p["name"]

    # Sort by total XP descending
    sorted_entries = sorted(
        xp_awards.items(),
        key=lambda item: item[1]["total"],
        reverse=True,
    )

    lines: list[str] = [HEADER]

    for emoji, award in sorted_entries:
        label = name_map.get(emoji, emoji)
        total = award["total"]
        breakdown = _format_breakdown(award)
        lines.append(f"  {label:<16}+{total} XP  {breakdown}")

        if award.get("leveled_up"):
            level_line = _format_level_up(award)
            lines.append(level_line)

    lines.append(FOOTER)
    return "\n".join(lines)
