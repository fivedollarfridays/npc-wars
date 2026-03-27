"""Tests for T54.4: Graduation UI — landing page card + editor badge/dropdown."""

from pathlib import Path

from fastapi.testclient import TestClient

from server.app import app
from server.db import init_db

STATIC = Path("server/static")


class TestIndexGraduationCard:
    """Landing page should have a hidden Training Complete card."""

    def test_has_training_complete_element(self) -> None:
        html = (STATIC / "index.html").read_text()
        assert "training-complete" in html.lower() or "graduated" in html.lower()

    def test_references_graduated_api(self) -> None:
        html = (STATIC / "index.html").read_text()
        assert "/api/rival/graduated" in html

    def test_training_card_hidden_by_default(self) -> None:
        html = (STATIC / "index.html").read_text()
        assert (
            "display:none" in html.replace(" ", "")
            or "display: none" in html
        )


class TestEditorGraduationUI:
    """Editor should have graduated badge and tier select dropdown."""

    def test_has_graduated_badge(self) -> None:
        html = (STATIC / "editor.html").read_text()
        assert "graduated" in html.lower()

    def test_has_tier_select(self) -> None:
        html = (STATIC / "editor.html").read_text()
        assert "tier-select" in html.lower() or "<select" in html.lower()

    def test_references_graduated_api(self) -> None:
        html = (STATIC / "editor.html").read_text()
        assert "/api/rival/graduated" in html


class TestPagesStillLoad:
    """Both pages must still serve 200 after modifications."""

    def test_index_loads(self) -> None:
        old_db = getattr(app.state, "db", None)
        app.state.db = init_db(":memory:")
        client = TestClient(app)
        assert client.get("/").status_code == 200
        app.state.db = old_db

    def test_editor_loads(self) -> None:
        old_db = getattr(app.state, "db", None)
        app.state.db = init_db(":memory:")
        client = TestClient(app)
        assert client.get("/static/editor.html").status_code == 200
        app.state.db = old_db
