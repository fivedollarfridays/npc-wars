"""Tests for server.worker -- match queue worker process."""

from __future__ import annotations

import signal
from unittest.mock import patch

import server.worker as w
from server.queue import InMemoryQueue, dequeue_match as real_dequeue, enqueue_match, set_backend
from server.worker import _shutdown, main


def _run_worker_with_mock(fake_match_data: dict, **run_match_kwargs):
    """Run the worker loop with mocked run_match/write_match, stopping after queue drains.

    Returns (mock_run, mock_write) for assertions.
    """
    def _patched_dequeue(timeout=1):
        result = real_dequeue(timeout=0)
        if result is None:
            w._running = False
        return result

    with (
        patch("server.worker.run_match", return_value=fake_match_data) as mock_run,
        patch("server.worker.write_match") as mock_write,
        patch("server.worker.dequeue_match", side_effect=_patched_dequeue),
    ):
        w._running = True
        main()
    return mock_run, mock_write


class TestWorkerProcessesJob:
    """Verify worker dequeues and runs matches."""

    def test_worker_processes_single_job(self) -> None:
        """Worker dequeues a job, calls run_match, and writes results."""
        set_backend(InMemoryQueue())
        job = {
            "bot_configs": [{"name": "A"}, {"name": "B"}],
            "match_id": 42,
            "seed": 99,
            "results_dir": "/tmp/test_results",
        }
        enqueue_match(job)
        fake_match_data = {"match_id": 42, "winner": "A"}

        mock_run, mock_write = _run_worker_with_mock(fake_match_data)

        mock_run.assert_called_once_with(
            [{"name": "A"}, {"name": "B"}], match_id=42, seed=99,
        )
        mock_write.assert_called_once_with(fake_match_data, "/tmp/test_results")

    def test_worker_uses_defaults_for_missing_fields(self) -> None:
        """Worker uses default match_id=1 and results_dir='results'."""
        set_backend(InMemoryQueue())
        enqueue_match({"bot_configs": [{"name": "X"}]})
        fake_match_data = {"match_id": 1, "winner": "X"}

        mock_run, mock_write = _run_worker_with_mock(fake_match_data)

        mock_run.assert_called_once_with([{"name": "X"}], match_id=1, seed=None)
        mock_write.assert_called_once_with(fake_match_data, "results")


class TestWorkerShutdown:
    """Verify graceful shutdown signal handling."""

    def test_shutdown_sets_running_false(self) -> None:
        w._running = True
        _shutdown(signal.SIGTERM, None)
        assert w._running is False
