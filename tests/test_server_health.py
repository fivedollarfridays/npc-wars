"""Tests for FastAPI server skeleton and health endpoint."""

from fastapi.testclient import TestClient

from server.app import app


client = TestClient(app)


def test_health_returns_ok():
    """GET /health returns 200 with {"status": "ok"}."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_headers_present():
    """OPTIONS request to /health returns CORS headers."""
    response = client.options(
        "/health",
        headers={"Origin": "http://localhost:8000", "Access-Control-Request-Method": "GET"},
    )
    assert response.headers.get("access-control-allow-origin") == "http://localhost:8000"


def test_app_has_title():
    """App title is 'NPC Wars Server'."""
    assert app.title == "NPC Wars Server"
