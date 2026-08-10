"""Match queue worker -- polls queue, runs matches, stores results."""

from __future__ import annotations

import logging
import os
import signal

from engine.game import run_match
from engine.match_writer import write_match
from server.coin_rewards import award_match_coins
from server.db import init_db
from server.queue import dequeue_match
from server.submission import SUBMISSION_KIND, run_submission_job

_logger = logging.getLogger(__name__)

_running = True


def _shutdown(sig: int, frame: object) -> None:
    """Signal handler for graceful shutdown."""
    global _running
    _running = False


def _process_regular_job(conn: object, job: dict) -> None:
    """Run a trusted lobby/tournament job whose configs carry decide_func."""
    bot_configs = job["bot_configs"]
    match_id = job.get("match_id", 1)
    seed = job.get("seed")
    results_dir = job.get("results_dir", "results")

    try:
        match_data = run_match(bot_configs, match_id=match_id, seed=seed)
        write_match(match_data, results_dir)
        award_match_coins(conn, match_data, bot_configs)
        _logger.info("Match %s completed", match_id)
    except Exception as exc:
        _logger.error("Match %s failed: %s", match_id, exc)


def main() -> None:
    """Poll the match queue and process jobs until shutdown.

    Jobs are routed by ``kind``: ``"submission"`` jobs carry untrusted bot
    SOURCE and run through the fail-closed sandbox (run_submission_job ->
    run_sandboxed); everything else is a trusted config job (run_match).
    """
    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)
    conn = init_db(os.environ.get("DB_PATH", "data/npcwars.db"))
    _logger.info("Worker started, polling queue...")

    while _running:
        job = dequeue_match(timeout=1)
        if job is None:
            continue
        if job.get("kind") == SUBMISSION_KIND:
            run_submission_job(conn, job)
        else:
            _process_regular_job(conn, job)


if __name__ == "__main__":
    main()
