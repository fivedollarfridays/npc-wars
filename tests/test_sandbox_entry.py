"""Tests for sandbox_entry — the Docker container entrypoint.

These run WITHOUT Docker: they exercise the entrypoint's importable core
(run_match_from_payload) and its stdin/stdout/stderr wrapper (main) directly,
using the real load_bot_from_source + run_match (stdlib-only engine).
"""

from __future__ import annotations

import io
import json

import sandbox_entry

# Three real, scan-clean bot sources — enough for an actual match.
_BOT_TEMPLATE = """\
BOT_NAME = "Bot{n}"
BOT_EMOJI = "{e}"
BOT_BIO = "test bot {n}"
def decide(state):
    return ("rest",)
"""


def _sources(count: int = 3) -> list[str]:
    return [_BOT_TEMPLATE.format(n=i, e=chr(65 + i)) for i in range(count)]


def _payload(count: int = 3, **config: object) -> dict[str, object]:
    return {"bots": _sources(count), "config": config}


# -- Cycle 1: core runs a REAL match, not the sandbox_ok stub -----------------


def test_core_returns_real_match_dict() -> None:
    """run_match_from_payload returns a real match, not {'status': 'sandbox_ok'}."""
    result = sandbox_entry.run_match_from_payload(_payload(seed=42))
    assert isinstance(result, dict)
    assert result.get("status") != "sandbox_ok"
    assert "winner" in result
    assert "rounds" in result
    assert "players" in result


def test_core_honors_match_id_and_seed() -> None:
    """config match_id/seed flow into run_match (deterministic with a seed)."""
    result = sandbox_entry.run_match_from_payload(_payload(match_id=77, seed=7))
    assert result["match_id"] == 77
    again = sandbox_entry.run_match_from_payload(_payload(match_id=77, seed=7))
    assert result["winner"] == again["winner"]


def test_core_result_is_json_serializable() -> None:
    """The returned match dict round-trips through JSON (container prints it)."""
    result = sandbox_entry.run_match_from_payload(_payload(seed=1))
    json.dumps(result)  # must not raise


# -- Cycle 2: main() happy path (stdin -> stdout, exit 0) ---------------------


def test_main_reads_stdin_writes_match_json_exit_zero() -> None:
    """main() reads a JSON payload from stdin and writes a real match to stdout."""
    stdin = io.StringIO(json.dumps(_payload(seed=3)))
    stdout, stderr = io.StringIO(), io.StringIO()
    code = sandbox_entry.main(stdin=stdin, stdout=stdout, stderr=stderr)
    assert code == 0
    out = json.loads(stdout.getvalue())
    assert out.get("status") != "sandbox_ok"
    assert "winner" in out and "rounds" in out
    assert stderr.getvalue() == ""


# -- Cycle 3: error paths (non-zero exit, message on stderr) ------------------


def test_main_malformed_stdin_exits_nonzero() -> None:
    """Non-JSON stdin -> non-zero exit, nothing on stdout, message on stderr."""
    stdin = io.StringIO("this is not json {")
    stdout, stderr = io.StringIO(), io.StringIO()
    code = sandbox_entry.main(stdin=stdin, stdout=stdout, stderr=stderr)
    assert code != 0
    assert stdout.getvalue() == ""
    assert stderr.getvalue() != ""


def test_main_bot_failing_scan_exits_nonzero() -> None:
    """A bot that fails the security scan -> non-zero exit with stderr message."""
    bad = "import os\nBOT_NAME='x'\nBOT_EMOJI='x'\ndef decide(s):\n    return ('rest',)\n"
    payload = {"bots": [bad, bad], "config": {}}
    stdin = io.StringIO(json.dumps(payload))
    stdout, stderr = io.StringIO(), io.StringIO()
    code = sandbox_entry.main(stdin=stdin, stdout=stdout, stderr=stderr)
    assert code != 0
    assert stderr.getvalue() != ""


# -- Cycle 4: load_bot_from_source moved but still re-exported ----------------


def test_load_bot_from_source_re_exported_from_docker_sandbox() -> None:
    """server.docker_sandbox still exposes the (moved) compile logic."""
    from engine.bot_loader import load_bot_from_source as canonical
    from server.docker_sandbox import load_bot_from_source as re_exported

    assert re_exported is canonical


def test_entrypoint_imports_load_bot_from_engine_not_server() -> None:
    """The entrypoint uses engine.bot_loader so the slim image needs no server pkg."""
    from engine.bot_loader import load_bot_from_source as canonical

    assert sandbox_entry.load_bot_from_source is canonical
