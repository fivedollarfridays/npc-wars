"""UP-5 P2: worker observability -- stdout logging config + liveness heartbeat.

The compose worker was silent (`server/worker.py` never called
``logging.basicConfig``) and its healthcheck (``python -c "print('ok')"``)
passed even when the poll loop was dead. These tests pin the two mechanisms
that fix that: :mod:`server.logging_setup` and :mod:`server.heartbeat`.
"""

from __future__ import annotations

import logging
import sys
import time

import pytest

from server.heartbeat import (
    HEARTBEAT_MAX_AGE_ENV,
    HEARTBEAT_PATH_ENV,
    heartbeat_age,
    heartbeat_is_fresh,
    heartbeat_max_age,
    heartbeat_path,
    main as heartbeat_main,
    touch_heartbeat,
)
from server.logging_setup import (
    LOG_LEVEL_ENV,
    configure_logging,
    resolve_log_level,
)
from server import worker
from server.submission import SUBMISSION_KIND


@pytest.fixture()
def beat(tmp_path, monkeypatch):
    """Point the heartbeat at a temp file and return its path."""
    path = tmp_path / "worker.heartbeat"
    monkeypatch.setenv(HEARTBEAT_PATH_ENV, str(path))
    monkeypatch.delenv(HEARTBEAT_MAX_AGE_ENV, raising=False)
    return path


class TestResolveLogLevel:
    """Level comes from the env, defaults to INFO, never explodes."""

    def test_default_is_info(self) -> None:
        assert resolve_log_level(None) == logging.INFO

    def test_blank_is_info(self) -> None:
        assert resolve_log_level("  ") == logging.INFO

    def test_named_level_is_honoured(self) -> None:
        assert resolve_log_level("debug") == logging.DEBUG
        assert resolve_log_level("WARNING") == logging.WARNING

    def test_numeric_level_is_honoured(self) -> None:
        assert resolve_log_level("10") == logging.DEBUG

    def test_garbage_falls_back_to_info(self) -> None:
        assert resolve_log_level("loud") == logging.INFO


class TestConfigureLogging:
    """configure_logging installs a root stdout handler at the env level."""

    def test_returns_configured_level(self, monkeypatch) -> None:
        monkeypatch.delenv(LOG_LEVEL_ENV, raising=False)
        assert configure_logging() == logging.INFO

    def test_env_override(self, monkeypatch) -> None:
        monkeypatch.setenv(LOG_LEVEL_ENV, "DEBUG")
        assert configure_logging() == logging.DEBUG
        assert logging.getLogger().level == logging.DEBUG

    def test_installs_a_stdout_handler(self, monkeypatch) -> None:
        monkeypatch.delenv(LOG_LEVEL_ENV, raising=False)
        configure_logging()
        streams = [
            getattr(h, "stream", None) for h in logging.getLogger().handlers
        ]
        assert sys.stdout in streams, "worker logs must go to stdout"

    def test_reconfigures_even_if_already_configured(self, monkeypatch) -> None:
        """force=True: an inherited config must not silence the worker."""
        monkeypatch.delenv(LOG_LEVEL_ENV, raising=False)
        logging.basicConfig(level=logging.CRITICAL)
        configure_logging()
        assert logging.getLogger().level == logging.INFO


class TestHeartbeatFile:
    """The loop touches a file each cycle; the healthcheck reads its age."""

    def test_path_defaults_and_env_override(self, monkeypatch, tmp_path) -> None:
        monkeypatch.delenv(HEARTBEAT_PATH_ENV, raising=False)
        assert heartbeat_path().endswith(".heartbeat")
        monkeypatch.setenv(HEARTBEAT_PATH_ENV, str(tmp_path / "hb"))
        assert heartbeat_path() == str(tmp_path / "hb")

    def test_max_age_defaults_and_env_override(self, monkeypatch) -> None:
        monkeypatch.delenv(HEARTBEAT_MAX_AGE_ENV, raising=False)
        assert heartbeat_max_age() > 0
        monkeypatch.setenv(HEARTBEAT_MAX_AGE_ENV, "5")
        assert heartbeat_max_age() == 5.0
        monkeypatch.setenv(HEARTBEAT_MAX_AGE_ENV, "not-a-number")
        assert heartbeat_max_age() > 0

    def test_touch_creates_the_file(self, beat) -> None:
        assert not beat.exists()
        touch_heartbeat()
        assert beat.is_file()

    def test_touch_creates_missing_parent_dirs(self, tmp_path, monkeypatch) -> None:
        nested = tmp_path / "deep" / "dir" / "worker.heartbeat"
        monkeypatch.setenv(HEARTBEAT_PATH_ENV, str(nested))
        touch_heartbeat()
        assert nested.is_file()

    def test_age_is_none_when_missing(self, beat) -> None:
        assert heartbeat_age() is None

    def test_age_is_small_right_after_touch(self, beat) -> None:
        touch_heartbeat()
        age = heartbeat_age()
        assert age is not None and age < 5


