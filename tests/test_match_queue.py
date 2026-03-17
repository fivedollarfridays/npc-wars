"""Tests for server.queue -- Redis match queue with in-memory backend."""

from __future__ import annotations

from server.queue import (
    InMemoryQueue,
    dequeue_match,
    enqueue_match,
    set_backend,
)


def _fresh_backend() -> InMemoryQueue:
    """Create and install a fresh in-memory backend for each test."""
    backend = InMemoryQueue()
    set_backend(backend)
    return backend


class TestInMemoryQueue:
    """Unit tests for InMemoryQueue backend directly."""

    def test_lpush_returns_length(self) -> None:
        q = InMemoryQueue()
        assert q.lpush("k", "a") == 1
        assert q.lpush("k", "b") == 2

    def test_brpop_empty_returns_none(self) -> None:
        q = InMemoryQueue()
        assert q.brpop("k", timeout=0) is None

    def test_brpop_returns_oldest_first(self) -> None:
        q = InMemoryQueue()
        q.lpush("k", "first")
        q.lpush("k", "second")
        result = q.brpop("k", timeout=0)
        assert result == ("k", "first")

    def test_brpop_drains_queue(self) -> None:
        q = InMemoryQueue()
        q.lpush("k", "only")
        q.brpop("k", timeout=0)
        assert q.brpop("k", timeout=0) is None


class TestEnqueueDequeue:
    """Integration tests using enqueue_match / dequeue_match API."""

    def test_enqueue_dequeue_roundtrip(self) -> None:
        _fresh_backend()
        job = {"bot_configs": [{"name": "Alice"}], "match_id": 42}
        enqueue_match(job)
        result = dequeue_match(timeout=0)
        assert result == job

    def test_dequeue_empty_returns_none(self) -> None:
        _fresh_backend()
        assert dequeue_match(timeout=0) is None

    def test_enqueue_preserves_nested_data(self) -> None:
        _fresh_backend()
        job = {
            "bot_configs": [{"name": "A", "hp": 100}, {"name": "B", "hp": 100}],
            "match_id": 7,
            "seed": 12345,
            "results_dir": "results",
        }
        enqueue_match(job)
        assert dequeue_match(timeout=0) == job

    def test_fifo_order(self) -> None:
        _fresh_backend()
        enqueue_match({"id": 1})
        enqueue_match({"id": 2})
        enqueue_match({"id": 3})
        assert dequeue_match(timeout=0) == {"id": 1}
        assert dequeue_match(timeout=0) == {"id": 2}
        assert dequeue_match(timeout=0) == {"id": 3}
        assert dequeue_match(timeout=0) is None
