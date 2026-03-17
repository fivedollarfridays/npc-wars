"""Tests for the in-browser code editor page (T17.8)."""

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from server.app import app

EDITOR_PATH = Path(__file__).resolve().parent.parent / "server" / "static" / "editor.html"


@pytest.fixture
def editor_html() -> str:
    """Read the editor HTML file contents."""
    assert EDITOR_PATH.exists(), f"editor.html not found at {EDITOR_PATH}"
    return EDITOR_PATH.read_text()


def test_editor_html_exists():
    """editor.html must exist at server/static/editor.html."""
    assert EDITOR_PATH.exists()


def test_editor_has_monaco(editor_html: str):
    """Editor must load Monaco Editor from CDN."""
    assert "monaco" in editor_html.lower()
    assert "vs/loader" in editor_html


def test_editor_has_submit_button(editor_html: str):
    """Editor must have a submit button."""
    assert "submit" in editor_html.lower()
    assert "<button" in editor_html.lower()


def test_editor_has_bot_template(editor_html: str):
    """Editor must contain the decide() function template."""
    assert "def decide(state)" in editor_html
    assert "BOT_NAME" in editor_html


def test_editor_has_error_display(editor_html: str):
    """Editor must have an error display area."""
    assert 'id="errors"' in editor_html or 'id="error' in editor_html.lower()


def test_editor_posts_to_submit_bot(editor_html: str):
    """Editor must reference the /api/submit-bot endpoint."""
    assert "/api/submit-bot" in editor_html


def test_editor_has_lobby_status(editor_html: str):
    """Editor must have a lobby status display area."""
    assert "lobby" in editor_html.lower()


def test_editor_has_match_link(editor_html: str):
    """Editor must have a match result link area."""
    assert "match-link" in editor_html or "match_link" in editor_html


@pytest.mark.anyio
async def test_static_files_mounted():
    """GET /static/editor.html should return 200."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/static/editor.html")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")
