"""Tests for TV rendering pipeline (T64.2)."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any
import pytest


# -- Helpers -----------------------------------------------------------------


def _ks_match() -> dict[str, Any]:
    """Minimal Kill Switch match JSON."""
    return {
        "match_id": 42,
        "game": "kill_switch",
        "date": "2026-04-09T00:00:00",
        "grid_size": 5,
        "winner": "A",
        "duration_rounds": 2,
        "players": [
            {"emoji": "A", "name": "AlphaBot", "bio": "alpha", "author": "auth_a", "x": 1, "y": 1},
            {"emoji": "B", "name": "BetaBot", "bio": "beta", "author": "auth_b", "x": 3, "y": 3},
        ],
        "rounds": [
            {
                "round": 1, "storm_border": 0,
                "bots": [
                    {"emoji": "A", "x": 1, "y": 1, "hp": 100, "energy": 5, "alive": True},
                    {"emoji": "B", "x": 3, "y": 3, "hp": 100, "energy": 5, "alive": True},
                ],
                "events": [],
            },
            {
                "round": 2, "storm_border": 0,
                "bots": [
                    {"emoji": "A", "x": 2, "y": 2, "hp": 80, "energy": 5, "alive": True},
                    {"emoji": "B", "x": 3, "y": 3, "hp": 0, "energy": 5, "alive": False},
                ],
                "events": [{"type": "hit", "attacker": "A", "target": "B", "damage": 100}],
            },
        ],
        "eliminations": [{"emoji": "B", "round": 2, "killed_by": "A", "cause": "damage"}],
        "stats": {
            "A": {"kills": 1, "damage_dealt": 100, "damage_taken": 20, "rounds_survived": 2, "score": 100},
            "B": {"kills": 0, "damage_dealt": 20, "damage_taken": 100, "rounds_survived": 1, "score": 0},
        },
    }


def _cc_match() -> dict[str, Any]:
    """Minimal Code Circuit match JSON."""
    return {
        "game": "code_circuit",
        "winner": "CarX",
        "players": [
            {"emoji": "CarX", "name": "CarX"},
            {"emoji": "CarY", "name": "CarY"},
        ],
        "frames": [
            {"tick": 0, "cars": [{"id": "CarX", "x": 0, "y": 0, "speed": 10, "lap": 1},
                                  {"id": "CarY", "x": 1, "y": 0, "speed": 9, "lap": 1}]},
            {"tick": 30, "cars": [{"id": "CarX", "x": 5, "y": 0, "speed": 12, "lap": 1},
                                   {"id": "CarY", "x": 4, "y": 0, "speed": 11, "lap": 1}]},
        ],
        "results": [
            {"car": "CarX", "position": 1},
            {"car": "CarY", "position": 2},
        ],
        "stats": {
            "CarX": {"points": 25, "position": 1},
            "CarY": {"points": 18, "position": 2},
        },
    }


def _write_match(tmp_path: Path, data: dict, name: str = "match.json") -> Path:
    """Write match JSON to tmp_path and return the file path."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    p = tmp_path / name
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


# -- Cycle 1: KS match pipeline -----------------------------------------------


class TestKsMatchPipeline:
    """process_match produces MP4 + episode JSON for Kill Switch."""

    def test_returns_mp4_and_episode_paths(self, tmp_path: Path) -> None:
        from tv.rendering import process_match

        match_path = _write_match(tmp_path / "queue", _ks_match(), "kill_switch_abc12345.json")
        output_dir = tmp_path / "output"
        mp4_path, episode_path = process_match(str(match_path), str(output_dir))
        assert mp4_path.endswith(".mp4")
        assert episode_path.endswith(".json")

    def test_mp4_file_created(self, tmp_path: Path) -> None:
        from tv.rendering import process_match

        match_path = _write_match(tmp_path / "queue", _ks_match(), "kill_switch_abc12345.json")
        output_dir = tmp_path / "output"
        mp4_path, _ = process_match(str(match_path), str(output_dir))
        assert Path(mp4_path).exists()
        assert Path(mp4_path).stat().st_size > 0

    def test_episode_json_created(self, tmp_path: Path) -> None:
        from tv.rendering import process_match

        match_path = _write_match(tmp_path / "queue", _ks_match(), "kill_switch_abc12345.json")
        output_dir = tmp_path / "output"
        _, episode_path = process_match(str(match_path), str(output_dir))
        assert Path(episode_path).exists()
        ep = json.loads(Path(episode_path).read_text())
        assert "metadata" in ep
        assert "match_commentary" in ep

    def test_episode_has_game_tag(self, tmp_path: Path) -> None:
        from tv.rendering import process_match

        match_path = _write_match(tmp_path / "queue", _ks_match(), "kill_switch_abc12345.json")
        output_dir = tmp_path / "output"
        _, episode_path = process_match(str(match_path), str(output_dir))
        ep = json.loads(Path(episode_path).read_text())
        assert ep["metadata"]["game"] == "kill_switch"


# -- Cycle 2: CC race pipeline ------------------------------------------------


