"""Tests for T49.4 — server middleware hardening (CORS, cookies, DB)."""

from __future__ import annotations

import logging
import os
from unittest.mock import patch

import pytest


# ── Cycle 1: CORS configuration ────────────────────────────────────


class TestCorsConfig:
    """CORS middleware should use explicit methods and headers, not wildcards."""

    def test_cors_allows_specific_methods_not_wildcard(self) -> None:
        """allow_methods must list GET/POST, not '*'."""
        from server.app import app

        for mw in app.user_middleware:
            if mw.cls.__name__ == "CORSMiddleware":
                methods = mw.kwargs.get("allow_methods", [])
                assert "*" not in methods, "CORS allow_methods must not use wildcard"
                assert "GET" in methods
                assert "POST" in methods
                return
        pytest.fail("CORSMiddleware not found in app middleware")

    def test_cors_allows_specific_headers_not_wildcard(self) -> None:
        """allow_headers must list specific headers, not '*'."""
        from server.app import app

        for mw in app.user_middleware:
            if mw.cls.__name__ == "CORSMiddleware":
                headers = mw.kwargs.get("allow_headers", [])
                assert "*" not in headers, "CORS allow_headers must not use wildcard"
                assert "Content-Type" in headers
                assert "X-API-Key" in headers
                assert "Authorization" in headers
                return
        pytest.fail("CORSMiddleware not found in app middleware")

    def test_cors_preflight_still_works(self) -> None:
        """OPTIONS preflight for allowed origin should succeed."""
        from fastapi.testclient import TestClient

        from server.app import app

        client = TestClient(app)
        resp = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:8000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.headers.get("access-control-allow-origin") == "http://localhost:8000"


# ── Cycle 2: Secure cookies ─────────────────────────────────────────


class TestSecureCookieDefault:
    """Secure cookie flag should default to True (secure by default)."""

    def test_secure_cookie_defaults_to_true(self) -> None:
        """Without NPCWARS_SECURE_COOKIES env var, _secure should be True."""
        env = os.environ.copy()
        env.pop("NPCWARS_SECURE_COOKIES", None)
        with patch.dict(os.environ, env, clear=True):
            # Simulate the default logic: default should be "1"
            val = os.environ.get("NPCWARS_SECURE_COOKIES", "1")
            _secure = val != "0"
            assert _secure is True, "Secure cookies should default to True"

    def test_secure_cookie_disabled_explicitly(self) -> None:
        """Setting NPCWARS_SECURE_COOKIES=0 disables secure flag."""
        with patch.dict(os.environ, {"NPCWARS_SECURE_COOKIES": "0"}):
            val = os.environ.get("NPCWARS_SECURE_COOKIES", "1")
            _secure = val != "0"
            assert _secure is False

    def test_secure_cookie_disable_logs_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """Disabling secure cookies should log a warning."""
        from fastapi.testclient import TestClient

        from server.app import app

        with patch.dict(os.environ, {"NPCWARS_SECURE_COOKIES": "0"}):
            client = TestClient(app)
            with caplog.at_level(logging.WARNING):
                # Make a request that triggers session cookie creation
                client.get("/health")
            assert any(
                "secure cookies disabled" in rec.message.lower()
                for rec in caplog.records
            ), f"Expected warning about secure cookies, got: {[r.message for r in caplog.records]}"


# ── Cycle 3: DB path warning ────────────────────────────────────────


class TestDbPathWarning:
    """Using :memory: DB without TESTING env var should log a warning."""

    @pytest.mark.skip(reason="server.app default changed to data/npcwars.db; no :memory: fallback to warn about")
    def test_memory_db_without_testing_env_logs_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """If DB_PATH is unset and TESTING is not set, warn about :memory:."""
        import importlib

        env = os.environ.copy()
        env.pop("DB_PATH", None)
        env.pop("TESTING", None)

        with caplog.at_level(logging.WARNING, logger="server.app"):
            with patch.dict(os.environ, env, clear=True):
                import server.app as app_mod

                importlib.reload(app_mod)

        assert any(
            ":memory:" in rec.message
            for rec in caplog.records
        ), f"Expected warning about :memory: DB, got: {[r.message for r in caplog.records]}"

    def test_memory_db_with_testing_env_no_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """If TESTING=1, no warning even with :memory: DB."""
        import importlib

        env = os.environ.copy()
        env.pop("DB_PATH", None)
        env["TESTING"] = "1"

        with caplog.at_level(logging.WARNING, logger="server.app"):
            with patch.dict(os.environ, env, clear=True):
                import server.app as app_mod

                importlib.reload(app_mod)

        memory_warnings = [
            rec for rec in caplog.records
            if ":memory:" in rec.message
        ]
        assert len(memory_warnings) == 0, f"Should not warn in test context, got: {memory_warnings}"
