"""Profile display formatting — renders player profiles and leaderboards.

Pure formatting functions, no I/O.
"""
from __future__ import annotations

from engine.levels import (
    LEVEL_TABLE,
    MAX_LEVEL,
    unlocks_at_level,
    xp_for_next_level,
)


def render_progress_bar(current: int, total: int, width: int = 20) -> str:
    """Render a text progress bar using block characters.

    Returns a string of *width* characters using filled (█) and empty (░) blocks.
    Clamps to full bar when current >= total or total == 0.
    """
    if total <= 0 or current >= total:
        return "█" * width
    fraction = current / total
    filled = int(fraction * width)
    return "█" * filled + "░" * (width - filled)


def _next_unlock(level: int) -> tuple[str, int] | None:
    """Find the next action/callback unlock above *level*. Returns (name, lvl) or None."""
    for lvl in range(level + 1, MAX_LEVEL + 1):
        entry = LEVEL_TABLE[lvl]
        names = entry["new_actions"] + entry["new_callbacks"]
        if names:
            return names[0], lvl
    return None


def format_profile(profile: dict) -> str:
    """Render a single player profile as a boxed display string."""
    name = profile["name"]
    level = profile["level"]
    total_xp = profile["total_xp"]
    matches = profile["matches"]
    wins = profile["wins"]
    kills = profile["kills"]

    # XP progress toward next level
    next_xp = xp_for_next_level(level)
    current_level_xp = LEVEL_TABLE[level]["xp_required"]
    xp_in_level = total_xp - current_level_xp
    xp_needed = next_xp - current_level_xp if level < MAX_LEVEL else 0
    bar = render_progress_bar(xp_in_level, xp_needed, width=18)

    # Stats
    win_rate = (wins / matches * 100) if matches > 0 else 0.0
    kpm = (kills / matches) if matches > 0 else 0.0

    # Unlocks
    unlocks = unlocks_at_level(level)
    action_list = " ".join(sorted(unlocks.actions))
    next_ul = _next_unlock(level)

    lines = [
        f"  {name} -- Level {level}",
        f"  {bar} {total_xp}/{next_xp} XP",
        "",
        f"  Matches: {matches}  |  Wins: {wins}  |  W/R: {win_rate:.1f}%",
        f"  Kills: {kills}    |  K/M: {kpm:.1f}",
        "",
        f"  Unlocked: {action_list}",
    ]
    if next_ul:
        lines.append(f"  Next: {next_ul[0]} (Level {next_ul[1]})")

    width = max(len(line) for line in lines) + 4
    box_top = "+" + "=" * (width - 2) + "+"
    box_bot = "+" + "=" * (width - 2) + "+"
    boxed = [box_top]
    for line in lines:
        boxed.append(f"|{line:<{width - 2}}|")
    boxed.append(box_bot)
    return "\n".join(boxed)


def format_leaderboard(profiles: list[dict]) -> str:
    """Render a leaderboard table from a list of profile dicts."""
    if not profiles:
        return "No profiles found."

    header = f"{'#':<4}{'Name':<16}{'Level':<8}{'XP':<8}{'Matches':<10}{'Wins':<6}"
    sep = "-" * len(header)
    rows = [header, sep]
    for i, p in enumerate(profiles, 1):
        rows.append(
            f"{f'{i}.':<4}{p['name']:<16}{p['level']:<8}"
            f"{p['total_xp']:<8}{p['matches']:<10}{p['wins']:<6}"
        )
    return "\n".join(rows)
