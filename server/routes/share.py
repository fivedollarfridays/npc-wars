"""Permalink sharing route: GET /m/{match_id} with OG meta tags."""

import json
import re
from html import escape
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from server.rival_factory import RIVAL_EMOJI

router = APIRouter()

_SAFE_ID = re.compile(r"^[A-Za-z0-9_-]+$")


def _load_match(results_dir: Path, match_id: str) -> dict[str, Any]:
    """Load match JSON from the results directory, or raise 404."""
    candidates = [
        results_dir / f"match_{match_id}.json",
        results_dir / f"{match_id}.json",
    ]
    resolved = results_dir.resolve()
    for p in candidates:
        if p.resolve().is_relative_to(resolved) and p.is_file():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
            break
    raise HTTPException(status_code=404, detail="Match not found")


def _build_description(match_data: dict[str, Any]) -> str:
    """Build OG description, enhanced for rival matches."""
    winner = escape(str(match_data.get("winner", "?")))
    duration = match_data.get("duration_rounds", 0)
    player_list = match_data.get("players", [])

    is_rival = any(p.get("emoji") == RIVAL_EMOJI for p in player_list)
    if is_rival:
        rival_player = next(
            (p for p in player_list if p.get("emoji") == RIVAL_EMOJI),
            None,
        )
        rival_name = rival_player.get("name", "Rival") if rival_player else "Rival"
        return f"{winner} vs {escape(rival_name)}! Rival training match, {duration} rounds"

    return f"{winner} wins! {len(player_list)} bots, {duration} rounds"


@router.get("/m/{match_id}", response_class=HTMLResponse)
async def share_match(match_id: str, request: Request) -> HTMLResponse:
    """Serve viewer HTML with OG meta tags for social sharing."""
    if not _SAFE_ID.match(match_id):
        raise HTTPException(status_code=400, detail="Invalid match ID")

    results_dir = Path(getattr(request.app.state, "results_dir", "results"))
    match_data = _load_match(results_dir, match_id)

    raw_id = match_data.get("match_id", match_id)
    title = f"NPC Wars Match #{escape(str(raw_id))}"
    description = _build_description(match_data)

    html = (
        "<!DOCTYPE html>\n"
        "<html>\n"
        "<head>\n"
        '  <meta charset="UTF-8">\n'
        f'  <meta property="og:title" content="{title}">\n'
        f'  <meta property="og:description" content="{description}">\n'
        '  <meta property="og:type" content="website">\n'
        f'  <meta http-equiv="refresh" content="0; url=/static/editor.html?match={escape(str(raw_id))}">\n'
        f"  <title>{title}</title>\n"
        "</head>\n"
        "<body>\n"
        "  <p>Redirecting to match viewer...</p>\n"
        "</body>\n"
        "</html>"
    )
    return HTMLResponse(content=html)
