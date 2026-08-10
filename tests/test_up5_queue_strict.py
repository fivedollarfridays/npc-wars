"""UP-5 P3: the queue must never silently split the app from the worker.

``_get_backend()`` fell back to an in-process ``InMemoryQueue`` whenever Redis
was unreachable. In compose that is a silent data-loss shape: the app enqueues
into its own process memory, the worker polls its own, and a 202 submit
produces no match and no error anywhere.

The fallback stays (it is legitimate for local dev and tests) but a deployment
can now demand Redis with ``NPCWARS_QUEUE_STRICT=1``, in which case an
unreachable Redis is a loud failure instead of a stranded job.
"""

from __future__ import annotations

import logging
import sys
from unittest.mock import MagicMock, patch

import pytest

from server import queue as queue_mod
from server.queue import (
    QUEUE_STRICT_ENV,
    InMemoryQueue,
    QueueBackendUnavailableError,
    backend_name,
    init_backend,
    queue_strict_mode,
    set_backend,
)


@pytest.fixture(autouse=True)
def _reset_backend():
    set_backend(None)
    yield
    set_backend(None)


def _broken_redis_module() -> MagicMock:
    """A stand-in ``redis`` module whose ping() always fails to connect."""
    mock_redis = MagicMock()
    mock_redis.Redis.from_url.return_value.ping.side_effect = ConnectionError(
        "Connection refused"
    )
    return mock_redis


class TestStrictModeFlag:
    """Exact-match opt-in, same fail-closed style as the sandbox gate."""

    def test_off_by_default(self, monkeypatch) -> None:
        monkeypatch.delenv(QUEUE_STRICT_ENV, raising=False)
        assert queue_strict_mode() is False

    def test_on_for_exactly_one(self, monkeypatch) -> None:
        monkeypatch.setenv(QUEUE_STRICT_ENV, "1")
        assert queue_strict_mode() is True

    def test_truthy_lookalikes_are_off(self, monkeypatch) -> None:
        for value in ("true", "yes", "0", "", "on"):
            monkeypatch.setenv(QUEUE_STRICT_ENV, value)
            assert queue_strict_mode() is False, value


class TestStrictModeBehaviour:
    """Strict: unreachable Redis raises. Default: fallback survives."""

    def test_strict_raises_instead_of_falling_back(self, monkeypatch) -> None:
        monkeypatch.setenv(QUEUE_STRICT_ENV, "1")
        with patch.dict(sys.modules, {"redis": _broken_redis_module()}):
            with pytest.raises(QueueBackendUnavailableError):
                queue_mod._get_backend()

    def test_strict_error_names_the_url_and_the_switch(self, monkeypatch) -> None:
        monkeypatch.setenv(QUEUE_STRICT_ENV, "1")
        monkeypatch.setenv("REDIS_URL", "redis://redis:6379")
        with patch.dict(sys.modules, {"redis": _broken_redis_module()}):
            with pytest.raises(QueueBackendUnavailableError) as excinfo:
                queue_mod._get_backend()
        message = str(excinfo.value)
        assert "redis://redis:6379" in message
        assert QUEUE_STRICT_ENV in message

    def test_strict_does_not_leave_an_in_memory_backend_behind(
        self, monkeypatch
    ) -> None:
        """A failed strict connect must not poison later calls with a fallback."""
        monkeypatch.setenv(QUEUE_STRICT_ENV, "1")
        with patch.dict(sys.modules, {"redis": _broken_redis_module()}):
            with pytest.raises(QueueBackendUnavailableError):
                queue_mod._get_backend()
        assert queue_mod._backend is None

    def test_default_still_falls_back(self, monkeypatch) -> None:
        monkeypatch.delenv(QUEUE_STRICT_ENV, raising=False)
        with patch.dict(sys.modules, {"redis": _broken_redis_module()}):
            assert isinstance(queue_mod._get_backend(), InMemoryQueue)

    def test_strict_enqueue_raises_rather_than_stranding_the_job(
        self, monkeypatch
    ) -> None:
        monkeypatch.setenv(QUEUE_STRICT_ENV, "1")
        with patch.dict(sys.modules, {"redis": _broken_redis_module()}):
            with pytest.raises(QueueBackendUnavailableError):
                queue_mod.enqueue_match({"job_id": "stranded"})


class TestBackendVisibility:
    """Both processes log which backend they got -- a split becomes obvious."""

    def test_backend_name_reports_in_memory(self) -> None:
        set_backend(InMemoryQueue())
        assert backend_name() == "in-memory"

    def test_backend_name_reports_redis(self) -> None:
        set_backend(MagicMock())
        assert backend_name() == "redis"

    def test_init_backend_logs_the_choice(self, caplog) -> None:
        set_backend(InMemoryQueue())
        with caplog.at_level(logging.INFO, logger="server.queue"):
            assert init_backend() == "in-memory"
        assert "in-memory" in caplog.text

    def test_init_backend_propagates_strict_failure(self, monkeypatch) -> None:
        monkeypatch.setenv(QUEUE_STRICT_ENV, "1")
        with patch.dict(sys.modules, {"redis": _broken_redis_module()}):
            with pytest.raises(QueueBackendUnavailableError):
                init_backend()
