"""Sprint 17 integration gate — verify all server modules are wired and functional."""

from __future__ import annotations

import ast
import importlib
import inspect
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from server.app import app

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ── Cycle 1: Router Registration ────────────────────────────────────


class TestRouterRegistration:
    """Verify all expected routers are wired into the FastAPI app.

    These used to grep ``server/app.py`` for literal import lines. That broke
    the moment the routers moved behind ``server.routes.ALL_ROUTERS`` (UP-5,
    to get app.py under the import limit) -- and it was always the weaker
    check: the import text can be present while registration is broken. The
    OpenAPI schema is built from the fully resolved route table, so it
    asserts the property the import line was only a proxy for. Same shape as
    TestRouterRegistration in test_s18_integration.py.
    """

    @staticmethod
    def _registered_paths() -> set[str]:
        return set(app.openapi()["paths"])

    def test_registration_probe_is_not_vacuous(self) -> None:
        """Positive control: a path that is NOT registered must be absent."""
        paths = self._registered_paths()
        assert paths
        assert "/api/definitely-not-a-route" not in paths

    def test_submit_router_registered(self) -> None:
        assert "/api/submit-bot" in self._registered_paths()

    def test_match_router_registered(self) -> None:
        assert "/api/match/{match_id}" in self._registered_paths()

    def test_stats_router_registered(self) -> None:
        paths = self._registered_paths()
        assert "/api/leaderboard" in paths
        assert "/api/stats/{player_id}" in paths


# ── Cycle 2: Endpoint Existence (non-405) ───────────────────────────


