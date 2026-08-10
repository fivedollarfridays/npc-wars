"""A share permalink must resolve a real (zero-padded) match file.

write_match names files match_{id:03d}.json; /m/{id} only tried match_{id}.json,
so every share link 404'd. Companion to test_up3_replay_resolution.py, which
pinned the same bug for /api/match/{id} and /api/match/{id}/stream.
"""
import json

import pytest
from fastapi.testclient import TestClient

from server.app import app


@pytest.fixture
def padded_match(tmp_path):
    match = {
        "match_id": 1,
        "winner": "A",
        "players": [{"name": "Alpha", "emoji": "A"}],
        "rounds": [{"round": 1, "positions": []}],
        "duration_rounds": 1,
    }
    (tmp_path / "match_001.json").write_text(json.dumps(match), encoding="utf-8")
    app.state.results_dir = str(tmp_path)
    return tmp_path


def test_share_permalink_resolves_zero_padded_match(padded_match):
    r = TestClient(app).get("/m/1")
    assert r.status_code == 200, f"/m/1 -> {r.status_code} (share permalink dead)"


def test_share_permalink_still_404s_for_a_missing_match(padded_match):
    # Positive control: the fix must not make every id resolve.
    assert TestClient(app).get("/m/999").status_code == 404
