"""Post-match diff display formatter and progression box.

Formats stat comparisons (current vs lifetime average) and XP/level
progression into a boxed CLI display.
"""

from __future__ import annotations

from engine.levels import LEVEL_TABLE, MAX_LEVEL, unlocks_at_level, xp_to_next_level

__all__ = ["format_diff_section", "format_progression", "format_match_summary"]

# ANSI color codes
_GREEN = "\033[32m"
_RED = "\033[31m"
_DIM = "\033[90m"
_RESET = "\033[0m"
_BOLD = "\033[1m"

# Stats to display and their human-readable labels
_DISPLAY_STATS: list[tuple[str, str]] = [
    ("win_rate", "Win Rate"),
    ("avg_kills", "Avg Kills"),
    ("avg_rounds_survived", "Avg Survived"),
    ("avg_damage_dealt", "Damage/Round"),
]

_ARROWS = {
    "improved": "\u25b2",   # ▲
    "regressed": "\u25bc",  # ▼
    "neutral": "\u2500",    # ─
}

_COLORS = {
    "improved": _GREEN,
    "regressed": _RED,
    "neutral": _DIM,
}


def _format_stat_value(key: str, value: float) -> str:
    """Format a stat value with appropriate suffix."""
    if key == "win_rate":
        return f"{value:.0f}%"
    if key.startswith("avg_rounds"):
        return f"R{value:.0f}"
    return f"{value:.1f}"


def _format_stat_line(key: str, label: str, entry: dict) -> str:
    """Format a single stat comparison line with ANSI color."""
    cls = entry["classification"]
    color = _COLORS.get(cls, _DIM)
    arrow = _ARROWS.get(cls, "\u2500")

    lifetime = entry["lifetime_avg"]
    current = entry["current"]
    delta = entry["delta"]
    percentage = entry["percentage"]

    old_str = _format_stat_value(key, lifetime)
    new_str = _format_stat_value(key, current)

    delta_str = ""
    if percentage is not None:
        sign = "+" if delta >= 0 else ""
        delta_str = f" {sign}{percentage:.0f}%"

    return (
        f"  {label + ':':<16}"
        f"{color}{old_str} \u2192 {new_str}  "
        f"{arrow}{delta_str}{_RESET}"
    )


def format_diff_section(diff_data: dict | None) -> str:
    """Format stat diff data into colored comparison lines.

    Args:
        diff_data: Dict from compute_diff(), keyed by stat name.
            Each entry has classification/delta/percentage/lifetime_avg/current.
            None or empty dict triggers first-match message.

    Returns:
        Multi-line string showing stat comparisons with colored arrows.
    """
    if not diff_data:
        return "  First match! No comparison data yet."

    lines: list[str] = []
    for key, label in _DISPLAY_STATS:
        if key not in diff_data:
            continue
        entry = diff_data[key]
        lines.append(_format_stat_line(key, label, entry))
    return "\n".join(lines)


def _new_unlocks(old_level: int, new_level: int) -> list[str]:
    """Return actions/callbacks newly unlocked between old and new level."""
    old = unlocks_at_level(old_level)
    new = unlocks_at_level(new_level)
    new_actions = sorted(new.actions - old.actions)
    new_callbacks = sorted(new.callbacks - old.callbacks)
    return new_actions + [f"{cb}()" for cb in new_callbacks]


def _find_next_unlock_level(current_level: int) -> int | None:
    """Find the next level that grants new actions or callbacks."""
    for lvl in range(current_level + 1, MAX_LEVEL + 1):
        entry = LEVEL_TABLE[lvl]
        if entry["new_actions"] or entry["new_callbacks"]:
            return lvl
    return None


