"""Tests for scripts/render_video.py CLI."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = str(Path(__file__).resolve().parent.parent / "scripts" / "render_video.py")

MINIMAL_MATCH = {
    "match_id": 1,
    "winner": "\U0001f986",
    "duration_rounds": 2,
    "seed": 42,
    "grid_size": 5,
    "players": [
        {"name": "DuckBot", "emoji": "\U0001f986", "bio": "test", "author": "test"},
        {"name": "GooseBot", "emoji": "\U0001fab7", "bio": "test", "author": "test"},
    ],
    "rounds": [
        {
            "round": 1,
            "storm_border": 0,
            "bots": [
                {"name": "DuckBot", "emoji": "\U0001f986", "x": 0, "y": 0, "hp": 100, "energy": 100},
                {"name": "GooseBot", "emoji": "\U0001fab7", "x": 1, "y": 1, "hp": 80, "energy": 90},
            ],
            "events": [],
        },
        {
            "round": 2,
            "storm_border": 0,
            "bots": [
                {"name": "DuckBot", "emoji": "\U0001f986", "x": 0, "y": 0, "hp": 100, "energy": 100},
                {"name": "GooseBot", "emoji": "\U0001fab7", "x": 1, "y": 1, "hp": 0, "energy": 0},
            ],
            "events": [
                {"type": "death", "emoji": "\U0001fab7", "killed_by": "\U0001f986", "cause": "attack"},
            ],
        },
    ],
    "eliminations": [
        {"round": 2, "emoji": "\U0001fab7", "cause": "attack", "killed_by": "\U0001f986"},
    ],
}


@pytest.fixture()
def match_json(tmp_path: Path) -> Path:
    """Write minimal match JSON to a temp file and return its path."""
    p = tmp_path / "match_001.json"
    p.write_text(json.dumps(MINIMAL_MATCH))
    return p


def _run_cli(*args: str, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    """Run the render_video.py script with the given arguments."""
    return subprocess.run(
        [sys.executable, SCRIPT, *args],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


class TestCliProducesMp4:
    """Test that the CLI produces an MP4 file."""

    def test_cli_produces_mp4(self, match_json: Path, tmp_path: Path) -> None:
        output = tmp_path / "out.mp4"
        result = _run_cli(str(match_json), "--output", str(output))
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert output.exists()
        assert output.stat().st_size > 0


class TestCliDefaultOutput:
    """Test default output path derivation."""

    def test_cli_default_output_path(self, match_json: Path) -> None:
        result = _run_cli(str(match_json))
        expected_mp4 = match_json.with_suffix(".mp4")
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert expected_mp4.exists()
        assert expected_mp4.stat().st_size > 0


class TestCliCustomOutput:
    """Test custom --output path."""

    def test_cli_custom_output_path(self, match_json: Path, tmp_path: Path) -> None:
        custom = tmp_path / "custom_dir" / "my_video.mp4"
        custom.parent.mkdir(parents=True, exist_ok=True)
        result = _run_cli(str(match_json), "--output", str(custom))
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert custom.exists()


class TestCliCustomFps:
    """Test --fps flag accepted without error."""

    def test_cli_custom_fps(self, match_json: Path, tmp_path: Path) -> None:
        output = tmp_path / "fps_test.mp4"
        result = _run_cli(str(match_json), "--fps", "2", "--output", str(output))
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert output.exists()


class TestCliMissingInput:
    """Test that a missing input file exits nonzero."""

    def test_cli_missing_input_exits_nonzero(self, tmp_path: Path) -> None:
        missing = tmp_path / "nonexistent.json"
        result = _run_cli(str(missing))
        assert result.returncode == 1
        assert "not found" in result.stderr.lower() or "error" in result.stderr.lower()


class TestCliInvalidJson:
    """Test that invalid JSON exits nonzero."""

    def test_cli_invalid_json_exits_nonzero(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.json"
        bad.write_text("{not valid json!!!")
        result = _run_cli(str(bad))
        assert result.returncode == 1
        assert "invalid json" in result.stderr.lower() or "error" in result.stderr.lower()
