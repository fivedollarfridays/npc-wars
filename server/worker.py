"""Match queue worker -- polls queue, runs matches, stores results."""

from __future__ import annotations

import logging
import os
import signal
import sys

from engine.game import run_match
from engine.match_writer import write_match
from server.coin_rewards import award_match_coins
from server.db import init_db
from server.docker_sandbox import SANDBOX_OPT_IN_ENV, sandbox_preflight
from server.heartbeat import heartbeat_path, touch_heartbeat
from server.logging_setup import configure_logging
from server.queue import dequeue_match, init_backend
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


def log_sandbox_preflight() -> dict:
    """Log whether the worker can actually reach the Docker sandbox.

    The worker runs untrusted submissions through an ephemeral container, so
    it needs a docker CLI plus a mounted ``/var/run/docker.sock`` (see
    docker-compose.yml) and the sandbox image built on the host daemon. When
    that is missing every submission fails closed one job at a time; this
    turns it into one unmistakable startup line.
    """
    report = sandbox_preflight()
    if report["ok"]:
        _logger.info(
            "Sandbox preflight OK: docker daemon reachable, image %s present",
            report["image_name"],
        )
        return report
    _logger.error(
        "Sandbox preflight FAILED (docker=%s image=%s, image %s): submissions "
        "will fail closed. Mount /var/run/docker.sock into this container and "
        "build the sandbox image on the host daemon. Do NOT set %s.",
        report["docker"],
        report["image"],
        report["image_name"],
        SANDBOX_OPT_IN_ENV,
    )
    return report


def poll_once(conn: object) -> bool:
    """Run one poll cycle: beat, take a job if there is one, run it.

    Returns True when a job was taken. Nothing in a single cycle is allowed
    to end the worker: both the dequeue and the job run are wrapped, because
    a silently-exiting worker was exactly the UP-5 P2 failure mode. The
    heartbeat is touched every cycle -- including empty and failed ones --
    since it attests that *the loop* is running, not that work arrived.
    """
    touch_heartbeat()
    try:
        job = dequeue_match(timeout=1)
    except Exception:
        _logger.exception("Queue poll failed; continuing")
        return False
    if job is None:
        return False

    try:
        if job.get("kind") == SUBMISSION_KIND:
            run_submission_job(conn, job)
        else:
            _process_regular_job(conn, job)
    except Exception:
        _logger.exception("Job %s failed; continuing", job.get("job_id", "?"))
    return True


def startup() -> object:
    """Wire signals, open the DB, and report the runtime the loop depends on.

    Everything here is announced in the logs because each one has silently
    diverged from the app's in a real bring-up: the DB path, the results
    dir, the queue backend, and whether the sandbox is reachable at all.
    """
    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    db_path = os.environ.get("DB_PATH", "data/npcwars.db")
    conn = init_db(db_path)
    _logger.info(
        "Worker starting | DB=%s | results=%s | heartbeat=%s",
        db_path,
        os.environ.get("RESULTS_DIR", "results"),
        heartbeat_path(),
    )
    init_backend()
    log_sandbox_preflight()
    return conn


def main() -> int:
    """Poll the match queue and process jobs until shutdown.

    Jobs are routed by ``kind``: ``"submission"`` jobs carry untrusted bot
    SOURCE and run through the fail-closed sandbox (run_submission_job ->
    run_sandboxed); everything else is a trusted config job (run_match).
    """
    configure_logging()
    try:
        conn = startup()
        _logger.info("Worker started, polling queue...")
        while _running:
            poll_once(conn)
    except BaseException:
        # Never die quietly. This covers startup too: in strict queue mode an
        # unreachable Redis raises here, and the operator needs the reason in
        # `docker compose logs worker`, not a bare non-zero exit.
        _logger.exception("Worker terminated by an unhandled exception")
        return 1

    _logger.info("Worker stopped cleanly")
    return 0


if __name__ == "__main__":
    sys.exit(main())
