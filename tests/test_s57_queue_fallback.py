"""Tests for Redis fallback to InMemoryQueue (T57.1)."""

from __future__ import annotations

from unittest.mock import patch

from server.queue import InMemoryQueue, set_backend


# ── Cycle 1: Auto-fallback + is_in_memory_mode ───────────────────────


def test_fallback_to_in_memory_when_redis_unavailable():
    """When Redis connection fails, _get_backend falls back to InMemoryQueue."""
    set_backend(None)
    import sys
    from unittest.mock import MagicMock
    mock_redis = MagicMock()
    mock_redis.Redis.from_url.return_value.ping.side_effect = ConnectionError(
        "Connection refused"
    )
    with patch.dict(sys.modules, {"redis": mock_redis}):
        from server.queue import _get_backend

        backend = _get_backend()
        assert isinstance(backend, InMemoryQueue)
    set_backend(None)


def test_is_in_memory_mode_true_after_fallback():
    """is_in_memory_mode returns True when backend is InMemoryQueue."""
    from server.queue import is_in_memory_mode

    set_backend(InMemoryQueue())
    assert is_in_memory_mode() is True
    set_backend(None)


def test_is_in_memory_mode_false_with_redis_mock():
    """is_in_memory_mode returns False when backend is not InMemoryQueue."""
    from server.queue import is_in_memory_mode

    # Use a mock that isn't InMemoryQueue
    with patch("server.queue._backend", new="fake_redis"):
        assert is_in_memory_mode() is False
    set_backend(None)


# ── Cycle 2: InMemoryQueue enqueue/dequeue via module functions ──────


def test_in_memory_enqueue_dequeue():
    """InMemoryQueue can enqueue and dequeue through module-level functions."""
    q = InMemoryQueue()
    set_backend(q)
    from server.queue import dequeue_match, enqueue_match

    job = {"job_id": "test-1", "bot_configs": [], "match_id": 1}
    enqueue_match(job)
    result = dequeue_match(timeout=1)
    assert result is not None
    assert result["job_id"] == "test-1"
    set_backend(None)


def test_in_memory_dequeue_empty_returns_none():
    """Dequeue from empty InMemoryQueue returns None."""
    q = InMemoryQueue()
    set_backend(q)
    from server.queue import dequeue_match

    result = dequeue_match(timeout=1)
    assert result is None
    set_backend(None)


def test_in_memory_queue_depth():
    """queue_depth works with InMemoryQueue."""
    q = InMemoryQueue()
    set_backend(q)
    from server.queue import enqueue_match, queue_depth

    assert queue_depth() == 0
    enqueue_match({"job_id": "a", "bot_configs": []})
    enqueue_match({"job_id": "b", "bot_configs": []})
    assert queue_depth() == 2
    set_backend(None)


# ── Cycle 3: Inline match processing in lobby ───────────────────────


def test_trigger_match_calls_inline_when_in_memory_mode():
    """When in-memory mode, _trigger_match calls _run_match_inline instead of enqueue."""
    set_backend(InMemoryQueue())
    from server.lobby import Lobby

    lobby = Lobby()
    with (
        patch("server.lobby._run_match_inline") as mock_inline,
        patch("server.lobby.enqueue_match") as mock_enqueue,
        patch("server.lobby.queue_depth", return_value=0),
        patch("server.lobby._get_fill_bots", return_value=[]),
    ):
        for i in range(4):
            lobby.join({"name": f"bot{i}", "emoji": "B"})
        # Timer triggers the match
        lobby._triggered = False
        lobby._trigger_match()
        mock_inline.assert_called_once()
        mock_enqueue.assert_not_called()
    set_backend(None)


def test_trigger_match_calls_enqueue_when_redis_mode():
    """When Redis mode, _trigger_match calls enqueue_match normally."""
    # Use a non-InMemoryQueue backend
    with patch("server.queue._backend", new="fake_redis"):
        from server.lobby import Lobby

        lobby = Lobby()
        with (
            patch("server.lobby._run_match_inline") as mock_inline,
            patch("server.lobby.enqueue_match") as mock_enqueue,
            patch("server.lobby.queue_depth", return_value=0),
            patch("server.lobby._get_fill_bots", return_value=[]),
        ):
            for i in range(4):
                lobby.join({"name": f"bot{i}", "emoji": "B"})
            lobby._triggered = False
            lobby._trigger_match()
            mock_enqueue.assert_called_once()
            mock_inline.assert_not_called()
    set_backend(None)


def test_run_match_inline_calls_engine():
    """_run_match_inline invokes run_match and write_match in a thread."""
    import threading

    from server.lobby import _run_match_inline

    job = {
        "job_id": "test-inline",
        "bot_configs": [{"name": "a"}, {"name": "b"}],
        "match_id": "test-123",
        "results_dir": "/tmp/test_results",
    }
    with (
        patch("engine.game.run_match") as mock_run,
        patch("engine.match_writer.write_match") as mock_write,
    ):
        mock_run.return_value = {"match_id": "test-123", "rounds": []}
        _run_match_inline(job)
        # Wait for the daemon thread to finish
        for t in threading.enumerate():
            if t.name != "MainThread" and t.daemon:
                t.join(timeout=2)
        mock_run.assert_called_once()
        mock_write.assert_called_once()
