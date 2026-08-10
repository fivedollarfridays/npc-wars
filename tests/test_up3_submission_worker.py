"""UP-3: the worker runs submission jobs through run_sandboxed, not run_match.

Mirrors PSC's PSCW.7 staging E2E: submit -> drain the queue -> a real match
result the ladder/SSE can read, attributed to the submitting player, with no
PII leaking into player names.  Uses NPCWARS_ALLOW_UNSANDBOXED=1 (conftest) so
the in-process executor runs a REAL match without Docker.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import server.worker as worker_mod
from data.match_history import next_match_id
from server.db import get_player_matches, init_db
from server.docker_sandbox import SandboxUnavailableError
from server.queue import (
    InMemoryQueue,
    dequeue_match as real_dequeue,
    enqueue_match,
    set_backend,
)
from server.submission import SUBMISSION_KIND, run_submission_job

SUBMITTER_SOURCE = """\
BOT_NAME = "Challenger"
BOT_EMOJI = "\U0001f9be"

def decide(state):
    me = state["me"]
    enemies = state["enemies"]
    if not enemies:
        return ("rest",)
    target = min(enemies, key=lambda e: abs(e["x"] - me["x"]) + abs(e["y"] - me["y"]))
    dx = target["x"] - me["x"]
    dy = target["y"] - me["y"]
    if abs(dx) + abs(dy) == 1:
        return ("attack", "east" if dx > 0 else "west") if dx else (
            "attack", "south" if dy > 0 else "north")
    if abs(dx) >= abs(dy):
        return ("move", "east" if dx > 0 else "west")
    return ("move", "south" if dy > 0 else "north")
"""


@pytest.fixture()
def conn(tmp_path):
    """A fresh SQLite connection backed by a temp file."""
    return init_db(str(tmp_path / "up3.db"))


def _submission_job(tmp_path, **overrides):
    job = {
        "kind": SUBMISSION_KIND,
        "job_id": "job-up3",
        "player_id": "player-abc",
        "bot_id": 7,
        "bot_source": SUBMITTER_SOURCE,
        "submitter_emoji": "\U0001f9be",
        "results_dir": str(tmp_path / "results"),
        "seed": 123,
    }
    job.update(overrides)
    return job


# ── Executor routing (worker dispatch) ───────────────────────────────


def _drain_worker() -> None:
    """Run the worker loop once, stopping when the queue drains."""

    def _patched_dequeue(timeout=1):
        result = real_dequeue(timeout=0)
        if result is None:
            worker_mod._running = False
        return result

    with patch("server.worker.dequeue_match", side_effect=_patched_dequeue):
        worker_mod._running = True
        worker_mod.main()


def test_worker_routes_submission_to_run_submission_job(tmp_path) -> None:
    """A submission job dispatches to run_submission_job, never run_match."""
    set_backend(InMemoryQueue())
    enqueue_match(_submission_job(tmp_path))

    with (
        patch("server.worker.run_submission_job", MagicMock()) as spy_sub,
        patch("server.worker.run_match") as spy_match,
    ):
        _drain_worker()

    spy_sub.assert_called_once()
    spy_match.assert_not_called()


def test_worker_routes_regular_job_to_run_match(tmp_path) -> None:
    """A job without kind='submission' still runs through run_match."""
    set_backend(InMemoryQueue())
    enqueue_match(
        {"bot_configs": [{"name": "A"}], "match_id": 5, "results_dir": str(tmp_path)}
    )

    with (
        patch("server.worker.run_submission_job", MagicMock()) as spy_sub,
        patch("server.worker.run_match", return_value={"match_id": 5, "winner": "A"}),
        patch("server.worker.write_match"),
        patch("server.worker.award_match_coins"),
    ):
        _drain_worker()

    spy_sub.assert_not_called()


# ── Real sandboxed execution ─────────────────────────────────────────


def test_up3_submission_runs_a_real_match(conn, tmp_path) -> None:
    """End-to-end-ish: a submission job produces a real, persisted match.

    run_sandboxed executes the submitted SOURCE in-process (opt-in set by
    conftest), so a genuine winner + rounds come back and a match file lands
    where the ladder/SSE read it.
    """
    results_dir = tmp_path / "results"
    job = _submission_job(tmp_path)

    match_id = run_submission_job(conn, job)

    assert match_id == 1  # first match in an empty results dir
    match_file = results_dir / "match_001.json"
    assert match_file.is_file()

    import json

    match_data = json.loads(match_file.read_text())
    emojis = [p["emoji"] for p in match_data["players"]]
    assert "\U0001f9be" in emojis  # submitter is in the match
    assert match_data["winner"] in emojis  # a real winner
    assert match_data["duration_rounds"] > 0


def test_submission_calls_run_sandboxed_not_run_match(conn, tmp_path) -> None:
    """The submission executor is run_sandboxed; run_match is never used."""
    fake = {
        "match_id": 1,
        "winner": "\U0001f9be",
        "players": [{"emoji": "\U0001f9be", "name": "Challenger"}],
        "eliminations": [],
        "stats": {},
        "duration_rounds": 3,
    }
    with (
        patch("server.submission.run_sandboxed", return_value=fake) as spy_box,
        patch("engine.game.run_match") as spy_match,
    ):
        run_submission_job(conn, _submission_job(tmp_path))

    spy_box.assert_called_once()
    spy_match.assert_not_called()
    # run_sandboxed received SOURCE strings, not compiled configs.
    sources = spy_box.call_args.args[0]
    assert sources[0] == SUBMITTER_SOURCE
    assert all(isinstance(s, str) for s in sources)


# ── Fail-closed ──────────────────────────────────────────────────────


def test_sandbox_unavailable_marks_job_failed_no_file(conn, tmp_path) -> None:
    """SandboxUnavailableError -> job fails cleanly, no match file written."""
    results_dir = tmp_path / "results"

    def _boom(*_args, **_kwargs):
        raise SandboxUnavailableError("docker down, opt-in off")

    with patch("server.submission.run_sandboxed", side_effect=_boom):
        result = run_submission_job(conn, _submission_job(tmp_path))

    assert result is None
    # No corrupt/half-written match left behind.
    assert not results_dir.exists() or list(results_dir.glob("*.json")) == []
    # Match id was never consumed, so the next job can still take it.
    assert next_match_id(str(results_dir)) == 1


# ── Attribution + no PII ─────────────────────────────────────────────


def test_submitter_is_credited_in_match_players(conn, tmp_path) -> None:
    """The persisted match binds to the submitting player_id (discoverable)."""
    run_submission_job(conn, _submission_job(tmp_path))

    matches = get_player_matches(conn, "player-abc")
    assert matches == [1]


def test_no_pii_in_persisted_player_names(conn, tmp_path) -> None:
    """Player names come from BOT_NAME/presets, never the submitter's ref."""
    job = _submission_job(tmp_path, player_id="ref-opaque-should-not-appear-1234")
    run_submission_job(conn, job)

    import json

    payload = (tmp_path / "results" / "match_001.json").read_text()
    data = json.loads(payload)
    for player in data["players"]:
        assert "ref-opaque-should-not-appear-1234" not in player["name"]
        assert "@" not in player["name"]  # no email-shaped leakage
    # Positive control: the opaque ref really is absent from the whole file.
    assert "ref-opaque-should-not-appear-1234" not in payload
