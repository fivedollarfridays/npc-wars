"""Post-match broadcast inbox hook (T70.2).

Writes a copy of the finalized match JSON to ``BROADCAST_INBOX_DIR`` for the
agentgrounds-web watcher daemon to pick up. No-op when the env var is unset,
logs a warning and swallows errors on write failure so the match still completes.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

__all__ = ["write_to_inbox"]

_ENV_VAR = "BROADCAST_INBOX_DIR"
_log = logging.getLogger(__name__)


def write_to_inbox(match_data: dict[str, Any], game: str) -> str | None:
    """Copy ``match_data`` to ``{BROADCAST_INBOX_DIR}/{game}/{match_id}.json``.

    Returns the written path, or ``None`` if the env var is unset or the write
    failed. Never raises.
    """
    inbox_root = os.environ.get(_ENV_VAR)
    if not inbox_root:
        return None

    match_id = match_data.get("match_id")
    if match_id is None:
        _log.warning("broadcast inbox skipped: match_data missing match_id")
        return None

    target_dir = os.path.join(inbox_root, game)
    target_path = os.path.join(target_dir, f"{match_id}.json")

    try:
        os.makedirs(target_dir, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(match_data, f, indent=2, default=str)
    except OSError as exc:
        _log.warning("broadcast inbox write failed (%s): %s", target_path, exc)
        return None

    return target_path
