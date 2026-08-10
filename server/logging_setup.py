"""Process-wide logging configuration for the API and the queue worker.

Neither ``server/worker.py`` nor the uvicorn-hosted app configured the root
logger, so every ``_logger.info(...)`` in ``server/`` went nowhere:
``docker compose logs worker`` was empty even with ``PYTHONUNBUFFERED=1``, and
uvicorn's own logging config only attaches handlers to the ``uvicorn.*``
loggers. That made a live bring-up undebuggable (UP-5 P2).

Both entrypoints call :func:`configure_logging` first thing so records land on
**stdout** (where Docker's log driver collects them) at a level the operator
controls via ``NPCWARS_LOG_LEVEL``.
"""

from __future__ import annotations

import logging
import os
import sys
from typing import TextIO

__all__ = [
    "DEFAULT_LOG_LEVEL",
    "LOG_FORMAT",
    "LOG_LEVEL_ENV",
    "configure_logging",
    "resolve_log_level",
]

#: Operator-facing knob: ``DEBUG``/``INFO``/``WARNING``/... or a number.
LOG_LEVEL_ENV: str = "NPCWARS_LOG_LEVEL"

DEFAULT_LOG_LEVEL: int = logging.INFO

LOG_FORMAT: str = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def resolve_log_level(raw: str | None) -> int:
    """Map an env value to a logging level, defaulting to INFO.

    Accepts level names (case-insensitive) and numeric strings. Anything
    unrecognised -- including ``None`` and blank -- resolves to INFO rather
    than raising: a typo in a deploy env must never silence the worker or
    stop it from booting.
    """
    if raw is None:
        return DEFAULT_LOG_LEVEL
    candidate = raw.strip()
    if not candidate:
        return DEFAULT_LOG_LEVEL
    if candidate.isdigit():
        return int(candidate)
    level = logging.getLevelName(candidate.upper())
    return level if isinstance(level, int) else DEFAULT_LOG_LEVEL


def configure_logging(stream: TextIO | None = None) -> int:
    """Send root-logger records to stdout at the ``NPCWARS_LOG_LEVEL`` level.

    ``force=True`` on purpose: a handler installed by an importing library
    (or a previous ``basicConfig`` call) must not be able to keep the
    process silent. Returns the level actually applied, so callers can log
    it back for confirmation.
    """
    level = resolve_log_level(os.environ.get(LOG_LEVEL_ENV))
    logging.basicConfig(
        stream=stream if stream is not None else sys.stdout,
        level=level,
        format=LOG_FORMAT,
        force=True,
    )
    return level
