"""HTML page routes for landing page, leaderboard, and player profile."""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(tags=["pages"])

_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
_VIEWER_DIR = Path(__file__).resolve().parent.parent.parent / "viewer"


@router.get("/")
async def landing_page() -> FileResponse:
    """Serve the Kill Switch landing page."""
    return FileResponse(
        _STATIC_DIR / "index.html",
        media_type="text/html",
    )


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


@router.get("/guide")
async def guide_page() -> FileResponse:
    """Serve the player guide page."""
    return FileResponse(
        _STATIC_DIR / "guide.html",
        media_type="text/html",
    )


@router.get("/viewer")
async def viewer_page() -> FileResponse:
    """Serve the match viewer page."""
    return FileResponse(
        _VIEWER_DIR / "index.html",
        media_type="text/html",
    )
