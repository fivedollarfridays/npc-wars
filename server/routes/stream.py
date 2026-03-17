"""SSE streaming route: GET /api/match/{match_id}/stream."""

import asyncio
import json
import re
from pathlib import Path
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api")

_SAFE_ID = re.compile(r"^[A-Za-z0-9_-]+$")


async def _match_stream(
    match_data: dict, speed: float = 1.0
) -> AsyncGenerator[str, None]:
    """Yield SSE events for each round in a completed match."""
    yield "retry: 3000\n\n"
    for round_data in match_data.get("rounds", []):
        event = json.dumps(round_data)
        yield f"event: round\ndata: {event}\n\n"
        await asyncio.sleep(1.0 / speed)
    final = {
        "winner": match_data.get("winner"),
        "duration_rounds": match_data.get("duration_rounds"),
    }
    yield f"event: complete\ndata: {json.dumps(final)}\n\n"


@router.get("/match/{match_id}/stream")
async def stream_match(match_id: str, request: Request) -> StreamingResponse:
    """Stream match rounds as Server-Sent Events."""
    if not _SAFE_ID.match(match_id):
        raise HTTPException(status_code=400, detail="Invalid match ID")

    results_dir = Path(getattr(request.app.state, "results_dir", "results"))
    candidates = [
        results_dir / f"match_{match_id}.json",
        results_dir / f"{match_id}.json",
    ]

    match_data = None
    for path in candidates:
        if path.is_file():
            try:
                match_data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                raise HTTPException(status_code=500, detail="Corrupt match file") from None
            break

    if match_data is None:
        raise HTTPException(status_code=404, detail="Match not found")

    return StreamingResponse(
        _match_stream(match_data),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
