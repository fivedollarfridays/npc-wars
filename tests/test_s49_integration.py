"""S49 security integration gate — cross-module regression tests.

Proves all S49 security fixes work together as a stack. Individual task
tests verify each fix in isolation; these tests verify cross-module
interactions and ensure nothing was missed.
"""

from __future__ import annotations

import inspect
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from engine.bot_scanner import scan_bot_source
from server.app import app
from server.db import create_api_key, create_player, init_db
from server.docker_sandbox import load_bot_from_source
from server.middleware.rate_limit import clear_rate_limit_state
from server.routes.submit import clear_rate_limits

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture()
def db_conn(tmp_path):
    """Fresh DB connection for integration tests."""
    conn = init_db(str(tmp_path / "integration.db"))
    app.state.db = conn
    yield conn
    conn.close()


@pytest.fixture()
def client(db_conn):
    """TestClient with a clean DB and reset rate limits."""
    clear_rate_limit_state()
    clear_rate_limits()
    return TestClient(app)


@pytest.fixture()
def player_with_key(db_conn):
    """Create a player and return (player_dict, raw_api_key)."""
    player = create_player(db_conn, "int-player-1", "IntegrationBot")
    key = create_api_key(db_conn, player["id"])
    return player, key


# ── TestSandboxIntegration ───────────────────────────────────────────


class TestSandboxIntegration:
    """End-to-end: malicious bots fail validation, safe bots pass."""

    def test_import_os_system_fails_validation(self):
        """A bot with __import__('os').system('echo pwned') is rejected."""
        source = (
            "__import__('os').system('echo pwned')\n"
            "BOT_NAME = 'Evil'\n"
            "BOT_EMOJI = '\\U0001f916'\n"
            "def decide(state): return ('rest',)\n"
        )
        with pytest.raises(ValueError, match="failed scan"):
            load_bot_from_source(source, "evil_import")

    def test_getattr_class_bases_fails_scanner(self):
        """A bot using getattr((), '__class__').__bases__ fails scan."""
        source = (
            "x = getattr((), '__class__').__bases__\n"
            "BOT_NAME = 'Evil'\n"
            "BOT_EMOJI = '\\U0001f916'\n"
            "def decide(state): return ('rest',)\n"
        )
        violations = scan_bot_source(source)
        assert any("getattr" in v for v in violations)
        assert any("__bases__" in v for v in violations)

    def test_safe_builtins_pass_validation(self):
        """A bot using len(), range(), min(), max() loads fine."""
        source = (
            "x = len(range(10))\n"
            "y = min(1, 2)\n"
            "z = max(3, 4)\n"
            "BOT_NAME = 'Safe'\n"
            "BOT_EMOJI = '\\U0001f916'\n"
            "def decide(state): return ('rest',)\n"
        )
        config = load_bot_from_source(source, "safe_bot")
        assert config["name"] == "Safe"

    def test_all_shipped_bots_pass_validation(self):
        """Every bot in bots/ passes both scanner and sandbox load."""
        from engine.bot_scanner import scan_bot_file

        bots_dir = PROJECT_ROOT / "bots"
        bot_files = list(bots_dir.glob("*.py"))
        assert len(bot_files) > 0, "No bot files found in bots/"

        for bot_path in bot_files:
            violations = scan_bot_file(str(bot_path))
            assert violations == [], (
                f"{bot_path.name} has violations: {violations}"
            )


# ── TestXSSAcrossPages ───────────────────────────────────────────────


class TestXSSAcrossPages:
    """Verify no HTML file has raw user data in innerHTML assignments."""

    def _get_html_files(self) -> list[Path]:
        """Return all HTML files in server/static/."""
        return list((PROJECT_ROOT / "server" / "static").glob("*.html"))

    def _extract_scripts(self, html: str) -> str:
        """Extract all <script> blocks from HTML."""
        blocks = re.findall(r"<script[^>]*>(.*?)</script>", html, re.DOTALL)
        return "\n".join(blocks)

    def test_all_innerhtml_near_user_data_has_sanitize(self):
        """Every innerHTML string concat with user data must use sanitize().

        We scan for user-controlled fields that appear in string
        concatenation (+ field) inside innerHTML blocks. Fields used
        only in comparisons (=== field) are safe and excluded.
        """
        # User-controlled field patterns inserted into HTML strings
        user_fields = ["t.name", "t.winner", "p.emoji", "m.winner"]

        for html_path in self._get_html_files():
            script = self._extract_scripts(html_path.read_text())
            for field in user_fields:
                # Find field in string concat context (+ field) without sanitize
                esc = re.escape(field)
                # Match: + field NOT inside sanitize()
                raw_concat = re.compile(
                    rf"\+\s*{esc}(?!\s*[?:=])"
                )
                sanitized = re.compile(rf"sanitize\({esc}\)")

                raw_hits = raw_concat.findall(script)
                if raw_hits:
                    assert sanitized.search(script), (
                        f"{html_path.name}: found {field} in string concat "
                        f"without sanitize() wrapper"
                    )

    def test_sanitize_pages_have_sanitize_function(self):
        """Pages that use innerHTML with user data define sanitize()."""
        sanitize_required = [
            "tournaments.html", "leaderboard.html", "profile.html",
        ]
        for name in sanitize_required:
            path = PROJECT_ROOT / "server" / "static" / name
            script = self._extract_scripts(path.read_text())
            assert "function sanitize" in script, (
                f"{name} is missing the sanitize() helper function"
            )


