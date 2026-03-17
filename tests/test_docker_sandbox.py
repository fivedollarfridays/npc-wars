"""Tests for server.docker_sandbox — Docker sandbox with fallback."""

from __future__ import annotations

from unittest.mock import patch

from server.docker_sandbox import (
    DOCKER_IMAGE,
    SANDBOX_TIMEOUT,
    _docker_available,
    _run_in_docker,
    _run_in_process,
    load_bot_from_source,
    run_sandboxed,
)


# -- Cycle 1: constants and _docker_available ---------------------------------


def test_sandbox_timeout_constant() -> None:
    """Timeout is 10 seconds."""
    assert SANDBOX_TIMEOUT == 10


def test_docker_image_constant() -> None:
    """Docker image name is set."""
    assert DOCKER_IMAGE == "npcwars-sandbox:latest"


def test_docker_available_returns_bool() -> None:
    """_docker_available always returns a bool."""
    result = _docker_available()
    assert isinstance(result, bool)


def test_docker_available_false_when_missing() -> None:
    """Returns False when docker binary not found."""
    with patch("server.docker_sandbox.subprocess.run", side_effect=FileNotFoundError):
        assert _docker_available() is False


# -- Cycle 2: load_bot_from_source and _run_in_process ------------------------

_SIMPLE_BOT = """\
import random
BOT_NAME = "TestBot"
BOT_EMOJI = "T"
BOT_BIO = "test"
def decide(state):
    return ("rest",)
"""


def test_load_bot_from_source_returns_config() -> None:
    """load_bot_from_source exec-s source and returns bot config dict."""
    config = load_bot_from_source(_SIMPLE_BOT, "test_0")
    assert config["name"] == "TestBot"
    assert config["emoji"] == "T"
    assert callable(config["decide_func"])


def test_load_bot_from_source_invalid_raises() -> None:
    """Raises ValueError for source missing required attributes."""
    import pytest

    with pytest.raises(ValueError, match="missing"):
        load_bot_from_source("x = 1\n", "bad_bot")


def test_run_in_process_returns_match_data() -> None:
    """_run_in_process runs a match and returns dict with winner and rounds."""
    bot_src = _SIMPLE_BOT
    # Need at least 2 bots for a match
    sources = [bot_src, bot_src.replace('"T"', '"U"').replace("TestBot", "Bot2")]
    result = _run_in_process(sources, {"match_id": 999})
    assert isinstance(result, dict)
    assert "winner" in result
    assert "rounds" in result


# -- Cycle 3: _run_in_docker and run_sandboxed dispatch -----------------------


def test_run_in_docker_passes_network_none() -> None:
    """_run_in_docker invokes docker run with --network=none."""
    with patch("server.docker_sandbox.subprocess.run") as mock_run:
        mock_run.return_value = type(
            "R", (), {"returncode": 0, "stdout": '{"winner": "x"}', "stderr": ""}
        )()
        _run_in_docker(["src1"], {"match_id": 1})
        args = mock_run.call_args[0][0]
        assert "--network=none" in args


def test_run_in_docker_raises_on_failure() -> None:
    """_run_in_docker raises RuntimeError on non-zero exit."""
    import pytest

    with patch("server.docker_sandbox.subprocess.run") as mock_run:
        mock_run.return_value = type(
            "R", (), {"returncode": 1, "stdout": "", "stderr": "boom"}
        )()
        with pytest.raises(RuntimeError, match="Sandbox error"):
            _run_in_docker(["src1"], {})


def test_run_sandboxed_uses_fallback_when_no_docker() -> None:
    """run_sandboxed calls _run_in_process when Docker is unavailable."""
    sources = [
        _SIMPLE_BOT,
        _SIMPLE_BOT.replace('"T"', '"U"').replace("TestBot", "Bot2"),
    ]
    with patch("server.docker_sandbox._docker_available", return_value=False):
        result = run_sandboxed(sources, {"match_id": 500})
    assert isinstance(result, dict)
    assert "winner" in result


def test_run_sandboxed_uses_docker_when_available() -> None:
    """run_sandboxed calls _run_in_docker when Docker is available."""
    with (
        patch("server.docker_sandbox._docker_available", return_value=True),
        patch("server.docker_sandbox._run_in_docker", return_value={"ok": True}) as mock_docker,
    ):
        result = run_sandboxed(["src"], {"match_id": 1})
    mock_docker.assert_called_once_with(["src"], {"match_id": 1})
    assert result == {"ok": True}


def test_run_sandboxed_default_config() -> None:
    """run_sandboxed uses empty dict when match_config is None."""
    with (
        patch("server.docker_sandbox._docker_available", return_value=True),
        patch("server.docker_sandbox._run_in_docker", return_value={}) as mock_docker,
    ):
        run_sandboxed(["src"])
    mock_docker.assert_called_once_with(["src"], {})
