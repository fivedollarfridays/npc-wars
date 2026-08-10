"""UP-3 follow-up: a submission match must be readable by its natural id.

The worker writes match_{id:03d}.json; the by-id read routes looked only for
match_{id}.json, so /api/match/1/stream 404'd on match_001.json. This pins the
submit -> replay loop end to end.
"""
import pytest
from fastapi.testclient import TestClient
from server.app import app
from server.submission import build_submission_job, run_submission_job
from server.db import init_db, store_bot, create_player


@pytest.fixture(autouse=True)
def _force_in_process_sandbox(monkeypatch):
    """Pin the in-process executor so the real match runs on any runner.

    On CI (Docker daemon present, no built sandbox image) run_sandboxed would
    take the Docker path and fail, leaving no match file to read back.
    """
    monkeypatch.setenv("NPCWARS_ALLOW_UNSANDBOXED", "1")
    monkeypatch.setattr("server.docker_sandbox._docker_available", lambda: False)


def _make_submission_match(results_dir):
    conn = init_db(":memory:")
    create_player(conn, "p1", "Submitter")
    src = 'BOT_NAME="ProofBot"\nBOT_EMOJI="P"\ndef decide(s):\n    return ("rest",)\n'
    bid = store_bot(conn, "p1", "ProofBot", "P", src)
    job = build_submission_job(
        job_id="job_x", player_id="p1", bot_id=bid, source=src,
        emoji="P", results_dir=results_dir,
    )
    return run_submission_job(conn, job)


def test_submission_match_readable_by_natural_id(monkeypatch, tmp_path):
    monkeypatch.setenv("NPCWARS_ALLOW_UNSANDBOXED", "1")
    rd = str(tmp_path)
    mid = _make_submission_match(rd)
    app.state.results_dir = rd
    client = TestClient(app)
    # The replay viewer fetches by the natural id the 202/history exposes.
    r = client.get(f"/api/match/{mid}")
    assert r.status_code == 200, f"/api/match/{mid} -> {r.status_code} (submission match unreachable)"
    body = r.json()
    assert "ProofBot" in [p.get("name") for p in body.get("players", [])]


def test_submission_match_stream_by_natural_id(monkeypatch, tmp_path):
    monkeypatch.setenv("NPCWARS_ALLOW_UNSANDBOXED", "1")
    rd = str(tmp_path)
    mid = _make_submission_match(rd)
    app.state.results_dir = rd
    client = TestClient(app)
    r = client.get(f"/api/match/{mid}/stream")
    assert r.status_code == 200, f"/api/match/{mid}/stream -> {r.status_code}"
