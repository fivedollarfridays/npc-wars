"""Docker sandbox for match execution with multiprocessing fallback."""

from __future__ import annotations

import json
import subprocess
from typing import Any

__all__ = [
    "DOCKER_IMAGE",
    "SANDBOX_TIMEOUT",
    "run_sandboxed",
]

SANDBOX_TIMEOUT: int = 10
DOCKER_IMAGE: str = "npcwars-sandbox:latest"


def _docker_available() -> bool:
    """Check if Docker daemon is running."""
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def load_bot_from_source(source: str, label: str) -> dict[str, Any]:
    """Exec bot source code and return a bot config dict.

    Source is pre-scanned for security violations before execution.
    Raises ValueError if scan fails or required attributes are missing.
    """
    from engine.bot_scanner import scan_bot_source

    errors = scan_bot_source(source)
    if errors:
        raise ValueError(f"Bot '{label}' failed scan: {'; '.join(errors[:3])}")

    import builtins as _builtins

    _safe_builtins = {
        k: getattr(_builtins, k)
        for k in (
            "__import__", "abs", "all", "any", "bool", "dict", "enumerate",
            "float", "int", "len", "list", "max", "min", "print", "range",
            "round", "set", "sorted", "str", "sum", "tuple", "zip",
            "True", "False", "None", "isinstance", "callable", "hasattr",
            "getattr", "setattr", "type", "object", "property", "staticmethod",
            "classmethod", "super", "map", "filter", "reversed", "iter", "next",
        )
        if hasattr(_builtins, k)
    }
    namespace: dict[str, Any] = {"__builtins__": _safe_builtins}
    exec(compile(source, f"<{label}>", "exec"), namespace)  # noqa: S102

    name = namespace.get("BOT_NAME")
    emoji = namespace.get("BOT_EMOJI")
    decide = namespace.get("decide")

    if not name or not emoji or not callable(decide):
        raise ValueError(
            f"Bot source '{label}' missing required attributes "
            "(BOT_NAME, BOT_EMOJI, decide)"
        )

    return {
        "name": name,
        "emoji": emoji,
        "bio": namespace.get("BOT_BIO", ""),
        "author": namespace.get("BOT_AUTHOR", "unknown"),
        "decide_func": decide,
    }


def _run_in_process(bot_sources: list[str], match_config: dict[str, Any]) -> dict[str, Any]:
    """Fallback: run match in-process when Docker is unavailable."""
    from engine.game import run_match

    bot_configs = []
    for i, source in enumerate(bot_sources):
        config = load_bot_from_source(source, f"bot_{i}")
        bot_configs.append(config)

    match_id = match_config.get("match_id", 1)
    seed = match_config.get("seed")
    return run_match(bot_configs, match_id=match_id, seed=seed)


def _run_in_docker(
    bot_sources: list[str], match_config: dict[str, Any]
) -> dict[str, Any]:
    """Run match in an ephemeral Docker container with no network."""
    payload = json.dumps({"bots": bot_sources, "config": match_config})
    result = subprocess.run(
        [
            "docker", "run", "--rm",
            "--network=none",
            "--memory=256m",
            "--cpus=1",
            "--pids-limit=50",
            "--read-only",
            f"--stop-timeout={SANDBOX_TIMEOUT}",
            "-i", DOCKER_IMAGE,
        ],
        input=payload,
        capture_output=True,
        text=True,
        timeout=SANDBOX_TIMEOUT + 5,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Sandbox error: {result.stderr[:200]}")
    return json.loads(result.stdout)


def run_sandboxed(
    bot_sources: list[str],
    match_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run a match in a sandbox. Uses Docker if available, else in-process."""
    config = match_config or {}
    if _docker_available():
        return _run_in_docker(bot_sources, config)
    return _run_in_process(bot_sources, config)
