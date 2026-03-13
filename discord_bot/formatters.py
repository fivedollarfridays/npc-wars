"""Pure formatting functions -- no discord.py dependency."""

from typing import Any

__all__ = [
    "format_match_start",
    "format_match_end",
    "format_results",
    "format_leaderboard",
    "format_claim_response",
    "format_unclaim_response",
]

# Colors as hex ints (matches discord.Color values)
COLOR_GREEN = 0x2ECC71
COLOR_RED = 0xE74C3C
COLOR_GOLD = 0xF1C40F
COLOR_BLUE = 0x3498DB
COLOR_ORANGE = 0xE67E22

PAGE_SIZE = 10


def format_match_start(
    match_id: int, players: list[dict[str, Any]], seed: int | None,
) -> dict[str, Any]:
    """Format match start data as a plain dict (no discord.Embed)."""
    roster = " ".join(p["emoji"] for p in players)
    fields: list[dict[str, Any]] = [
        {"name": "Players", "value": roster or "none", "inline": False},
        {"name": "Competitors", "value": str(len(players)), "inline": True},
    ]
    if seed is not None:
        fields.append({"name": "Seed", "value": str(seed), "inline": True})
    return {
        "title": f"\u2694\ufe0f Match #{match_id} \u2014 FIGHT!",
        "description": "The battle begins!",
        "color": COLOR_ORANGE,
        "fields": fields,
    }


def format_match_end(match_data: dict[str, Any]) -> dict[str, Any]:
    """Format match end data as a plain dict."""
    winner = match_data["winner"]
    duration = match_data["duration_rounds"]
    eliminations: list[dict[str, Any]] = match_data.get("eliminations", [])

    lines = [
        f"R{e['round']}: {e.get('killed_by', '?')} \u2192 {e['emoji']} ({e['cause']})"
        for e in eliminations[-3:]
    ]
    fields: list[dict[str, Any]] = [
        {"name": "Duration", "value": f"{duration} rounds", "inline": True},
    ]
    if lines:
        fields.append(
            {"name": "Final Kills", "value": "\n".join(lines), "inline": False},
        )
    return {
        "title": f"\U0001f3c6 Match #{match_data['match_id']} Complete!",
        "description": f"Winner: **{winner}**",
        "color": COLOR_GOLD,
        "fields": fields,
    }


def format_results(match_data: dict[str, Any]) -> dict[str, Any]:
    """Format match results with placements as a plain dict."""
    winner = match_data["winner"]
    duration = match_data["duration_rounds"]
    eliminations: list[dict[str, Any]] = match_data.get("eliminations", [])

    elim_emojis = [e["emoji"] for e in eliminations]
    ordered = [winner] + [e for e in reversed(elim_emojis) if e != winner]
    placement_lines = [f"{i + 1}. {emoji}" for i, emoji in enumerate(ordered)]

    return {
        "title": f"\U0001f4ca Match #{match_data['match_id']} Results",
        "description": f"\U0001f3c6 Winner: **{winner}**",
        "color": COLOR_GOLD,
        "fields": [
            {"name": "Duration", "value": f"{duration} rounds", "inline": True},
            {
                "name": "Placements",
                "value": "\n".join(placement_lines) or "\u2014",
                "inline": False,
            },
        ],
    }


def format_leaderboard(
    rankings: list[dict[str, Any]], page: int = 1, sort_by: str = "wins",
) -> dict[str, Any]:
    """Format leaderboard rankings with pagination as a plain dict."""
    total_pages = max(1, (len(rankings) + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(1, min(page, total_pages))
    start = (page - 1) * PAGE_SIZE
    slice_ = rankings[start : start + PAGE_SIZE]

    if not slice_:
        return {
            "title": "\U0001f3c6 Leaderboard",
            "description": "No data yet.",
            "color": COLOR_BLUE,
            "fields": [],
            "footer": "Page 1/1",
        }

    lines = [
        f"{start + i + 1}. {e['emoji']} \u2014 {e.get('wins', 0)}W / {e.get('kills', 0)}K"
        for i, e in enumerate(slice_)
    ]
    return {
        "title": f"\U0001f3c6 Leaderboard (by {sort_by})",
        "description": "\n".join(lines),
        "color": COLOR_BLUE,
        "fields": [],
        "footer": f"Page {page}/{total_pages}",
    }


def format_claim_response(
    emoji: str, ok: bool, reason: str,
) -> dict[str, Any]:
    """Format claim response as a plain dict."""
    if ok:
        return {
            "title": "\u2705 Emoji Claimed",
            "description": f"{emoji} is now yours!",
            "color": COLOR_GREEN,
            "fields": [],
        }
    return {
        "title": "\u274c Claim Failed",
        "description": reason,
        "color": COLOR_RED,
        "fields": [],
    }


def format_unclaim_response(
    emoji: str, ok: bool, reason: str,
) -> dict[str, Any]:
    """Format unclaim response as a plain dict."""
    if ok:
        return {
            "title": "\u2705 Emoji Released",
            "description": f"{emoji} unclaimed.",
            "color": COLOR_GREEN,
            "fields": [],
        }
    return {
        "title": "\u274c Unclaim Failed",
        "description": reason,
        "color": COLOR_RED,
        "fields": [],
    }
