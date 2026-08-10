"""UP-5: in-process rehearsal of every contract scripts/verify_arena_e2e.sh uses.

The E2E script itself can only run on a Docker host. What *can* be pinned here
is everything it asserts about the application: the exact header names of the
UP-2 delegated submit, the 202 body shape, the ``/api/lobby/history`` polling
shape it discovers the match id from, natural-id replay resolution on both
``/api/match/{id}`` and ``/api/match/{id}/stream``, and the leaderboard row it
looks the submitter up in.

If any of these drift, the shell script would fail on a live host with a
confusing message; these tests fail here instead. The queue, worker and match
are all real -- only the Docker sandbox is swapped for the in-process executor
(the same substitution the UP-3 worker tests make).
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

import server.worker as worker_mod
from server.app import app
from server.db import init_db
from server.middleware.rate_limit import clear_all_rate_limit_state
from server.queue import InMemoryQueue, set_backend

SERVICE_KEY = "up5-e2e-service-key"
PLAYER_REF = "e2e-17549999912345"
MARKER = "E2E17549999912345"

#: Byte-for-byte the bot the E2E script's BUILD_PAYLOAD_PY emits.
BOT_SOURCE = (
    f'BOT_NAME = "E2E Probe {MARKER}"\n'
    f'BOT_EMOJI = "{MARKER}"\n'
    'BOT_BIO = "arena end-to-end probe"\n'
    "\n"
    "def decide(state):\n"
    '    return ("rest",)\n'
)


@pytest.fixture()
def arena(tmp_path, monkeypatch):
    """A real app + real queue + real worker, on a temp results dir and DB."""
    monkeypatch.setenv("NPCWARS_SERVICE_API_KEY", SERVICE_KEY)
    monkeypatch.setenv("NPCWARS_ALLOW_UNSANDBOXED", "1")
    monkeypatch.setattr("server.docker_sandbox._docker_available", lambda: False)

    results_dir = tmp_path / "results"
    results_dir.mkdir()
    conn = init_db(str(tmp_path / "npcwars.db"))

    monkeypatch.setattr(app.state, "results_dir", str(results_dir), raising=False)
    monkeypatch.setattr(app.state, "db", conn, raising=False)
    # Submissions are rate-limited to 1 per 30s per (api key, player ref). The
    # live script sidesteps this by minting a fresh X-Player-Ref per run; the
    # tests reuse one ref, so clear the window instead.
    clear_all_rate_limit_state()
    set_backend(InMemoryQueue())
    try:
        yield TestClient(app), conn
    finally:
        set_backend(None)


def _submit(client: TestClient) -> dict:
    """The script's step 2: delegated submit, asserted 202 + job_id."""
    response = client.post(
        "/api/submit-bot",
        content=json.dumps({"source": BOT_SOURCE}),
        headers={
            "Content-Type": "application/json",
            "X-API-Key": SERVICE_KEY,
            "X-Player-Ref": PLAYER_REF,
        },
    )
    assert response.status_code == 202, response.text
    return response.json()


def _drain(conn) -> None:
    """Stand in for the worker container: one poll cycle runs the job."""
    assert worker_mod.poll_once(conn) is True


def _history_match_id(client: TestClient) -> int:
    """The script's step 3: poll /api/lobby/history, take the newest id."""
    response = client.get(
        "/api/lobby/history",
        headers={"X-API-Key": SERVICE_KEY, "X-Player-Ref": PLAYER_REF},
    )
    assert response.status_code == 200, response.text
    matches = response.json()["matches"]
    assert matches, "history is the script's only handle on the match id"
    return max(int(m) for m in matches)


class TestSubmitContract:
    """Step 2: the UP-2 delegated shape the script sends."""

    def test_service_key_plus_player_ref_is_accepted_with_a_job_id(
        self, arena
    ) -> None:
        client, _ = arena
        body = _submit(client)
        assert body["job_id"]

    def test_the_scripts_json_payload_survives_the_wire(self, arena) -> None:
        """Real newlines inside the source must arrive intact (json.dumps)."""
        client, conn = arena
        _submit(client)
        from server.queue import dequeue_match

        job = dequeue_match(timeout=1)
        assert job is not None
        assert job["bot_source"] == BOT_SOURCE
        assert job["kind"] == "submission"


class TestMatchDiscoveryContract:
    """Step 3: history is how the script learns the match id."""

    def test_history_exposes_the_match_after_the_worker_runs_it(
        self, arena
    ) -> None:
        client, conn = arena
        _submit(client)
        _drain(conn)
        assert _history_match_id(client) >= 1

    def test_history_is_empty_before_the_worker_runs(self, arena) -> None:
        """The poll loop must have something to wait *for*."""
        client, _ = arena
        _submit(client)
        response = client.get(
            "/api/lobby/history",
            headers={"X-API-Key": SERVICE_KEY, "X-Player-Ref": PLAYER_REF},
        )
        assert response.json()["matches"] == []


class TestReplayContract:
    """Step 4: natural-id resolution on both replay surfaces."""

    def test_match_json_is_readable_by_natural_id(self, arena) -> None:
        client, conn = arena
        _submit(client)
        _drain(conn)
        match_id = _history_match_id(client)

        response = client.get(f"/api/match/{match_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["match_id"] == match_id
        assert data["winner"]
        assert data["rounds"]
        assert MARKER in [p["emoji"] for p in data["players"]]

    def test_stream_resolves_the_same_natural_id(self, arena) -> None:
        client, conn = arena
        _submit(client)
        _drain(conn)
        match_id = _history_match_id(client)

        with client.stream("GET", f"/api/match/{match_id}/stream") as response:
            assert response.status_code == 200
            head = ""
            for chunk in response.iter_text():
                head += chunk
                if "event: round" in head:
                    break
        assert "event: round" in head


class TestLadderContract:
    """Step 5: the submitter is discoverable on the public ladder."""

    def test_submitter_appears_on_the_leaderboard(self, arena) -> None:
        client, conn = arena
        _submit(client)
        _drain(conn)

        rows = client.get("/api/leaderboard").json()
        entry = next((r for r in rows if r["emoji"] == MARKER), None)
        assert entry is not None, [r["emoji"] for r in rows]
        assert entry["matches_played"] == 1


class TestFailClosedRemainsTheDefault:
    """The property step 1 of the script leans on: no opt-in, no execution."""

    def test_no_match_is_written_when_the_sandbox_is_unavailable(
        self, arena, monkeypatch
    ) -> None:
        client, conn = arena
        monkeypatch.delenv("NPCWARS_ALLOW_UNSANDBOXED", raising=False)
        _submit(client)
        _drain(conn)

        assert client.get("/api/leaderboard").json() == []
        response = client.get(
            "/api/lobby/history",
            headers={"X-API-Key": SERVICE_KEY, "X-Player-Ref": PLAYER_REF},
        )
        assert response.json()["matches"] == []
