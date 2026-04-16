"""TV/episode/highlight formatters -- no discord.py dependency."""

from typing import Any

__all__ = [
    "format_tv_main_message",
    "format_tv_thread_stats",
    "format_tv_thread_watcher",
    "format_highlights",
    "format_game_standings",
]

COLOR_GOLD = 0xF1C40F
COLOR_BLUE = 0x3498DB
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
