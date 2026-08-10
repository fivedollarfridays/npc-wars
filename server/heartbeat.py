"""Worker liveness heartbeat -- the thing the compose healthcheck actually checks.

The old worker healthcheck was ``python -c "print('ok')"``: it proved the
container could start a Python interpreter and nothing else. During a live
bring-up the worker reported ``Up (healthy)`` while its poll loop was not
running at all (UP-5 P2).

The loop now touches a file every cycle (:func:`touch_heartbeat`) and the
healthcheck runs ``python -m server.heartbeat``, which exits non-zero once
that file is missing or older than ``NPCWARS_WORKER_HEARTBEAT_MAX_AGE``. A
stalled or dead loop therefore turns the container *unhealthy* instead of
lying about it.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

__all__ = [
    "DEFAULT_HEARTBEAT_MAX_AGE",
    "DEFAULT_HEARTBEAT_PATH",
    "HEARTBEAT_MAX_AGE_ENV",
    "HEARTBEAT_PATH_ENV",
    "heartbeat_age",
    "heartbeat_is_fresh",
    "heartbeat_max_age",
    "heartbeat_path",
    "main",
    "touch_heartbeat",
]

HEARTBEAT_PATH_ENV: str = "NPCWARS_WORKER_HEARTBEAT"
DEFAULT_HEARTBEAT_PATH: str = "/tmp/npcwars-worker.heartbeat"  # noqa: S108

HEARTBEAT_MAX_AGE_ENV: str = "NPCWARS_WORKER_HEARTBEAT_MAX_AGE"

#: Generous enough for the slowest legitimate cycle: a submission job blocks
#: the loop for up to SANDBOX_TIMEOUT + 5s while the sandbox container runs.
DEFAULT_HEARTBEAT_MAX_AGE: float = 60.0


def heartbeat_path() -> str:
    """Path of the worker's heartbeat file."""
    return os.environ.get(HEARTBEAT_PATH_ENV) or DEFAULT_HEARTBEAT_PATH


def heartbeat_max_age() -> float:
    """Seconds after which a heartbeat counts as stale (bad env -> default)."""
    raw = os.environ.get(HEARTBEAT_MAX_AGE_ENV)
    if not raw:
        return DEFAULT_HEARTBEAT_MAX_AGE
    try:
        value = float(raw)
    except ValueError:
        return DEFAULT_HEARTBEAT_MAX_AGE
    return value if value > 0 else DEFAULT_HEARTBEAT_MAX_AGE


def touch_heartbeat() -> None:
    """Record 'the loop is alive' as of now.

    Never raises: a heartbeat write failure must not kill a worker that is
    otherwise processing jobs. A write that keeps failing shows up as a stale
    heartbeat, which the healthcheck already treats as unhealthy.
    """
    path = Path(heartbeat_path())
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{time.time()}\n", encoding="utf-8")
    except OSError:
        pass


def heartbeat_age() -> float | None:
    """Seconds since the last heartbeat, or None when there is none."""
    try:
        mtime = os.path.getmtime(heartbeat_path())
    except OSError:
        return None
    return max(0.0, time.time() - mtime)


def heartbeat_is_fresh() -> bool:
    """True only if the loop touched the heartbeat within the max age."""
    age = heartbeat_age()
    return age is not None and age <= heartbeat_max_age()


def main() -> int:
    """Healthcheck entrypoint: exit 0 when the poll loop is demonstrably alive."""
    age = heartbeat_age()
    if age is None:
        print(f"worker heartbeat missing at {heartbeat_path()}", file=sys.stderr)
        return 1
    if age > heartbeat_max_age():
        print(
            f"worker heartbeat stale: {age:.1f}s > {heartbeat_max_age():.1f}s",
            file=sys.stderr,
        )
        return 1
    print(f"worker heartbeat ok ({age:.1f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