def format_progression(
    xp_data: dict | None, old_level: int, new_level: int,
) -> str:
    """Format XP progression and level-up information.

    Args:
        xp_data: Dict with 'total' (XP earned this match) and 'new_xp'
            (cumulative XP after match). None returns empty string.
        old_level: Level before this match.
        new_level: Level after this match.

    Returns:
        Multi-line string showing level change, unlocks, and next milestone.
    """
    if xp_data is None:
        return ""

    lines: list[str] = []
    total_xp = xp_data.get("total", 0)

    if old_level != new_level:
        lines.append(f"  Level {old_level} \u2192 {new_level}  (+{total_xp} XP)")
        unlocks = _new_unlocks(old_level, new_level)
        for unlock in unlocks:
            lines.append(f"  \U0001f513 UNLOCKED: {unlock}")
    else:
        lines.append(f"  Level {new_level}  (+{total_xp} XP)")

    # Next unlock preview
    next_lvl = _find_next_unlock_level(new_level)
    if next_lvl is not None:
        entry = LEVEL_TABLE[next_lvl]
        items = entry["new_actions"] + [
            f"{cb}()" for cb in entry["new_callbacks"]
        ]
        xp_remaining = xp_to_next_level(new_level, xp_data.get("new_xp", 0))
        lines.append(
            f"  Next unlock: {', '.join(items)}"
            f" (Level {next_lvl}, {xp_remaining} XP away)"
        )

    return "\n".join(lines)


_BOX_WIDTH = 50

_ORDINALS = {1: "1st", 2: "2nd", 3: "3rd"}


def _ordinal(n: int) -> str:
    """Return ordinal string for placement (1st, 2nd, 3rd, 4th...)."""
    if n in _ORDINALS:
        return _ORDINALS[n]
    return f"{n}th"


def _box_line(text: str) -> str:
    """Wrap text in box side borders, padded to _BOX_WIDTH."""
    inner = _BOX_WIDTH - 2  # subtract 2 for │ on each side
    return f"\u2502{text:<{inner}}\u2502"


def _section_header(title: str) -> str:
    """Format a section header like '── Stats vs Lifetime Average ──'."""
    return f"  \u2500\u2500 {title} \u2500\u2500"


def format_match_summary(
    bot_name: str,
    bot_glyph: str,
    placement: int,
    kills: int,
    rounds_survived: int,
    score: int,
    momentum_name: str,
    diff_data: dict | None,
    xp_data: dict | None,
    old_level: int,
    new_level: int,
) -> str:
    """Combine header, diff section, and progression into a boxed display.

    Args:
        bot_name: Name of the bot.
        bot_glyph: Emoji/glyph for the bot.
        placement: Final placement (1 = winner).
        kills: Total kills this match.
        rounds_survived: Number of rounds survived.
        score: Match score.
        momentum_name: Current momentum tier name.
        diff_data: Diff data from compute_diff(), or None.
        xp_data: XP data dict, or None.
        old_level: Level before match.
        new_level: Level after match.

    Returns:
        Boxed multi-line string for CLI display.
    """
    inner = _BOX_WIDTH - 2
    top = f"\u250c{'\u2500' * inner}\u2510"
    bottom = f"\u2514{'\u2500' * inner}\u2518"

    lines: list[str] = [top]
    lines.append(_box_line(f"  {_BOLD}MATCH COMPLETE{_RESET}"))
    lines.append(_box_line(""))
    lines.append(_box_line(f"  Your Bot: {bot_glyph} {bot_name}"))
    place_str = _ordinal(placement)
    lines.append(
        _box_line(
            f"  Result:   {place_str} place"
            f" \u2014 {kills} kills, {rounds_survived} rounds"
        )
    )
    lines.append(
        _box_line(f"  Score:    {score} pts (peaked: {momentum_name})")
    )
    lines.append(_box_line(""))

    # Diff section
    lines.append(_box_line(_section_header("Stats vs Lifetime Average")))
    diff_text = format_diff_section(diff_data)
    for dline in diff_text.split("\n"):
        lines.append(_box_line(dline))
    lines.append(_box_line(""))

    # Progression section
    prog_text = format_progression(xp_data, old_level, new_level)
    if prog_text:
        lines.append(_box_line(_section_header("Progression")))
        for pline in prog_text.split("\n"):
            lines.append(_box_line(pline))

    lines.append(bottom)
    return "\n".join(lines)
