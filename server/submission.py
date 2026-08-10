"""UP-3: submission-match plumbing (submit -> worker -> run_sandboxed).

A *submission* job differs from a lobby/tournament job in one load-bearing
way: it carries untrusted bot SOURCE, not a pre-compiled ``decide_func``.  The
only correct executor for that source is
:func:`server.docker_sandbox.run_sandboxed` (Docker-isolated, fail-closed).
This module builds the job on submit and processes it in the worker.
"""

from __future__ import annotations

import logging
import sqlite3
from typing import Any

from data.match_history import next_match_id
from engine.match_writer import write_match
from server.coin_rewards import award_match_coins
from server.db import record_match_player
from server.docker_sandbox import SandboxUnavailableError, run_sandboxed

_logger = logging.getLogger(__name__)

#: Job discriminator: the worker routes these through ``run_sandboxed``.
SUBMISSION_KIND = "submission"

#: Number of AI opponents a submitted bot faces.
SUBMISSION_FILL_COUNT = 2


def build_submission_job(
    *,
    job_id: str,
    player_id: str,
    bot_id: int,
    source: str,
    emoji: str,
    results_dir: str = "results",
    seed: int | None = None,
) -> dict[str, Any]:
    """Build a ``kind='submission'`` job for the match queue.

    Carries the submitter's SOURCE plus the player/bot binding used for
    attribution.  Fill-opponent sources are gathered later, in the worker.
    """
    return {
        "kind": SUBMISSION_KIND,
        "job_id": job_id,
        "player_id": player_id,
        "bot_id": bot_id,
        "bot_source": source,
        "submitter_emoji": emoji,
        "results_dir": results_dir,
        "seed": seed,
    }


def gather_fill_sources(count: int) -> list[str]:
    """Return SOURCE strings for ``count`` AI fill opponents.

    Reuses the trusted preset fill-bot machinery but keeps only the source
    text, because the executor (``run_sandboxed``) compiles source, not
    configs.
    """
    from server.fill_bots import generate_fill_bots

    return [bot["source"] for bot in generate_fill_bots(count, skill_level=0.5)]


def _submitter_credit_config(job: dict[str, Any]) -> list[dict[str, Any]]:
    """Config list crediting only the submitter (fill bots earn nothing)."""
    return [{"player_id": job["player_id"], "emoji": job.get("submitter_emoji")}]


def run_submission_job(
    conn: sqlite3.Connection, job: dict[str, Any]
) -> int | None:
    """Run one submission job through the sandbox and persist the result.

    Returns the allocated match_id on success, or ``None`` when the sandbox is
    unavailable (fail-closed) or the run errors.  No match file is written
    unless ``run_sandboxed`` returns a full result, so a failed job never
    leaves a corrupt/half-written match behind.
    """
    results_dir = job.get("results_dir", "results")
    sources = [job["bot_source"], *gather_fill_sources(SUBMISSION_FILL_COUNT)]
    match_id = next_match_id(results_dir)
    match_config = {"match_id": match_id, "seed": job.get("seed")}

    try:
        match_data = run_sandboxed(sources, match_config)
    except SandboxUnavailableError as exc:
        _logger.error(
            "Submission job %s FAILED closed: %s", job.get("job_id"), exc
        )
        return None
    except Exception as exc:  # noqa: BLE001 -- untrusted code; isolate failures
        _logger.error("Submission job %s errored: %s", job.get("job_id"), exc)
        return None

    write_match(match_data, results_dir)
    record_match_player(conn, match_id, job["player_id"], job["bot_id"])
    award_match_coins(conn, match_data, _submitter_credit_config(job))
    _logger.info(
        "Submission match %s completed for player %s",
        match_id,
        job["player_id"],
    )
    return match_id