class TestCcRacePipeline:
    """process_match produces MP4 + episode JSON for Code Circuit."""

    def test_returns_mp4_and_episode_paths(self, tmp_path: Path) -> None:
        from tv.rendering import process_match

        match_path = _write_match(tmp_path / "queue", _cc_match(), "code_circuit_def67890.json")
        output_dir = tmp_path / "output"
        mp4_path, episode_path = process_match(str(match_path), str(output_dir))
        assert mp4_path.endswith(".mp4")
        assert episode_path.endswith(".json")

    def test_mp4_file_created(self, tmp_path: Path) -> None:
        from tv.rendering import process_match

        match_path = _write_match(tmp_path / "queue", _cc_match(), "code_circuit_def67890.json")
        output_dir = tmp_path / "output"
        mp4_path, _ = process_match(str(match_path), str(output_dir))
        assert Path(mp4_path).exists()
        assert Path(mp4_path).stat().st_size > 0

    def test_episode_json_created(self, tmp_path: Path) -> None:
        from tv.rendering import process_match

        match_path = _write_match(tmp_path / "queue", _cc_match(), "code_circuit_def67890.json")
        output_dir = tmp_path / "output"
        _, episode_path = process_match(str(match_path), str(output_dir))
        ep = json.loads(Path(episode_path).read_text())
        assert ep["metadata"]["game"] == "code_circuit"

    def test_cc_highlight_reel_has_frames(self, tmp_path: Path) -> None:
        from tv.rendering import process_match

        match_path = _write_match(tmp_path / "queue", _cc_match(), "code_circuit_def67890.json")
        output_dir = tmp_path / "output"
        mp4_path, _ = process_match(str(match_path), str(output_dir))
        assert Path(mp4_path).stat().st_size > 0


# -- Cycle 3: Corrupt input handling -------------------------------------------


class TestCorruptInput:
    """Corrupt JSON logged, does not crash."""

    def test_corrupt_json_raises_value_error(self, tmp_path: Path) -> None:
        from tv.rendering import process_match

        bad_file = tmp_path / "queue" / "bad.json"
        bad_file.parent.mkdir(parents=True, exist_ok=True)
        bad_file.write_text("{not valid json", encoding="utf-8")
        with pytest.raises(ValueError, match="[Cc]orrupt|[Ii]nvalid|JSON"):
            process_match(str(bad_file), str(tmp_path / "output"))

    def test_missing_required_fields_raises(self, tmp_path: Path) -> None:
        from tv.rendering import process_match

        bad_data = {"foo": "bar"}
        match_path = _write_match(tmp_path / "queue", bad_data)
        with pytest.raises(ValueError, match="[Uu]nrecogni|schema"):
            process_match(str(match_path), str(tmp_path / "output"))

    def test_empty_dict_raises(self, tmp_path: Path) -> None:
        from tv.rendering import process_match

        match_path = _write_match(tmp_path / "queue", {})
        with pytest.raises(ValueError, match="[Uu]nrecogni|schema"):
            process_match(str(match_path), str(tmp_path / "output"))


# -- Cycle 4: Queue processing ------------------------------------------------


class TestProcessQueue:
    """process_queue processes entries sequentially, survives errors."""

    def test_processes_all_valid_entries(self, tmp_path: Path) -> None:
        from tv.rendering import process_queue

        queue_dir = tmp_path / "queue"
        queue_dir.mkdir()
        _write_match(queue_dir, _ks_match(), "kill_switch_aaa11111.json")
        _write_match(queue_dir, _ks_match(), "kill_switch_bbb22222.json")
        output_dir = tmp_path / "output"

        results = process_queue(str(queue_dir), str(output_dir))
        successes = [r for r in results if r["ok"]]
        assert len(successes) == 2

    def test_queue_continues_after_corrupt(self, tmp_path: Path) -> None:
        from tv.rendering import process_queue

        queue_dir = tmp_path / "queue"
        queue_dir.mkdir()
        # One bad, one good
        (queue_dir / "bad_corrupt.json").write_text("{{invalid", encoding="utf-8")
        _write_match(queue_dir, _ks_match(), "kill_switch_ccc33333.json")
        output_dir = tmp_path / "output"

        results = process_queue(str(queue_dir), str(output_dir))
        successes = [r for r in results if r["ok"]]
        failures = [r for r in results if not r["ok"]]
        assert len(successes) == 1
        assert len(failures) == 1

    def test_corrupt_error_logged(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        from tv.rendering import process_queue

        queue_dir = tmp_path / "queue"
        queue_dir.mkdir()
        (queue_dir / "bad.json").write_text("not json", encoding="utf-8")
        output_dir = tmp_path / "output"

        with caplog.at_level(logging.ERROR):
            process_queue(str(queue_dir), str(output_dir))
        assert any("bad.json" in r.message for r in caplog.records)

    def test_empty_queue_returns_empty(self, tmp_path: Path) -> None:
        from tv.rendering import process_queue

        queue_dir = tmp_path / "queue"
        queue_dir.mkdir()
        results = process_queue(str(queue_dir), str(tmp_path / "output"))
        assert results == []


# -- Cycle 5: Processing time logging ------------------------------------------


class TestProcessingTimeLogged:
    """Processing time is logged per match."""

    def test_timing_logged(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        from tv.rendering import process_match

        match_path = _write_match(tmp_path / "queue", _ks_match(), "kill_switch_ttt44444.json")
        output_dir = tmp_path / "output"
        with caplog.at_level(logging.INFO):
            process_match(str(match_path), str(output_dir))
        assert any("processed" in r.message.lower() or "time" in r.message.lower()
                    for r in caplog.records)


# -- Cycle 6: Output size constraint -------------------------------------------


class TestOutputSize:
    """Output MP4 should be under 25MB for Discord free upload."""

    def test_mp4_under_25mb(self, tmp_path: Path) -> None:
        from tv.rendering import process_match

        match_path = _write_match(tmp_path / "queue", _ks_match(), "kill_switch_sz555555.json")
        output_dir = tmp_path / "output"
        mp4_path, _ = process_match(str(match_path), str(output_dir))
        size_mb = Path(mp4_path).stat().st_size / (1024 * 1024)
        assert size_mb < 25
