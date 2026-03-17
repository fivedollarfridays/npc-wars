"""Rate limiting dependency for bot submissions."""

import time

from fastapi import Request
from fastapi.responses import JSONResponse

RATE_LIMIT_SECONDS = 30
MAX_SUBMISSIONS = 1

# In-memory store: session_token -> last submission timestamp
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


async def check_rate_limit(request: Request) -> JSONResponse | None:
    """Check and enforce rate limits for the current session.

    Returns a 429 JSONResponse if rate limited, else None.
    Records the submission timestamp on success.
    Attaches rate limit headers to the request state for the route to use.
    """
    token = getattr(request.state, "session_token", "unknown")

    if len(_submissions) > 1000:
        _cleanup_stale()

    now = time.monotonic()
    last_time = _submissions.get(token)

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


def record_submission(request: Request) -> None:
    """Record that a submission was made for this session."""
    token = getattr(request.state, "session_token", "unknown")
    _submissions[token] = time.monotonic()
