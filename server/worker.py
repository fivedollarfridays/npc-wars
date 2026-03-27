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

_logger = logging.getLogger(__name__)

_running = True


def _shutdown(sig: int, frame: object) -> None:
    """Signal handler for graceful shutdown."""
    global _running
    _running = False


def main() -> None:
    """Poll the match queue and process jobs until shutdown."""
    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)
    conn = init_db(os.environ.get("DB_PATH", "data/npcwars.db"))
    _logger.info("Worker started, polling queue...")

    while _running:
        job = dequeue_match(timeout=1)
        if job is None:
            continue

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


if __name__ == "__main__":
    main()