class TestEndpointsExist:
    """All S17 endpoints respond with non-405 (Method Not Allowed)."""

    @pytest.fixture()
    def client(self, tmp_path: Path) -> TestClient:
        app.state.results_dir = str(tmp_path)
        return TestClient(app, raise_server_exceptions=False)

    def test_health(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code != 405

    def test_submit_bot(self, client: TestClient) -> None:
        resp = client.post("/api/submit-bot", json={"source": ""})
        assert resp.status_code != 405

    def test_match_by_id(self, client: TestClient) -> None:
        resp = client.get("/api/match/test123")
        assert resp.status_code != 405

    def test_stats_by_id(self, client: TestClient) -> None:
        resp = client.get("/api/stats/player1")
        assert resp.status_code != 405

    def test_leaderboard(self, client: TestClient) -> None:
        resp = client.get("/api/leaderboard")
        assert resp.status_code != 405


# ── Cycle 3: Static Mount ───────────────────────────────────────────


class TestStaticMount:
    """The static directory is mounted and editor.html is accessible."""

    def test_editor_html_accessible(self) -> None:
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/static/editor.html")
        # Should be 200 if file exists, NOT 404 from missing mount
        assert resp.status_code == 200
        assert "editor" in resp.text.lower() or "monaco" in resp.text.lower()


# ── Cycle 4: Wiring Checks (Source Inspection) ──────────────────────


class TestWiring:
    """Lobby calls enqueue_match and generate_fill_bots."""

    def test_lobby_trigger_calls_enqueue_match(self) -> None:
        source = (PROJECT_ROOT / "server" / "lobby.py").read_text()
        assert "enqueue_match" in source
        # Verify it's actually called in _trigger_match
        tree = ast.parse(source)
        trigger_fn = _get_function(tree, "_trigger_match")
        assert trigger_fn is not None, "_trigger_match not found in lobby.py"
        calls = _get_call_names(trigger_fn)
        assert "enqueue_match" in calls

    def test_fill_bots_calls_generate_fill_bots(self) -> None:
        source = (PROJECT_ROOT / "server" / "lobby.py").read_text()
        assert "generate_fill_bots" in source
        tree = ast.parse(source)
        fill_fn = _get_function(tree, "_get_fill_bots")
        assert fill_fn is not None, "_get_fill_bots not found in lobby.py"
        calls = _get_call_names(fill_fn)
        assert "generate_fill_bots" in calls


# ── Cycle 5: DB Module Exports ──────────────────────────────────────


class TestDBExports:
    """server/db.py exports all required functions."""

    REQUIRED = [
        "init_db",
        "create_player",
        "get_player",
        "list_players",
        "create_session",
        "get_session",
        "expire_session",
    ]

    def test_all_db_functions_exported(self) -> None:
        import server.db as db_mod

        for name in self.REQUIRED:
            assert hasattr(db_mod, name), f"server.db missing: {name}"
            assert callable(getattr(db_mod, name)), f"server.db.{name} not callable"


# ── Cycle 6: No Dead Public Functions ────────────────────────────────


class TestNoDeadCode:
    """Every public function in server/*.py has a caller outside tests.

    server.db functions are a standalone player registry (T17.9) designed
    for route wiring in S18+.  They are excluded here but verified by
    TestDBExports.  server.queue.set_backend is a DI helper used only
    from test fixtures.
    """

    SERVER_MODULES = [
        "server.app",
        "server.fill_bots",
        "server.lobby",
        "server.queue",
        "server.worker",
    ]

    # Functions intentionally public but only consumed from tests / future routes
    KNOWN_API_ONLY: set[str] = {
        "server.queue.set_backend",  # DI for tests
    }

    def test_no_dead_public_functions(self) -> None:
        # Collect all public function names per module
        public_fns: dict[str, list[str]] = {}
        for mod_name in self.SERVER_MODULES:
            mod = importlib.import_module(mod_name)
            fns = [
                name
                for name, obj in inspect.getmembers(mod, inspect.isfunction)
                if not name.startswith("_")
                and obj.__module__ == mod_name
            ]
            if fns:
                public_fns[mod_name] = fns

        # Gather all source text from non-test Python files
        all_source = ""
        for py_file in PROJECT_ROOT.rglob("*.py"):
            if "test" in py_file.name or "__pycache__" in str(py_file):
                continue
            all_source += py_file.read_text(errors="ignore") + "\n"

        dead: list[str] = []
        for mod_name, fns in public_fns.items():
            for fn in fns:
                qualified = f"{mod_name}.{fn}"
                if qualified in self.KNOWN_API_ONLY:
                    continue
                # Count occurrences: must appear more than just its def line
                pattern = re.compile(rf"\b{fn}\b")
                hits = pattern.findall(all_source)
                # At minimum: 1 def + 1 call = 2 occurrences
                if len(hits) < 2:
                    dead.append(qualified)

        assert not dead, f"Dead public functions with no callers: {dead}"

    def test_db_module_not_dead(self) -> None:
        """server.db is a standalone registry — verify it's importable and tested."""
        import server.db as db_mod

        public = [n for n in dir(db_mod) if not n.startswith("_") and callable(getattr(db_mod, n))]
        assert len(public) >= 7, f"Expected >=7 public db functions, got {len(public)}"


# ── Cycle 7: Dependencies in pyproject.toml ──────────────────────────


class TestDependencies:
    """pyproject.toml includes all required server dependencies."""

    REQUIRED_DEPS = ["fastapi", "uvicorn", "redis"]
    REQUIRED_DEV_DEPS = ["httpx"]

    def test_runtime_deps(self) -> None:
        toml_text = (PROJECT_ROOT / "pyproject.toml").read_text()
        for dep in self.REQUIRED_DEPS:
            assert dep in toml_text, f"Missing runtime dep: {dep}"

    def test_dev_deps(self) -> None:
        toml_text = (PROJECT_ROOT / "pyproject.toml").read_text()
        for dep in self.REQUIRED_DEV_DEPS:
            assert dep in toml_text, f"Missing dev dep: {dep}"


# ── AST Helpers ──────────────────────────────────────────────────────


def _get_function(tree: ast.Module, name: str) -> ast.FunctionDef | None:
    """Find a top-level or nested function by name."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == name:
                return node
    return None


def _get_call_names(node: ast.AST) -> list[str]:
    """Extract function call names from an AST node."""
    names: list[str] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            if isinstance(child.func, ast.Name):
                names.append(child.func.id)
            elif isinstance(child.func, ast.Attribute):
                names.append(child.func.attr)
    return names
