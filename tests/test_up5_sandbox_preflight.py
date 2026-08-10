"""UP-5 P1: the worker must be able to prove it can reach the sandbox.

In the compose topology the worker had neither a ``docker`` CLI nor a mounted
``/var/run/docker.sock``, so ``run_sandboxed()`` fail-closed on every
submission -- and the only signal was a per-job error. The worker now runs a
startup preflight that says, in one line, whether the CLI, the daemon and the
``npcwars-sandbox:latest`` image are actually there.
"""

from __future__ import annotations

import logging
import subprocess
from unittest.mock import patch

from server.docker_sandbox import DOCKER_IMAGE, sandbox_preflight


def _run_result(returncode: int):
    return subprocess.CompletedProcess(args=[], returncode=returncode)


class TestSandboxPreflight:
    """Reports CLI/daemon and image availability without ever raising."""

    def test_all_present_is_ok(self) -> None:
        with patch("server.docker_sandbox.subprocess.run", return_value=_run_result(0)):
            report = sandbox_preflight()
        assert report["docker"] is True
        assert report["image"] is True
        assert report["ok"] is True

    def test_missing_docker_cli_is_not_ok(self) -> None:
        with patch(
            "server.docker_sandbox.subprocess.run", side_effect=FileNotFoundError
        ):
            report = sandbox_preflight()
        assert report["docker"] is False
        assert report["image"] is False
        assert report["ok"] is False

    def test_daemon_up_but_image_missing_is_not_ok(self) -> None:
        """The exact state after a fresh `docker compose up` with no image build."""
        calls: list[list[str]] = []

        def fake_run(cmd, *args, **kwargs):
            calls.append(cmd)
            return _run_result(0 if cmd[:2] == ["docker", "info"] else 1)

        with patch("server.docker_sandbox.subprocess.run", side_effect=fake_run):
            report = sandbox_preflight()
        assert report["docker"] is True
        assert report["image"] is False
        assert report["ok"] is False
        assert any(DOCKER_IMAGE in c for c in calls), "image must be inspected by name"

    def test_timeout_is_reported_not_raised(self) -> None:
        with patch(
            "server.docker_sandbox.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="docker", timeout=5),
        ):
            report = sandbox_preflight()
        assert report["ok"] is False

    def test_report_names_the_image(self) -> None:
        with patch("server.docker_sandbox.subprocess.run", return_value=_run_result(0)):
            assert sandbox_preflight()["image_name"] == DOCKER_IMAGE


class TestWorkerStartupReport:
    """The worker surfaces the preflight in its logs at startup."""

    def test_logs_error_when_sandbox_unreachable(self, caplog) -> None:
        from server import worker

        bad = {"docker": False, "image": False, "ok": False, "image_name": DOCKER_IMAGE}
        with patch("server.worker.sandbox_preflight", return_value=bad):
            with caplog.at_level(logging.ERROR, logger="server.worker"):
                worker.log_sandbox_preflight()
        assert DOCKER_IMAGE in caplog.text
        assert "docker" in caplog.text.lower()

    def test_logs_info_when_sandbox_ready(self, caplog) -> None:
        from server import worker

        good = {"docker": True, "image": True, "ok": True, "image_name": DOCKER_IMAGE}
        with patch("server.worker.sandbox_preflight", return_value=good):
            with caplog.at_level(logging.INFO, logger="server.worker"):
                worker.log_sandbox_preflight()
        assert DOCKER_IMAGE in caplog.text
        assert "ERROR" not in caplog.text
