"""Queue backend types: the protocol, the dev fallback, and its failure mode.

Split out of ``server/queue.py`` (UP-5) so that module can grow the
strict-mode plumbing without breaking the per-file function budget.
``server.queue`` re-exports every name here, so existing imports such as
``from server.queue import InMemoryQueue`` keep working.
"""

from __future__ import annotations

from typing import Any, Protocol

__all__ = [
    "InMemoryQueue",
    "QueueBackend",
    "QueueBackendUnavailableError",
]


class QueueBackendUnavailableError(RuntimeError):
    """Raised when the required queue backend cannot be reached.

    Only raised in strict mode (``NPCWARS_QUEUE_STRICT=1``). Strict mode
    exists because the *silent* alternative -- an in-process fallback queue --
    strands jobs: the API accepts a submission with 202 and the worker, in its
    own container with its own in-process queue, never sees it.
    """


class QueueBackend(Protocol):
    """Protocol matching the Redis subset we use."""

    def lpush(self, key: str, value: str) -> Any: ...
    def brpop(self, key: str, timeout: int) -> tuple | None: ...
    def ping(self) -> bool: ...


class InMemoryQueue:
    """Test-friendly in-memory queue backend implementing QueueBackend.

    Single-process only. Legitimate for local dev and the test-suite; never
    correct for the compose topology, where the enqueuing app and the
    dequeuing worker are separate processes.
    """

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
