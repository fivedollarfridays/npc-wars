"""Redis-backed match queue with in-memory fallback for testing."""

from __future__ import annotations

import json
from typing import Any, Protocol


class QueueBackend(Protocol):
    """Protocol matching the Redis subset we use."""

    def lpush(self, key: str, value: str) -> Any: ...
    def brpop(self, key: str, timeout: int) -> tuple | None: ...


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


MATCH_QUEUE_KEY = "npcwars:match_queue"

_backend: QueueBackend | None = None


def set_backend(backend: QueueBackend) -> None:
    """Set the queue backend (Redis client or InMemoryQueue)."""
    global _backend
    _backend = backend


def _get_backend() -> QueueBackend:
    """Lazy-init: default to real Redis if no backend was injected."""
    global _backend
    if _backend is None:
        import redis
        _backend = redis.Redis(decode_responses=True)
    return _backend


def enqueue_match(job: dict) -> None:
    """Push a match job onto the queue."""
    _get_backend().lpush(MATCH_QUEUE_KEY, json.dumps(job))


def dequeue_match(timeout: int = 1) -> dict | None:
    """Pop the oldest match job from the queue (blocking with timeout)."""
    result = _get_backend().brpop(MATCH_QUEUE_KEY, timeout=timeout)
    if result is None:
        return None
    return json.loads(result[1])
