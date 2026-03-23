"""HTML page routes for leaderboard and player profile."""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(tags=["pages"])

_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@router.get("/leaderboard")
async def leaderboard_page() -> FileResponse:
    """Serve the leaderboard HTML page."""
    return FileResponse(
        _STATIC_DIR / "leaderboard.html",
        media_type="text/html",
    )


@router.get("/profile/{player_id}")
async def profile_page(player_id: str) -> FileResponse:
    """Serve the player profile HTML page.

    The player_id is extracted from the URL by client-side JS.
    """
    return FileResponse(
        _STATIC_DIR / "profile.html",
        media_type="text/html",
    )
