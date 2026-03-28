"""Redis-backed match queue with in-memory fallback for testing."""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Protocol

import redis

_logger = logging.getLogger(__name__)


class QueueBackend(Protocol):
    """Protocol matching the Redis subset we use."""

    def lpush(self, key: str, value: str) -> Any: ...
    def brpop(self, key: str, timeout: int) -> tuple | None: ...
    def ping(self) -> bool: ...


class InMemoryQueue:
    """Test-friendly in-memory queue backend implementing QueueBackend."""

    def __init__(self) -> None:
        self._data: dict[str, list[str]] = {}

    def lpush(self, key: str, value: str) -> int:
        self._data.setdefault(key, []).insert(0, value)
        return len(self._data[key])

    def brpop(self, key: str, timeout: int = 0) -> tuple | None:
        items = self._data.get(key, [])
        if not items:
            return None
        return (key, items.pop())

    def ping(self) -> bool:
        return True


MATCH_QUEUE_KEY = "npcwars:match_queue"

_backend: QueueBackend | None = None


def set_backend(backend: QueueBackend | None) -> None:
    """Set the queue backend (Redis client or InMemoryQueue)."""
    global _backend
    _backend = backend


def is_in_memory_mode() -> bool:
    """Return True if the current backend is the in-memory fallback."""
    return isinstance(_backend, InMemoryQueue)


def _get_backend() -> QueueBackend:
    """Lazy-init: connect to Redis, falling back to InMemoryQueue on failure."""
    global _backend
    if _backend is not None:
        return _backend
    url = os.environ.get("REDIS_URL", "redis://localhost:6379")
    try:
        client = redis.Redis.from_url(url, decode_responses=True)
        client.ping()
        _backend = client
        _logger.info("Queue backend: Redis at %s", url)
    except Exception:
        _backend = InMemoryQueue()
        _logger.warning(
            "Queue backend: Redis unavailable, using in-memory fallback"
        )
    return _backend


def enqueue_match(job: dict) -> None:
    """Push a match job onto the queue."""
    _get_backend().lpush(MATCH_QUEUE_KEY, json.dumps(job))


def queue_depth() -> int:
    """Return the number of jobs currently in the match queue."""
    backend = _get_backend()
    if hasattr(backend, "llen"):
        return backend.llen(MATCH_QUEUE_KEY)
    # Fallback for InMemoryQueue
    if hasattr(backend, "_data"):
        return len(backend._data.get(MATCH_QUEUE_KEY, []))
    return 0


def dequeue_match(timeout: int = 1) -> dict | None:
    """Pop the oldest match job from the queue (blocking with timeout)."""
    result = _get_backend().brpop(MATCH_QUEUE_KEY, timeout=timeout)
    if result is None:
        return None
    return json.loads(result[1])
