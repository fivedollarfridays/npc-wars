"""Permalink sharing route: GET /m/{match_id} with OG meta tags."""

import json
import re
from html import escape
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

router = APIRouter()

_SAFE_ID = re.compile(r"^[A-Za-z0-9_-]+$")


@router.get("/m/{match_id}", response_class=HTMLResponse)
async def share_match(match_id: str, request: Request) -> HTMLResponse:
    """Serve viewer HTML with OG meta tags for social sharing."""
    if not _SAFE_ID.match(match_id):
        raise HTTPException(status_code=400, detail="Invalid match ID")

    results_dir = Path(getattr(request.app.state, "results_dir", "results"))

    candidates = [
        results_dir / f"match_{match_id}.json",
        results_dir / f"{match_id}.json",
    ]

    resolved_results = results_dir.resolve()
    match_data = None
    for p in candidates:
        if p.resolve().is_relative_to(resolved_results) and p.is_file():
            try:
                match_data = json.loads(p.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
            break

    if match_data is None:
        raise HTTPException(status_code=404, detail="Match not found")

    winner = escape(str(match_data.get("winner", "?")))
    duration = match_data.get("duration_rounds", 0)
    players = len(match_data.get("players", []))
    raw_id = match_data.get("match_id", match_id)
    title = f"NPC Wars Match #{escape(str(raw_id))}"
    description = f"{winner} wins! {players} bots, {duration} rounds"

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
