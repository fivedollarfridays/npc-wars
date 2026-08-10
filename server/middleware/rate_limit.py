"""Rate limiting dependency for bot submissions."""

import hashlib
import time

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

RATE_LIMIT_SECONDS = 30
MAX_SUBMISSIONS = 1
MAX_SUBMISSIONS_ENTRIES = 10_000

# In-memory store: client_key -> last submission timestamp
_submissions: dict[str, float] = {}

# Generic per-category stores: category -> {client_key -> [timestamps]}
_rate_stores: dict[str, dict[str, list[float]]] = {}


def clear_rate_limit_state() -> None:
    """Clear all rate limit state (for testing)."""
    _submissions.clear()


def clear_all_rate_limit_state() -> None:
    """Clear both legacy and generic rate limit state (for testing)."""
    _submissions.clear()
    _rate_stores.clear()


def _cleanup_stale() -> None:
    """Remove entries older than the rate limit window."""
    now = time.monotonic()
    stale = [k for k, ts in _submissions.items() if now - ts > RATE_LIMIT_SECONDS]
    for k in stale:
        del _submissions[k]


def _get_client_key(request: Request) -> str:
    """Derive rate-limit key: prefer X-API-Key, fall back to client IP.

    Delegated (service-key) requests carry an ``X-Player-Ref`` and are limited
    per acting player rather than per relay — otherwise one shared key would
    throttle every delegated player at once.  Auth rejects the ref unless the
    key is the service key, so this cannot be used to evade the limit.  The
    ref is hashed so the opaque token never lands in the in-memory map.
    """
    api_key = request.headers.get("x-api-key")
    if api_key:
        player_ref = request.headers.get("x-player-ref")
        if player_ref:
            digest = hashlib.sha256(player_ref.encode()).hexdigest()[:16]
            return f"{api_key}:{digest}"
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


MAX_GENERIC_ENTRIES = 10_000
TOURNAMENT_RATE_LIMIT = 5
TOURNAMENT_RATE_WINDOW = 60
LOBBY_RATE_LIMIT = 10
LOBBY_RATE_WINDOW = 60


def check_rate_limit_generic(
    request: Request, category: str, window_seconds: int, max_requests: int,
) -> None:
    """Generic rate limiter for any endpoint category.

    Tracks timestamps per client within a sliding window.
    Raises HTTPException(429) if over limit.
    """
    store = _rate_stores.setdefault(category, {})
    client_key = _get_client_key(request)
    now = time.monotonic()
    cutoff = now - window_seconds

    # Periodic cleanup: remove stale client keys
    if len(store) > MAX_GENERIC_ENTRIES // 2:
        stale_keys = [k for k, ts in store.items() if not any(t > cutoff for t in ts)]
        for k in stale_keys:
            del store[k]

    # Get existing timestamps for this client, prune expired
    timestamps = [t for t in store.get(client_key, []) if t > cutoff]

    if len(timestamps) >= max_requests:
        oldest = min(timestamps)
        remaining = window_seconds - (now - oldest)
        retry_after = max(int(remaining) + 1, 1)
        raise HTTPException(
            status_code=429,
            detail=f"Rate limited. Try again in {retry_after}s",
            headers={"Retry-After": str(retry_after)},
        )

    timestamps.append(now)
    store[client_key] = timestamps


def check_tournament_rate_limit(request: Request) -> None:
    """Rate limit tournament creation: 5 per 60s."""
    check_rate_limit_generic(request, "tournament", TOURNAMENT_RATE_WINDOW, TOURNAMENT_RATE_LIMIT)


def check_lobby_rate_limit(request: Request) -> None:
    """Rate limit lobby joins: 10 per 60s."""
    check_rate_limit_generic(request, "lobby", LOBBY_RATE_WINDOW, LOBBY_RATE_LIMIT)
