"""Match retrieval route: GET /api/match/{match_id}."""

import json
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/api")

_SAFE_ID = re.compile(r"^[A-Za-z0-9_-]+$")


@router.get("/match/{match_id}")
async def get_match(match_id: str, request: Request) -> dict:
    """Return match result JSON by match ID."""
    if not _SAFE_ID.match(match_id):
        raise HTTPException(status_code=400, detail="Invalid match ID")

    results_dir = Path(getattr(request.app.state, "results_dir", "results"))

    # Try match_{id}.json first (numeric IDs), then {id}.json (UUID job IDs).
    # Matches are written zero-padded (match_{id:03d}.json), so a natural-id
    # lookup like /api/match/1 must also try match_001.json (UP-3 submit->replay).
    candidates = [
        results_dir / f"match_{match_id}.json",
        results_dir / f"{match_id}.json",
    ]
    if match_id.isdigit():
        candidates.append(results_dir / f"match_{int(match_id):03d}.json")

    resolved_results = results_dir.resolve()
    for path in candidates:
        if path.resolve().is_relative_to(resolved_results) and path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                raise HTTPException(status_code=500, detail="Corrupt match file")
            return data

    raise HTTPException(status_code=404, detail="Match not found")