class TestHeartbeatFreshness:
    """A dead loop must FAIL the healthcheck -- that was the P2 bug."""

    def test_missing_heartbeat_is_not_fresh(self, beat) -> None:
        assert heartbeat_is_fresh() is False

    def test_just_touched_is_fresh(self, beat) -> None:
        touch_heartbeat()
        assert heartbeat_is_fresh() is True

    def test_stale_heartbeat_is_not_fresh(self, beat, monkeypatch) -> None:
        touch_heartbeat()
        monkeypatch.setenv(HEARTBEAT_MAX_AGE_ENV, "0.0001")
        time.sleep(0.01)
        assert heartbeat_is_fresh() is False

    def test_main_exits_zero_when_fresh(self, beat) -> None:
        touch_heartbeat()
        assert heartbeat_main() == 0

    def test_main_exits_nonzero_when_stale(self, beat) -> None:
        assert heartbeat_main() != 0


class TestWorkerPollCycle:
    """The loop proves liveness every cycle and survives a bad job."""

    def test_idle_cycle_touches_the_heartbeat(self, beat, monkeypatch) -> None:
        """An empty queue is still a live loop -- it must beat."""
        monkeypatch.setattr(worker, "dequeue_match", lambda timeout=1: None)
        assert worker.poll_once(object()) is False
        assert beat.is_file()

    def test_job_cycle_touches_the_heartbeat(self, beat, monkeypatch) -> None:
        monkeypatch.setattr(
            worker, "dequeue_match", lambda timeout=1: {"kind": "other"}
        )
        monkeypatch.setattr(worker, "_process_regular_job", lambda conn, job: None)
        assert worker.poll_once(object()) is True
        assert beat.is_file()

    def test_submission_jobs_route_to_the_sandboxed_runner(
        self, beat, monkeypatch
    ) -> None:
        seen: list[dict] = []
        monkeypatch.setattr(
            worker,
            "dequeue_match",
            lambda timeout=1: {"kind": SUBMISSION_KIND, "job_id": "j1"},
        )
        monkeypatch.setattr(
            worker, "run_submission_job", lambda conn, job: seen.append(job)
        )
        worker.poll_once(object())
        assert [j["job_id"] for j in seen] == ["j1"]

    def test_a_failing_job_does_not_kill_the_loop(
        self, beat, monkeypatch, caplog
    ) -> None:
        """Log-and-continue: one poisoned job must not end the worker."""
        def boom(conn, job):
            raise RuntimeError("job exploded")

        monkeypatch.setattr(
            worker, "dequeue_match", lambda timeout=1: {"kind": "other"}
        )
        monkeypatch.setattr(worker, "_process_regular_job", boom)
        with caplog.at_level(logging.ERROR):
            assert worker.poll_once(object()) is True
        assert "job exploded" in caplog.text

    def test_startup_failure_is_logged_before_exit(self, beat, capsys) -> None:
        """Strict-mode Redis failure must explain itself, not exit silently."""
        import server.queue as queue_mod

        def boom() -> str:
            raise queue_mod.QueueBackendUnavailableError("redis unreachable")

        original = worker.init_backend
        worker.init_backend = boom  # type: ignore[assignment]
        try:
            assert worker.main() == 1
        finally:
            worker.init_backend = original  # type: ignore[assignment]
            logging.basicConfig(force=True)
        captured = capsys.readouterr()
        assert "redis unreachable" in captured.out + captured.err

    def test_dequeue_failure_is_logged_and_survived(
        self, beat, monkeypatch, caplog
    ) -> None:
        """A transient queue/redis error must not silently exit the worker."""
        def boom(timeout=1):
            raise ConnectionError("redis went away")

        monkeypatch.setattr(worker, "dequeue_match", boom)
        with caplog.at_level(logging.ERROR):
            assert worker.poll_once(object()) is False
        assert "redis went away" in caplog.text
        assert beat.is_file(), "a beat still proves the loop itself is running"
