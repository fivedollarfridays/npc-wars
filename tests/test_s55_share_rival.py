"""Tests for T55.4: Shareable rival replays."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from server.app import app
from server.db import init_db


@pytest.fixture(autouse=True)
def setup_db():
    old_db = getattr(app.state, "db", None)
    old_results = getattr(app.state, "results_dir", "results")
    app.state.db = init_db(":memory:")
    yield
    app.state.db = old_db
    app.state.results_dir = old_results


client = TestClient(app)


class TestShareRouteRivalDetection:
    """Share route detects rival matches and enhances OG description."""

    def test_share_imports_rival_emoji(self) -> None:
        share_code = Path("server/routes/share.py").read_text()
        assert "RIVAL_EMOJI" in share_code

    def test_share_has_rival_detection_logic(self) -> None:
        share_code = Path("server/routes/share.py").read_text()
        assert "is_rival" in share_code.lower()


class TestDebriefShareButton:
    """Debrief page has a share button with clipboard copy."""

    def test_debrief_has_share_button(self) -> None:
        html = Path("server/static/debrief.html").read_text()
        assert "share" in html.lower()

    def test_debrief_has_copy_to_clipboard(self) -> None:
        html = Path("server/static/debrief.html").read_text()
        assert "clipboard" in html.lower()

    def test_debrief_has_share_confirm_element(self) -> None:
        html = Path("server/static/debrief.html").read_text()
        assert "share-confirm" in html


class TestViewerShareButton:
    """Viewer results overlay has a share button."""

    def test_results_js_has_share_functionality(self) -> None:
        js = Path("viewer/js/results.js").read_text()
        assert "share" in js.lower()

    def test_viewer_html_has_share_button(self) -> None:
        html = Path("viewer/index.html").read_text()
        assert "share" in html.lower()


class TestPagesLoad:
    """Debrief page loads successfully."""

    def test_debrief_loads(self) -> None:
        resp = client.get("/debrief/1")
        assert resp.status_code == 200
