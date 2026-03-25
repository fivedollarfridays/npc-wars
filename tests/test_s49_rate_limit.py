"""Tests for T49.3: rate limiter key fix + stats route sort_by validation."""

import time as real_time
import pytest
from fastapi.testclient import TestClient

from server.app import app
from server.middleware.rate_limit import (
    _submissions,
    clear_rate_limit_state,
)
from server.routes.submit import clear_rate_limits

CLEAN_SOURCE = """\
def decide(me, enemies, storm):
    if enemies:
        return {"move": "north", "action": "shoot north"}
    return {"move": "south", "action": "none"}
"""


def _make_client() -> TestClient:
    return TestClient(app)


def setup_function():
    """Reset state before each test."""
    from server.db import init_db

    app.state.db = init_db(":memory:")
    clear_rate_limit_state()
    clear_rate_limits()


# --- Cycle 1: Rate limiter uses player ID from X-API-Key ---


def test_get_client_key_uses_api_key_header():
    """_get_client_key should return X-API-Key value when present."""
    from server.middleware.rate_limit import _get_client_key
    from unittest.mock import MagicMock

    request = MagicMock()
    request.headers = {"x-api-key": "player-aaa"}
    request.client.host = "192.168.1.1"

    assert _get_client_key(request) == "player-aaa"


def test_get_client_key_falls_back_to_ip():
    """_get_client_key should return client IP when no API key."""
    from server.middleware.rate_limit import _get_client_key
    from unittest.mock import MagicMock

    request = MagicMock()
    request.headers = {}
    request.client.host = "10.0.0.5"

    assert _get_client_key(request) == "10.0.0.5"


def test_rate_limit_keys_on_ip_when_no_auth():
    """Without X-API-Key, rate limiter should key on client IP, not session."""
    client = _make_client()

    # Submit without API key header
    client.post("/api/submit-bot", json={"source": CLEAN_SOURCE})

    # Should NOT have "unknown" as the key
    assert "unknown" not in _submissions
    # Should have an IP-based or host-based key, not a UUID session token
    keys = list(_submissions.keys())
    assert len(keys) >= 1
    # None of the keys should be long UUID-like session tokens
    for k in keys:
        clean = k.replace("-", "")
        is_uuid = len(clean) >= 32 and all(
            c in "0123456789abcdef" for c in clean
        )
        assert not is_uuid, f"Key {k!r} looks like a session token, not IP"


# --- Cycle 2: _submissions max cap ---


def test_submissions_dict_capped_at_max_size():
    """_submissions dict should not grow beyond MAX_SUBMISSIONS_ENTRIES."""
    from server.middleware.rate_limit import MAX_SUBMISSIONS_ENTRIES

    # Fill beyond the cap with stale entries
    now = real_time.monotonic()
    for i in range(MAX_SUBMISSIONS_ENTRIES + 500):
        _submissions[f"stale-{i}"] = now - 9999  # expired entries

    # Trigger a request which should trigger cleanup + cap enforcement
    client = _make_client()
    client.post("/api/submit-bot", json={"source": CLEAN_SOURCE})

    assert len(_submissions) <= MAX_SUBMISSIONS_ENTRIES


# --- Cycle 3: Stats route sort_by validation ---


@pytest.fixture()
def stats_results_dir(tmp_path):
    """Create a results dir with match data for stats tests."""
    import json
    import os

    match = {
        "match_id": 1,
        "date": "2026-03-25",
        "winner": "\U0001f916",
        "duration_rounds": 5,
        "players": [
            {"emoji": "\U0001f916", "name": "Bot1"},
            {"emoji": "\U0001f3af", "name": "Bot2"},
        ],
        "stats": {
            "\U0001f916": {"kills": 2, "damage_dealt": 100, "damage_taken": 30},
            "\U0001f3af": {"kills": 0, "damage_dealt": 30, "damage_taken": 100},
        },
        "eliminations": [{"emoji": "\U0001f3af", "round": 5}],
    }
    rdir = str(tmp_path / "results")
    os.makedirs(rdir)
    with open(os.path.join(rdir, "match_001.json"), "w") as f:
        json.dump(match, f)
    app.state.results_dir = rdir
    return rdir


def test_leaderboard_invalid_sort_by_returns_400(stats_results_dir):
    """Invalid sort_by param should return 400, not 500."""
    client = _make_client()
    resp = client.get("/api/leaderboard?sort_by=nonexistent_field")
    assert resp.status_code == 400
    assert "detail" in resp.json()
    # Should NOT leak internal error details
    assert "ValueError" not in resp.json()["detail"]


def test_leaderboard_valid_sort_by_still_works(stats_results_dir):
    """Valid sort_by values should continue to work."""
    client = _make_client()
    for field in ("wins", "kills", "damage_dealt", "win_rate"):
        resp = client.get(f"/api/leaderboard?sort_by={field}")
        assert resp.status_code == 200, f"sort_by={field} failed"
