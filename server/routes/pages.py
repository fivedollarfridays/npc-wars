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
    """Serve the player profile HTML page."""
    return FileResponse(
        _STATIC_DIR / "profile.html",
        media_type="text/html",
    )


@router.get("/tournament/{tournament_id}")
async def tournament_page(tournament_id: int) -> FileResponse:
    """Serve the tournament bracket page."""
    return FileResponse(
        _STATIC_DIR / "tournament.html",
        media_type="text/html",
    )


@router.get("/tournaments")
async def tournaments_page() -> FileResponse:
    """Serve the tournaments list page."""
    return FileResponse(
        _STATIC_DIR / "tournaments.html",
        media_type="text/html",
    )
