"""Redis-backed match queue, with a dev-only in-memory fallback.

The fallback is a foot-gun in any multi-process deployment (see
:class:`~server.queue_backends.QueueBackendUnavailableError`), so deployments
set ``NPCWARS_QUEUE_STRICT=1`` and get a loud failure instead.
"""

from __future__ import annotations

import json
import logging
import os

from server.queue_backends import (
    InMemoryQueue,
    QueueBackend,
    QueueBackendUnavailableError,
)

__all__ = [
    "MATCH_QUEUE_KEY",
    "QUEUE_STRICT_ENV",
    "InMemoryQueue",
    "QueueBackend",
    "QueueBackendUnavailableError",
    "backend_name",
    "dequeue_match",
    "enqueue_match",
    "init_backend",
    "is_in_memory_mode",
    "queue_depth",
    "queue_strict_mode",
    "set_backend",
]

_logger = logging.getLogger(__name__)

MATCH_QUEUE_KEY = "npcwars:match_queue"

#: Deployment opt-in: require Redis, never fall back. Exact match on "1", the
#: same fail-closed convention as NPCWARS_ALLOW_UNSANDBOXED / _ALLOW_KEYLESS.
QUEUE_STRICT_ENV: str = "NPCWARS_QUEUE_STRICT"

_backend: QueueBackend | None = None


def set_backend(backend: QueueBackend | None) -> None:
    """Set the queue backend (Redis client or InMemoryQueue)."""
    global _backend
    _backend = backend


def is_in_memory_mode() -> bool:
    """Return True if the current backend is the in-memory fallback."""
    return isinstance(_backend, InMemoryQueue)


def queue_strict_mode() -> bool:
    """True only when the deployment demands a real Redis backend."""
    return os.environ.get(QUEUE_STRICT_ENV) == "1"


def backend_name() -> str:
    """Human-readable name of the active backend, for startup logging."""
    if _backend is None:
        return "none"
    return "in-memory" if isinstance(_backend, InMemoryQueue) else "redis"


def _get_backend() -> QueueBackend:
    """Lazy-init the backend: Redis, else fall back -- or fail if strict."""
    global _backend
    if _backend is not None:
        return _backend
    url = os.environ.get("REDIS_URL", "redis://localhost:6379")
    try:
        import redis

        client = redis.Redis.from_url(url, decode_responses=True)
        client.ping()
        _backend = client
        _logger.info("Queue backend: Redis at %s", url)
    except Exception as exc:
        if queue_strict_mode():
            # Leave _backend as None so a later call retries Redis rather
            # than inheriting a fallback nobody asked for.
            raise QueueBackendUnavailableError(
                f"Redis at {url} is unreachable and {QUEUE_STRICT_ENV}=1 forbids "
                "the in-process fallback (it would strand jobs the worker never "
                f"sees). Underlying error: {exc}"
            ) from exc
        _backend = InMemoryQueue()
        _logger.warning(
            "Queue backend: Redis at %s unavailable (%s), using the in-memory "
            "fallback -- single-process only, a separate worker will NOT see "
            "these jobs. Set %s=1 to make this a hard failure.",
            url,
            exc,
            QUEUE_STRICT_ENV,
        )
    return _backend


def init_backend() -> str:
    """Resolve and log the queue backend at process startup.

    Called by both the API app and the worker so a split brain is visible in
    the first lines of each container's logs.
    """
    _get_backend()
    name = backend_name()
    _logger.info(
        "Queue backend ready: %s (strict=%s, key=%s)",
        name,
        queue_strict_mode(),
        MATCH_QUEUE_KEY,
    )
    return name


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
