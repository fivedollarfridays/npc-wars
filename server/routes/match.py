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

    # Try match_{id}.json first (numeric IDs), then {id}.json (UUID job IDs)
    candidates = [
        results_dir / f"match_{match_id}.json",
        results_dir / f"{match_id}.json",
    ]

    for path in candidates:
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                raise HTTPException(status_code=500, detail="Corrupt match file")
            return data

    raise HTTPException(status_code=404, detail="Match not found")
