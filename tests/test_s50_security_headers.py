"""Tests for security response headers middleware (T50.2)."""

from fastapi.testclient import TestClient

from server.app import app

client = TestClient(app)

EXPECTED_HEADERS = {
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains",
    "Content-Security-Policy": (
        "default-src 'self'; script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'"
    ),
    "Referrer-Policy": "strict-origin-when-cross-origin",
}


def test_health_has_x_frame_options() -> None:
    """GET /health includes X-Frame-Options: DENY."""
    resp = client.get("/health")
    assert resp.headers.get("X-Frame-Options") == "DENY"


def test_all_security_headers_present() -> None:
    """GET /health includes all 5 security headers with correct values."""
    resp = client.get("/health")
    for header, value in EXPECTED_HEADERS.items():
        assert resp.headers.get(header) == value, (
            f"Header {header} expected '{value}', got '{resp.headers.get(header)}'"
        )


def test_headers_on_error_responses() -> None:
    """GET to a nonexistent path (404) still has all security headers."""
    resp = client.get("/nonexistent-path-that-does-not-exist")
    assert resp.status_code == 404
    for header, value in EXPECTED_HEADERS.items():
        assert resp.headers.get(header) == value, (
            f"Header {header} missing on 404 response"
        )


def test_csp_header_value() -> None:
    """CSP header matches the exact expected policy string."""
    resp = client.get("/health")
    expected_csp = (
        "default-src 'self'; script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'"
    )
    assert resp.headers.get("Content-Security-Policy") == expected_csp


def test_headers_on_api_endpoints() -> None:
    """GET /api/lobby/status includes all security headers."""
    resp = client.get("/api/lobby/status")
    for header, value in EXPECTED_HEADERS.items():
        assert resp.headers.get(header) == value, (
            f"Header {header} missing on /api/lobby/status"
        )