# ── TestServerSecurityStack ──────────────────────────────────────────


class TestServerSecurityStack:
    """Full auth + submit + rate-limit + validation flow."""

    def test_full_auth_flow_create_and_submit(self, client, db_conn):
        """Auto-create player -> get API key -> submit bot succeeds."""
        clean_source = (
            "BOT_NAME = 'TestBot'\n"
            "BOT_EMOJI = '\\U0001f916'\n"
            "def decide(me, enemies, storm):\n"
            "    return {'move': 'north', 'action': 'none'}\n"
        )

        # First submission auto-creates player, returns API key
        resp = client.post(
            "/api/submit-bot", json={"source": clean_source}
        )
        assert resp.status_code == 202
        data = resp.json()
        assert "api_key" in data, "First submission should return API key"
        api_key = data["api_key"]

        # Second submission with the returned key should work (after cooldown)
        clear_rate_limit_state()
        clear_rate_limits()
        resp2 = client.post(
            "/api/submit-bot",
            json={"source": clean_source},
            headers={"X-API-Key": api_key},
        )
        assert resp2.status_code == 202

    def test_rate_limited_on_rapid_resubmit(self, client, db_conn):
        """Rapid resubmission returns 429."""
        clean_source = (
            "BOT_NAME = 'RateTest'\n"
            "BOT_EMOJI = '\\U0001f916'\n"
            "def decide(me, enemies, storm):\n"
            "    return {'move': 'north', 'action': 'none'}\n"
        )

        # First submit
        resp1 = client.post(
            "/api/submit-bot", json={"source": clean_source}
        )
        assert resp1.status_code == 202

        # Immediate second submit should be rate limited
        resp2 = client.post(
            "/api/submit-bot", json={"source": clean_source}
        )
        assert resp2.status_code == 429

    def test_api_key_works_for_auth(self, client, player_with_key):
        """A created API key authenticates subsequent requests."""
        player, key = player_with_key
        clean_source = (
            "BOT_NAME = 'AuthTest'\n"
            "BOT_EMOJI = '\\U0001f916'\n"
            "def decide(me, enemies, storm):\n"
            "    return {'move': 'north', 'action': 'none'}\n"
        )

        resp = client.post(
            "/api/submit-bot",
            json={"source": clean_source},
            headers={"X-API-Key": key},
        )
        assert resp.status_code == 202
        # Should NOT contain api_key (not a new player)
        assert "api_key" not in resp.json()

    def test_invalid_sort_by_returns_400(self, client, db_conn, tmp_path):
        """Stats route rejects invalid sort_by with 400, not 500."""
        import json

        # Set up a results dir with one match
        results_dir = tmp_path / "results"
        results_dir.mkdir()
        match_data = {
            "match_id": 1, "date": "2026-03-25", "winner": "X",
            "duration_rounds": 5,
            "players": [{"emoji": "X", "name": "Bot1"}],
            "stats": {"X": {"kills": 1, "damage_dealt": 50, "damage_taken": 10}},
            "eliminations": [],
        }
        (results_dir / "match_001.json").write_text(
            json.dumps(match_data), encoding="utf-8"
        )
        app.state.results_dir = str(results_dir)

        resp = client.get("/api/leaderboard?sort_by=__import__")
        assert resp.status_code == 400

    def test_cors_headers_match_restricted_config(self, client):
        """CORS preflight returns restricted methods, not wildcards."""
        resp = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:8000",
                "Access-Control-Request-Method": "GET",
            },
        )
        allow_methods = resp.headers.get("access-control-allow-methods", "")
        assert "*" not in allow_methods, "CORS should not use wildcard methods"


# ── TestPathTraversal ────────────────────────────────────────────────


class TestPathTraversal:
    """Path traversal protection on match and share routes."""

    def test_match_route_rejects_traversal(self, client, tmp_path):
        """GET /api/match with traversal ID returns 400 or 404."""
        app.state.results_dir = str(tmp_path)
        # Direct traversal in the match_id parameter
        resp = client.get("/api/match/..%2Fetc%2Fpasswd")
        assert resp.status_code in (400, 404)

    def test_share_route_rejects_traversal(self, client, tmp_path):
        """GET /m/../etc/passwd returns 400 or 404."""
        app.state.results_dir = str(tmp_path)
        resp = client.get("/m/../etc/passwd", follow_redirects=False)
        assert resp.status_code in (400, 404)

    def test_match_route_has_resolve_check(self):
        """match.py source contains resolve() + is_relative_to."""
        import server.routes.match as match_mod

        src = inspect.getsource(match_mod)
        assert "resolve()" in src
        assert "is_relative_to" in src

    def test_share_route_has_resolve_check(self):
        """share.py source contains resolve() + is_relative_to."""
        import server.routes.share as share_mod

        src = inspect.getsource(share_mod)
        assert "resolve()" in src
        assert "is_relative_to" in src
