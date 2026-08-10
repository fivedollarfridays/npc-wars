"""UP-3: submitting a bot enqueues a real submission match job.

Closes the gap where POST /api/submit-bot minted a cosmetic job_id that
nothing consumed. The submit route must now enqueue a discriminated
``kind == "submission"`` job carrying the submitter's SOURCE (not a
pre-compiled decide_func) plus the player binding, so the worker can run it
through the sandbox.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from server.app import app
from server.queue import InMemoryQueue, dequeue_match, set_backend
from server.routes.submit import clear_rate_limits
from server.submission import SUBMISSION_KIND

client = TestClient(app)

VALID_SOURCE = """\
BOT_NAME = "Enqueued"
BOT_EMOJI = "\U0001f9ea"

def decide(state):
    return ("rest",)
"""


def setup_function() -> None:
    clear_rate_limits()
    set_backend(InMemoryQueue())


def test_submit_enqueues_a_submission_job() -> None:
    """A valid submission pushes a kind='submission' job onto the queue."""
    resp = client.post("/api/submit-bot", json={"source": VALID_SOURCE})
    assert resp.status_code == 202

    job = dequeue_match(timeout=0)
    assert job is not None
    assert job["kind"] == SUBMISSION_KIND


def test_submission_job_carries_submitter_source() -> None:
    """The enqueued job carries the submitted SOURCE (for run_sandboxed)."""
    client.post("/api/submit-bot", json={"source": VALID_SOURCE})

    job = dequeue_match(timeout=0)
    assert job["bot_source"] == VALID_SOURCE
    # No pre-compiled decide_func is smuggled through the queue.
    assert "decide_func" not in job


def test_submission_job_carries_player_binding() -> None:
    """The job binds the submitting player + stored bot for attribution."""
    resp = client.post("/api/submit-bot", json={"source": VALID_SOURCE})
    bot_id = resp.json()["bot_id"]

    job = dequeue_match(timeout=0)
    assert isinstance(job["player_id"], str) and job["player_id"]
    assert job["bot_id"] == bot_id
    # The submitter's chosen emoji becomes their ladder identity.
    assert job["submitter_emoji"] == "\U0001f9ea"


def test_job_id_matches_202_response() -> None:
    """The queued job_id is the same handle returned to the client (202)."""
    resp = client.post("/api/submit-bot", json={"source": VALID_SOURCE})
    job = dequeue_match(timeout=0)
    assert job["job_id"] == resp.json()["job_id"]
