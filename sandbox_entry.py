#!/usr/bin/env python3
"""Docker sandbox entrypoint: run one match from a stdin JSON payload.

This is the ``CMD`` of ``Dockerfile.sandbox``. ``server.docker_sandbox``'s
``_run_in_docker`` pipes ``{"bots": [source, ...], "config": {...}}`` to the
container's stdin and ``json.loads`` its stdout expecting a real match result.

Contract:
  * stdin  <- JSON: {"bots": [src, ...], "config": {"match_id"?, "seed"?}}
  * stdout -> JSON: the match_data dict (same shape write_match serializes)
  * exit 0 on success; on ANY error, exit non-zero with the message on stderr
    (so _run_in_docker's returncode check raises RuntimeError).

Import hygiene: imports only ``engine`` (stdlib-only engine + bot_loader), so
the sandbox image needs just ``engine/`` + ``data/`` + this file — no server
package, no third-party deps.
"""

from __future__ import annotations

import json
import sys
from typing import Any, TextIO

from engine.bot_loader import load_bot_from_source
from engine.game import run_match


def run_match_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Compile each bot source and run a single match; return the match dict."""
    sources = payload["bots"]
    config = payload.get("config") or {}
    bot_configs = [
        load_bot_from_source(src, f"bot_{i}") for i, src in enumerate(sources)
    ]
    return run_match(
        bot_configs,
        match_id=config.get("match_id", 1),
        seed=config.get("seed"),
    )


def _dump_json(result: dict[str, Any]) -> str:
    """Serialize the match result, coercing any stray non-JSON value to str."""
    try:
        return json.dumps(result)
    except TypeError:
        return json.dumps(result, default=str)


def main(
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Read a payload from stdin, run the match, write JSON to stdout.

    Returns 0 on success, 1 on any failure (message written to stderr).
    """
    stdin = stdin if stdin is not None else sys.stdin
    stdout = stdout if stdout is not None else sys.stdout
    stderr = stderr if stderr is not None else sys.stderr
    try:
        payload = json.loads(stdin.read())
        result = run_match_from_payload(payload)
        stdout.write(_dump_json(result))
    except Exception as exc:  # noqa: BLE001 — surface any failure as exit 1
        stderr.write(f"{type(exc).__name__}: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
