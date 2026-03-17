"""Tests for health check and monitoring endpoints."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from server.app import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


# ── /health endpoint ─────────────────────────────────────────────────


def test_health_returns_components(client: TestClient) -> None:
    """GET /health returns status and components dict."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "components" in data
    assert isinstance(data["components"], dict)


def test_health_has_redis_check(client: TestClient) -> None:
    """Components include a redis entry."""
    data = client.get("/health").json()
    assert "redis" in data["components"]
    assert "status" in data["components"]["redis"]


def test_health_has_sqlite_check(client: TestClient) -> None:
    """Components include a sqlite entry."""
    data = client.get("/health").json()
    assert "sqlite" in data["components"]
    assert "status" in data["components"]["sqlite"]


def test_health_has_disk_check(client: TestClient) -> None:
    """Components include a disk entry."""
    data = client.get("/health").json()
    assert "disk" in data["components"]
    assert "status" in data["components"]["disk"]


def test_health_degraded_when_component_fails(client: TestClient) -> None:
    """Status is 'degraded' when a component check fails."""
    with patch("server.routes.health._check_redis", return_value={"status": "error", "detail": "down"}):
        data = client.get("/health").json()
    assert data["status"] == "degraded"


# ── /health/ready endpoint ───────────────────────────────────────────


def test_readiness_returns_200_when_healthy(client: TestClient) -> None:
    """GET /health/ready returns 200 when all components are ok."""
    with patch("server.routes.health._check_redis", return_value={"status": "ok"}), \
         patch("server.routes.health._check_sqlite", return_value={"status": "ok"}), \
         patch("server.routes.health._check_disk", return_value={"status": "ok"}):
        resp = client.get("/health/ready")
    assert resp.status_code == 200


def test_readiness_returns_503_when_degraded(client: TestClient) -> None:
    """GET /health/ready returns 503 when a component fails."""
    with patch("server.routes.health._check_redis", return_value={"status": "error", "detail": "conn refused"}):
        resp = client.get("/health/ready")
    assert resp.status_code == 503


# ── /metrics endpoint ────────────────────────────────────────────────


def test_metrics_has_match_count(client: TestClient) -> None:
    """GET /metrics includes match_count."""
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "match_count" in resp.json()


def test_metrics_has_queue_depth(client: TestClient) -> None:
    """GET /metrics includes queue_depth."""
    data = client.get("/metrics").json()
    assert "queue_depth" in data


def test_metrics_match_count_with_files(client: TestClient, tmp_path: Path) -> None:
    """Match count reflects actual result files."""
    for i in range(3):
        (tmp_path / f"match_{i:03d}.json").write_text(json.dumps({"id": i}))
    app.state.results_dir = str(tmp_path)
    try:
        data = client.get("/metrics").json()
        assert data["match_count"] == 3
    finally:
        app.state.results_dir = "results"
