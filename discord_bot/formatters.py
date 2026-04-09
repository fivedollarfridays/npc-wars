"""Pure formatting functions -- no discord.py dependency."""

from typing import Any

__all__ = [
    "format_match_start",
    "format_match_end",
    "format_results",
    "format_leaderboard",
    "format_roster",
    "format_claim_response",
    "format_unclaim_response",
    "format_tv_main_message",
    "format_tv_thread_stats",
    "format_tv_thread_watcher",
    "format_highlights",
    "format_game_standings",
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


def format_roster(claims: dict[str, str]) -> dict[str, Any]:
    """Format emoji roster as a plain dict."""
    if not claims:
        description = "No emojis claimed yet."
    else:
        description = "\n".join(f"{emoji} -> <@{uid}>" for emoji, uid in claims.items())
    return {
        "title": "📋 Roster",
        "description": description,
        "color": COLOR_BLUE,
        "fields": [],
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


# Colors for TV posting
COLOR_PURPLE = 0x9B59B6

_GAME_LABELS = {
    "kill_switch": "Kill Switch",
    "code_circuit": "Code Circuit",
}


def format_tv_main_message(episode: dict[str, Any]) -> dict[str, Any]:
    """Format the main TV post: winner, participants, top highlights."""
    meta = episode["metadata"]
    game = meta["game"]
    label = _GAME_LABELS.get(game, game)
    winner = meta["winner"]
    participants = meta["participants"]
    highlights = episode["post_match"].get("highlights", [])

    fields: list[dict[str, Any]] = [
        {"name": "Participants", "value": " ".join(participants), "inline": True},
    ]

    if highlights:
        hl_lines = [
            f"R{h['round']}: {h['trigger_type']} ({', '.join(h.get('participants', []))})"
            for h in highlights[:5]
        ]
        fields.append(
            {"name": "Top Highlights", "value": "\n".join(hl_lines), "inline": False},
        )

    return {
        "title": f"\U0001f4fa {label} TV",
        "description": f"\U0001f3c6 Winner: **{winner}**",
        "color": COLOR_GOLD,
        "fields": fields,
    }


def format_tv_thread_stats(episode: dict[str, Any]) -> dict[str, Any]:
    """Format the thread reply with full stats table and season standings."""
    post = episode["post_match"]
    stat_diffs = post.get("stat_diffs", [])
    standings = post.get("standings", [])

    fields: list[dict[str, Any]] = []

    if stat_diffs:
        stat_lines = []
        for row in stat_diffs:
            emoji = row["emoji"]
            parts = [f"{k}: {v}" for k, v in row.items() if k != "emoji"]
            stat_lines.append(f"{emoji} \u2014 {', '.join(parts)}")
        fields.append(
            {"name": "Stats", "value": "\n".join(stat_lines), "inline": False},
        )

    if standings:
        stand_lines = [
            f"{s['participant']} \u2014 {s['points']}pts ({s['tier']})"
            for s in standings
        ]
        fields.append(
            {"name": "Season Standings", "value": "\n".join(stand_lines), "inline": False},
        )

    return {
        "title": "\U0001f4ca Match Stats & Standings",
        "description": "",
        "color": COLOR_BLUE,
        "fields": fields,
    }


def format_highlights(
    game: str, highlights: list[dict[str, Any]],
) -> dict[str, Any]:
    """Format recent highlights for a game as a plain dict."""
    label = _GAME_LABELS.get(game, game)
    if not highlights:
        return {
            "title": f"\U0001f4fa {label} Highlights",
            "description": "No highlights yet.",
            "color": COLOR_GOLD,
            "fields": [],
        }
    shown = highlights[:5]
    lines = []
    for h in shown:
        rng = h.get("round_range", (0, 0))
        trigger = h.get("trigger_type", "?")
        participants = ", ".join(h.get("participants", []))
        score = h.get("drama_score", 0)
        lines.append(f"R{rng[0]}-{rng[1]}: {trigger} ({participants}) \u2014 drama {score}")
    return {
        "title": f"\U0001f4fa {label} Highlights",
        "description": "",
        "color": COLOR_GOLD,
        "fields": [
            {"name": "Recent Highlights", "value": "\n".join(lines), "inline": False},
        ],
    }


def format_game_standings(
    game: str, season_name: str, standings: list[dict[str, Any]],
) -> dict[str, Any]:
    """Format season standings for a specific game as a plain dict."""
    label = _GAME_LABELS.get(game, game)
    if not standings:
        return {
            "title": f"\U0001f4ca {label} \u2014 {season_name} Standings",
            "description": "No results yet.",
            "color": COLOR_BLUE,
            "fields": [],
        }
    lines = [
        f"{i + 1}. {s['participant']} \u2014 {s['points']}pts ({s['tier']})"
        for i, s in enumerate(standings)
    ]
    return {
        "title": f"\U0001f4ca {label} \u2014 {season_name} Standings",
        "description": "",
        "color": COLOR_BLUE,
        "fields": [
            {"name": "Rankings", "value": "\n".join(lines), "inline": False},
        ],
    }


def format_tv_thread_watcher(
    dossiers: dict[str, Any],
) -> dict[str, Any] | None:
    """Format Watcher dossier section for Kill Switch thread. Returns None if empty."""
    if not dossiers:
        return None

    fields: list[dict[str, Any]] = []
    for pid, dossier in dossiers.items():
        text = dossier.get("text_summary", "")
        sync = dossier.get("sync_score", 0)
        fields.append({
            "name": f"Watcher Dossier: {pid}",
            "value": f"Sync: {sync}%\n{text}",
            "inline": False,
        })

    return {
        "title": "\U0001f441 The Watcher's Analysis",
        "description": "",
        "color": COLOR_PURPLE,
        "fields": fields,
    }
