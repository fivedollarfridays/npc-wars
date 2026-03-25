"""Rate limiting dependency for bot submissions."""

import time

from fastapi import Request
from fastapi.responses import JSONResponse

RATE_LIMIT_SECONDS = 30
MAX_SUBMISSIONS = 1
MAX_SUBMISSIONS_ENTRIES = 10_000

# In-memory store: client_key -> last submission timestamp
_submissions: dict[str, float] = {}


def clear_rate_limit_state() -> None:
    """Clear all rate limit state (for testing)."""
    _submissions.clear()


def _cleanup_stale() -> None:
    """Remove entries older than the rate limit window."""
    now = time.monotonic()
    stale = [k for k, ts in _submissions.items() if now - ts > RATE_LIMIT_SECONDS]
    for k in stale:
        del _submissions[k]


def _get_client_key(request: Request) -> str:
    """Derive rate-limit key: prefer X-API-Key, fall back to client IP."""
    api_key = request.headers.get("x-api-key")
    if api_key:
        return api_key
    host = getattr(request.client, "host", None) if request.client else None
    return host or "unknown"


async def check_rate_limit(request: Request) -> JSONResponse | None:
    """Check and enforce rate limits for the current session.

    Returns a 429 JSONResponse if rate limited, else None.
    Records the submission timestamp on success.
    Attaches rate limit headers to the request state for the route to use.
    """
    client_key = _get_client_key(request)

    # Aggressive cleanup: always clean when over half capacity, or at cap
    if len(_submissions) > MAX_SUBMISSIONS_ENTRIES // 2:
        _cleanup_stale()
    # Hard cap: if still over limit after cleanup, evict oldest entries
    if len(_submissions) >= MAX_SUBMISSIONS_ENTRIES:
        _evict_oldest(len(_submissions) - MAX_SUBMISSIONS_ENTRIES + 1)

    now = time.monotonic()
    last_time = _submissions.get(client_key)

    if last_time is not None:
        elapsed = now - last_time
        if elapsed < RATE_LIMIT_SECONDS:
            retry_after = int(RATE_LIMIT_SECONDS - elapsed) + 1
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limited. Try again later."},
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(MAX_SUBMISSIONS),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(retry_after),
                },
            )

    # Store headers for the route handler to attach
    request.state.rate_limit_headers = {
        "X-RateLimit-Limit": str(MAX_SUBMISSIONS),
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Reset": str(RATE_LIMIT_SECONDS),
    }

    return None


def _evict_oldest(count: int) -> None:
    """Remove the N oldest entries from _submissions."""
    if count <= 0:
        return
    sorted_keys = sorted(_submissions, key=_submissions.get)  # type: ignore[arg-type]
    for k in sorted_keys[:count]:
        del _submissions[k]


def record_submission(request: Request) -> None:
    """Record that a submission was made for this client."""
    client_key = _get_client_key(request)
    _submissions[client_key] = time.monotonic()
