"""UP-5: the API container must agree with the worker about where data lives.

``server/app.py`` hardcoded ``app.state.results_dir = "results"`` while
docker-compose set ``RESULTS_DIR=/data/results`` on both services. In compose
that means the worker writes ``match_NNN.json`` into its *own* container's
``/app/results`` while the API reads its own -- so a completed submission is
never visible at ``/api/match/{id}``, ``/api/match/{id}/stream``, or on the
leaderboard. Same class of split as the queue one (P3).

Also covered: the API logs its queue backend at startup, so an app/worker
split brain is visible in the first lines of both containers' logs.
"""

from __future__ import annotations

import importlib
import logging

import pytest

import server.app as app_module
from server.queue import InMemoryQueue, set_backend


@pytest.fixture()
def reloaded_app(monkeypatch, tmp_path):
    """Reload server.app with an isolated env; restore the default after."""

    def _reload(**env: str):
        monkeypatch.setenv("DB_PATH", str(tmp_path / "npcwars.db"))
        for key, value in env.items():
            if value is None:
                monkeypatch.delenv(key, raising=False)
            else:
                monkeypatch.setenv(key, value)
        return importlib.reload(app_module)

    yield _reload
    monkeypatch.undo()
    importlib.reload(app_module)


class TestResultsDirWiring:
    """RESULTS_DIR must reach app.state, or app and worker read different dirs."""

    def test_results_dir_comes_from_the_environment(self, reloaded_app) -> None:
        mod = reloaded_app(RESULTS_DIR="/data/results")
        assert mod.app.state.results_dir == "/data/results"

    def test_results_dir_defaults_to_results(self, reloaded_app, monkeypatch) -> None:
        monkeypatch.delenv("RESULTS_DIR", raising=False)
        mod = reloaded_app()
        assert mod.app.state.results_dir == "results"

    def test_db_path_is_exposed_on_state(self, reloaded_app, tmp_path) -> None:
        """/health's sqlite probe reads app.state.db_path -- it must be real."""
        mod = reloaded_app()
        assert mod.app.state.db_path == str(tmp_path / "npcwars.db")


class TestStartupBackendLogging:
    """The app announces its queue backend on startup (UP-5 P3)."""

    def test_lifespan_logs_the_queue_backend_to_stdout(self, capsys) -> None:
        """Asserted on stdout, not caplog: that is where Docker reads logs."""
        from fastapi.testclient import TestClient

        set_backend(InMemoryQueue())
        try:
            with TestClient(app_module.app):
                pass
        finally:
            set_backend(None)
            logging.basicConfig(force=True)
        out = capsys.readouterr().out
        assert "Queue backend ready: in-memory" in out

    def test_lifespan_logs_the_results_dir_to_stdout(self, capsys) -> None:
        """The app/worker results-dir agreement must be checkable from logs."""
        from fastapi.testclient import TestClient

        set_backend(InMemoryQueue())
        try:
            with TestClient(app_module.app):
                pass
        finally:
            set_backend(None)
            logging.basicConfig(force=True)
        assert "Results dir:" in capsys.readouterr().out
