"""Docker sandbox for match execution, with an opt-in in-process fallback."""

from __future__ import annotations

import json
import os
import subprocess
from typing import Any

# Re-exported: the reusable bot-compile logic now lives in a dep-light module
# (engine.bot_loader) so the Docker sandbox image can import it without the
# server package. Kept importable from here for backward compatibility.
from engine.bot_loader import load_bot_from_source

__all__ = [
    "DOCKER_IMAGE",
    "SANDBOX_OPT_IN_ENV",
    "SANDBOX_OPT_IN_VALUE",
    "SANDBOX_TIMEOUT",
    "SandboxUnavailableError",
    "load_bot_from_source",
    "run_sandboxed",
]

SANDBOX_TIMEOUT: int = 10
DOCKER_IMAGE: str = "npcwars-sandbox:latest"

SANDBOX_OPT_IN_ENV: str = "NPCWARS_ALLOW_UNSANDBOXED"
SANDBOX_OPT_IN_VALUE: str = "1"


class SandboxUnavailableError(RuntimeError):
    """Raised when no sandbox is available and unsandboxed execution is not allowed.

    Callers should treat this as a failed match/job (error state), not as a
    reason to run submitted bot source some other way.
    """


def _unsandboxed_allowed() -> bool:
    """Whether running submitted bot source in-process is explicitly permitted.

    Exact-match allow-list on purpose: only the literal string "1" enables the
    in-process path. Unset, blank, "true", "yes", "0", or anything else means
    NOT allowed. Fail-closed is the point -- production and any environment
    that never heard of this switch stays dark, and developers/CI opt in
    deliberately rather than inheriting the unsafe path from a typo or a
    truthy-looking value.
    """
    return os.environ.get(SANDBOX_OPT_IN_ENV) == SANDBOX_OPT_IN_VALUE


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


def _run_in_process(bot_sources: list[str], match_config: dict[str, Any]) -> dict[str, Any]:
    """Opt-in fallback: run the match in *this* process when Docker is unavailable.

    This executes submitted bot source in the API/worker process behind only an
    import-restriction shim. The opt-in is re-checked here, not just in
    run_sandboxed(), so a future caller cannot reach it by accident.
    """
    if not _unsandboxed_allowed():
        raise SandboxUnavailableError(
            "Refusing to execute submitted bot source in-process: "
            f"{SANDBOX_OPT_IN_ENV} is not set to {SANDBOX_OPT_IN_VALUE!r}."
        )

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
    """Run a match in a sandbox. Uses Docker; fails closed when Docker is absent.

    The in-process fallback executes submitted (arbitrary) bot source inside
    this process, so it only runs when NPCWARS_ALLOW_UNSANDBOXED is exactly
    "1". Otherwise a missing Docker daemon raises SandboxUnavailableError.
    """
    config = match_config or {}
    if _docker_available():
        return _run_in_docker(bot_sources, config)
    if not _unsandboxed_allowed():
        raise SandboxUnavailableError(
            "Docker sandbox unavailable and unsandboxed execution is not permitted. "
            "Refusing to run submitted bot source in-process. "
            f"Start the Docker daemon (image {DOCKER_IMAGE}), or -- for local "
            f"development/CI only -- set {SANDBOX_OPT_IN_ENV}={SANDBOX_OPT_IN_VALUE}."
        )
    return _run_in_process(bot_sources, config)
