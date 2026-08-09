"""Fail-closed guarantees for server.docker_sandbox (UP-1).

Submitted bot source is arbitrary user Python. Executing it in-process
(`_run_in_process`) puts it inside the API/worker process behind only an
import-restriction shim. That path must be unreachable unless an operator
explicitly opts in via NPCWARS_ALLOW_UNSANDBOXED=1.

These tests deliberately remove the opt-in that tests/conftest.py sets for
the rest of the suite, so they prove the *default* (production) behavior.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from server.docker_sandbox import (
    SANDBOX_OPT_IN_ENV,
    SandboxUnavailableError,
    run_sandboxed,
)

_SIMPLE_BOT = """\
BOT_NAME = "TestBot"
BOT_EMOJI = "T"
BOT_BIO = "test"
def decide(state):
    return ("rest",)
"""

_BOT_SOURCES = [
    _SIMPLE_BOT,
    _SIMPLE_BOT.replace('"T"', '"U"').replace("TestBot", "Bot2"),
]


@pytest.fixture
def no_opt_in(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove the suite-wide opt-in so the production default is under test."""
    monkeypatch.delenv(SANDBOX_OPT_IN_ENV, raising=False)


# -- Cycle 1: no Docker + no opt-in => hard failure, never in-process ---------


def test_run_sandboxed_raises_when_docker_unavailable_and_no_opt_in(
    no_opt_in: None,
) -> None:
    """Docker down and no opt-in: run_sandboxed refuses to run the match."""
    with patch("server.docker_sandbox._docker_available", return_value=False):
        with pytest.raises(SandboxUnavailableError):
            run_sandboxed(_BOT_SOURCES, {"match_id": 500})


def test_run_sandboxed_never_calls_in_process_without_opt_in(
    no_opt_in: None,
) -> None:
    """The in-process executor is not merely avoided -- it is never invoked."""
    with (
        patch("server.docker_sandbox._docker_available", return_value=False),
        patch("server.docker_sandbox._run_in_process") as spy,
    ):
        with pytest.raises(SandboxUnavailableError):
            run_sandboxed(_BOT_SOURCES, {"match_id": 500})
    spy.assert_not_called()


# -- Cycle 2: the opt-in is an exact-match allow-list, not truthiness ---------


@pytest.mark.parametrize(
    "value",
    ["true", "True", "yes", "on", "0", "", " ", "1 ", " 1", "01", "y"],
)
def test_run_sandboxed_rejects_non_exact_opt_in_values(
    no_opt_in: None, monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    """Only the literal "1" opts in; truthy-looking values still fail closed."""
    monkeypatch.setenv(SANDBOX_OPT_IN_ENV, value)
    with (
        patch("server.docker_sandbox._docker_available", return_value=False),
        patch("server.docker_sandbox._run_in_process") as spy,
    ):
        with pytest.raises(SandboxUnavailableError):
            run_sandboxed(_BOT_SOURCES, {"match_id": 501})
    spy.assert_not_called()


# -- Cycle 3: positive controls -- the opt-in and Docker paths still work -----


def test_run_sandboxed_runs_in_process_with_exact_opt_in(
    no_opt_in: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Opt-in "1" restores the in-process path (positive control for the spy).

    Without this, the fail-closed assertions above could pass vacuously -- e.g.
    if run_sandboxed raised for an unrelated reason on every input.
    """
    monkeypatch.setenv(SANDBOX_OPT_IN_ENV, "1")
    with patch("server.docker_sandbox._docker_available", return_value=False):
        result = run_sandboxed(_BOT_SOURCES, {"match_id": 502})
    assert isinstance(result, dict)
    assert "winner" in result


def test_run_sandboxed_uses_docker_regardless_of_opt_in(
    no_opt_in: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When Docker is available it is used, and the opt-in is irrelevant."""
    for value in (None, "1", "true"):
        if value is None:
            monkeypatch.delenv(SANDBOX_OPT_IN_ENV, raising=False)
        else:
            monkeypatch.setenv(SANDBOX_OPT_IN_ENV, value)
        with (
            patch("server.docker_sandbox._docker_available", return_value=True),
            patch("server.docker_sandbox._run_in_docker", return_value={"ok": True}) as docker,
            patch("server.docker_sandbox._run_in_process") as in_process,
        ):
            assert run_sandboxed(["src"], {"match_id": 1}) == {"ok": True}
        docker.assert_called_once_with(["src"], {"match_id": 1})
        in_process.assert_not_called()


def test_sandbox_unavailable_error_is_a_runtime_error() -> None:
    """Existing `except RuntimeError` handlers keep catching sandbox failures."""
    assert issubclass(SandboxUnavailableError, RuntimeError)


# -- Cycle 4: the executor itself refuses, not just the dispatcher -----------


def test_run_in_process_refuses_directly_without_opt_in(no_opt_in: None) -> None:
    """A future caller cannot reach the unsandboxed executor by calling it directly."""
    from server.docker_sandbox import _run_in_process

    with pytest.raises(SandboxUnavailableError):
        _run_in_process(_BOT_SOURCES, {"match_id": 503})


def test_run_in_process_runs_with_opt_in(
    no_opt_in: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Positive control for the direct-call guard."""
    from server.docker_sandbox import _run_in_process

    monkeypatch.setenv(SANDBOX_OPT_IN_ENV, "1")
    result = _run_in_process(_BOT_SOURCES, {"match_id": 504})
    assert "winner" in result
