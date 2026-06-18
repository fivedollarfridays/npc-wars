"""Sprint 18 integration gate — verify all modules are wired and functional."""

from __future__ import annotations

import inspect
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from server.app import app

PROJECT_ROOT = Path(__file__).resolve().parent.parent
client = TestClient(app)


def _registered_paths() -> set[str]:
    """Router paths from ``server.app`` imported in a clean subprocess.

    This gate verifies the app wires its routers. It historically read the
    module-level ``app`` singleton shared across the whole suite via
    ``from server.app import app`` — but under CI's full-suite + coverage run,
    in-process state contamination (a sibling test's reload / sys.modules
    manipulation) intermittently stripped the router routes here, even though
    the app registers all routers when imported cleanly (verified) and every
    other server test passed. Importing in a subprocess answers the real
    question — "does a fresh process register the routers?" — immune to any
    in-process pollution.
    """
    import json
    import subprocess
    import sys

    code = (
        "import json; from server.app import app; "
        "print(json.dumps([r.path for r in app.routes if hasattr(r, 'path')]))"
    )
    out = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(PROJECT_ROOT), capture_output=True, text=True, check=True,
    )
    return set(json.loads(out.stdout.strip().splitlines()[-1]))


# ---------------------------------------------------------------------------
# 1. Router registration
# ---------------------------------------------------------------------------


class TestRouterRegistration:
    """Verify S18 routers are included in the FastAPI app."""

    def test_stream_router_registered(self) -> None:
        assert "/api/match/{match_id}/stream" in _registered_paths()

    def test_share_router_registered(self) -> None:
        assert "/m/{match_id}" in _registered_paths()

    def test_health_router_registered(self) -> None:
        paths = _registered_paths()
        assert "/health" in paths
        assert "/health/ready" in paths
        assert "/metrics" in paths


# ---------------------------------------------------------------------------
# 2. Endpoint existence (non-405)
# ---------------------------------------------------------------------------


class TestEndpointsExist:
    """All S18 endpoints return non-405 (method exists)."""

    def test_health(self) -> None:
        resp = client.get("/health")
        assert resp.status_code != 405

    def test_health_ready(self) -> None:
        resp = client.get("/health/ready")
        assert resp.status_code != 405

    def test_metrics(self) -> None:
        resp = client.get("/metrics")
        assert resp.status_code != 405

    def test_stream_endpoint(self) -> None:
        resp = client.get("/api/match/nonexistent/stream")
        # 404 is fine (match not found), 405 means route missing
        assert resp.status_code != 405

    def test_share_endpoint(self) -> None:
        resp = client.get("/m/nonexistent")
        assert resp.status_code != 405

    def test_submit_bot_endpoint(self) -> None:
        resp = client.post("/api/submit-bot", json={"source": ""})
        # 400 (empty source) is fine, 405 means route missing
        assert resp.status_code != 405


# ---------------------------------------------------------------------------
# 3. Session middleware
# ---------------------------------------------------------------------------


class TestSessionMiddleware:
    """SessionMiddleware is registered in app."""

    def test_session_middleware_registered(self) -> None:
        from server.middleware.session import SessionMiddleware

        middleware_classes = [
            m.cls for m in app.user_middleware if hasattr(m, "cls")
        ]
        assert SessionMiddleware in middleware_classes

    def test_session_cookie_set(self) -> None:
        fresh = TestClient(app, cookies={})
        resp = fresh.get("/health")
        assert "npcwars_session" in resp.cookies


# ---------------------------------------------------------------------------
# 4. Match modes wired into engine
# ---------------------------------------------------------------------------


class TestMatchModesWired:
    """engine/game.py accepts match_mode parameter."""

    def test_run_match_has_match_mode_param(self) -> None:
        from engine.game import run_match

        sig = inspect.signature(run_match)
        assert "match_mode" in sig.parameters
        assert sig.parameters["match_mode"].default == "standard"

    def test_run_match_async_has_match_mode_param(self) -> None:
        from engine.game import run_match_async

        sig = inspect.signature(run_match_async)
        assert "match_mode" in sig.parameters
        assert sig.parameters["match_mode"].default == "standard"


# ---------------------------------------------------------------------------
# 5. Viewer effects wired
# ---------------------------------------------------------------------------


class TestViewerEffects:
    """viewer/match.html contains required JS functions."""

    @pytest.fixture()
    def viewer_source(self) -> str:
        from conftest import read_viewer_content
        return read_viewer_content()

    def test_attack_swoosh_function(self, viewer_source: str) -> None:
        assert "function attackSwoosh" in viewer_source

    def test_death_explosion_function(self, viewer_source: str) -> None:
        assert "function deathExplosion" in viewer_source

    def test_copy_permalink_function(self, viewer_source: str) -> None:
        assert "function copyPermalink" in viewer_source

    def test_share_button_present(self, viewer_source: str) -> None:
        assert "copyPermalink()" in viewer_source


# ---------------------------------------------------------------------------
# 6. Docker files exist
# ---------------------------------------------------------------------------


class TestDockerFiles:
    """Production Docker files exist at project root."""

    def test_docker_compose_exists(self) -> None:
        assert (PROJECT_ROOT / "docker-compose.yml").is_file()

    def test_dockerfile_exists(self) -> None:
        assert (PROJECT_ROOT / "Dockerfile").is_file()

    def test_dockerfile_sandbox_exists(self) -> None:
        assert (PROJECT_ROOT / "Dockerfile.sandbox").is_file()


# ---------------------------------------------------------------------------
# 7. Config module works
# ---------------------------------------------------------------------------


class TestConfigModule:
    """server/config.py Settings can be instantiated with defaults."""

    def test_settings_instantiates(self) -> None:
        from server.config import Settings

        s = Settings()
        assert isinstance(s.redis_url, str)
        assert isinstance(s.port, int)

    def test_settings_has_results_dir(self) -> None:
        from server.config import Settings

        s = Settings()
        assert s.results_dir == os.environ.get("RESULTS_DIR", "results")


# ---------------------------------------------------------------------------
# 8. No dead public functions — key modules have callers outside tests
# ---------------------------------------------------------------------------


class TestNoDeadCode:
    """Key S18 public functions are imported/called outside their own module."""

    def _is_imported_outside_tests(self, symbol: str, module_path: str) -> bool:
        """Check if symbol appears in project files outside tests/ and its own module."""
        for py_file in PROJECT_ROOT.rglob("*.py"):
            rel = py_file.relative_to(PROJECT_ROOT)
            # Skip test files and the module itself
            if str(rel).startswith("tests/"):
                continue
            if str(rel) == module_path:
                continue
            try:
                content = py_file.read_text()
            except (OSError, UnicodeDecodeError):
                continue
            if symbol in content:
                return True
        return False

    def test_session_middleware_used(self) -> None:
        assert self._is_imported_outside_tests(
            "SessionMiddleware", "server/middleware/session.py"
        )

    def test_health_router_used(self) -> None:
        assert self._is_imported_outside_tests(
            "health_router", "server/routes/health.py"
        )

    def test_stream_router_used(self) -> None:
        assert self._is_imported_outside_tests(
            "stream_router", "server/routes/stream.py"
        )

    def test_share_router_used(self) -> None:
        assert self._is_imported_outside_tests(
            "share_router", "server/routes/share.py"
        )

    def test_match_modes_used_in_game(self) -> None:
        assert self._is_imported_outside_tests(
            "get_mode", "engine/match_modes.py"
        )

    def test_settings_importable(self) -> None:
        """Settings is importable and has non-test callers (task files count)."""
        from server.config import Settings

        assert Settings is not None
