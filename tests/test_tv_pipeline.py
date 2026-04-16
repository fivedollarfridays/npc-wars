"""Tests for TV pipeline wiring into play command (T59.4)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest


# -- Fixtures ----------------------------------------------------------------

_BOT_A = """\
BOT_NAME = "AlphaBot"
BOT_EMOJI = "A"
BOT_BIO = "test alpha"
BOT_AUTHOR = "author_a"

def decide(state):
    return ("rest",)
"""

_BOT_B = """\
BOT_NAME = "BetaBot"
BOT_EMOJI = "B"
BOT_BIO = "test beta"
BOT_AUTHOR = "author_b"

def decide(state):
    return ("rest",)
"""


def _setup_bots(tmp_path: Path) -> Path:
    bots_dir = tmp_path / "bots"
    bots_dir.mkdir()
    (bots_dir / "alpha.py").write_text(_BOT_A, encoding="utf-8")
    (bots_dir / "beta.py").write_text(_BOT_B, encoding="utf-8")
    return bots_dir


def _run_main(
    argv: list[str], capsys: pytest.CaptureFixture[str],
) -> tuple[str, str, int]:
    from agentgrounds.wars.cli import main

    try:
        main(argv)
        captured = capsys.readouterr()
        return captured.out, captured.err, 0
    except SystemExit as exc:
        captured = capsys.readouterr()
        return captured.out, captured.err, exc.code


# -- Cycle 1: --no-tv flag registration -------------------------------------


class TestNoTvFlag:
    """--no-tv flag is registered and defaults to False."""

    def test_no_tv_appears_in_help(
        self, capsys: pytest.CaptureFixture[str],
    ) -> None:
        out, _err, code = _run_main(["play", "--help"], capsys)
        assert code == 0
        assert "--no-tv" in out

    def test_no_tv_defaults_false(self) -> None:
        from agentgrounds.wars.cli.cmd_play import register

        parser = argparse.ArgumentParser()
        subs = parser.add_subparsers()
        register(subs)
        args = parser.parse_args(["play", "--bots-dir", "bots", "--no-watch"])
        assert args.no_tv is False

    def test_no_tv_true_when_passed(self) -> None:
        from agentgrounds.wars.cli.cmd_play import register

        parser = argparse.ArgumentParser()
        subs = parser.add_subparsers()
        register(subs)
        args = parser.parse_args(["play", "--no-tv", "--no-watch"])
        assert args.no_tv is True


# -- Cycle 2: TV pipeline enrichment ----------------------------------------


class TestTvPipelineEnrich:
    """_enrich_tv appends TV keys to match_data."""

    def test_enrich_adds_commentary_key(self) -> None:
        from engine.tv_pipeline import enrich_tv

        md = _minimal_match_data()
        enrich_tv(md, results_dir="results", patterns_dir="data/rival_patterns")
        assert "commentary" in md

    def test_enrich_adds_highlights_key(self) -> None:
        from engine.tv_pipeline import enrich_tv

        md = _minimal_match_data()
        enrich_tv(md, results_dir="results", patterns_dir="data/rival_patterns")
        assert "highlights" in md

    def test_enrich_adds_profiles_key(self) -> None:
        from engine.tv_pipeline import enrich_tv

        md = _minimal_match_data()
        enrich_tv(md, results_dir="results", patterns_dir="data/rival_patterns")
        assert "profiles" in md

    def test_enrich_adds_rivalries_key(self) -> None:
        from engine.tv_pipeline import enrich_tv

        md = _minimal_match_data()
        enrich_tv(md, results_dir="results", patterns_dir="data/rival_patterns")
        assert "rivalries" in md

    def test_enrich_adds_watcher_dossier_key(self) -> None:
        from engine.tv_pipeline import enrich_tv

        md = _minimal_match_data()
        enrich_tv(md, results_dir="results", patterns_dir="data/rival_patterns")
        assert "watcher_dossier" in md

    def test_commentary_is_list(self) -> None:
        from engine.tv_pipeline import enrich_tv

        md = _minimal_match_data()
        enrich_tv(md, results_dir="results", patterns_dir="data/rival_patterns")
        assert isinstance(md["commentary"], list)

    def test_highlights_is_list(self) -> None:
        from engine.tv_pipeline import enrich_tv

        md = _minimal_match_data()
        enrich_tv(md, results_dir="results", patterns_dir="data/rival_patterns")
        assert isinstance(md["highlights"], list)

    def test_profiles_keyed_by_emoji(self) -> None:
        from engine.tv_pipeline import enrich_tv

        md = _minimal_match_data()
        enrich_tv(md, results_dir="results", patterns_dir="data/rival_patterns")
        assert isinstance(md["profiles"], dict)
        for emoji in ("A", "B"):
            assert emoji in md["profiles"]

    def test_rivalries_is_dict(self) -> None:
        from engine.tv_pipeline import enrich_tv

        md = _minimal_match_data()
        enrich_tv(md, results_dir="results", patterns_dir="data/rival_patterns")
        assert isinstance(md["rivalries"], dict)

    def test_existing_keys_untouched(self) -> None:
        from engine.tv_pipeline import enrich_tv

        md = _minimal_match_data()
        original_winner = md["winner"]
        enrich_tv(md, results_dir="results", patterns_dir="data/rival_patterns")
        assert md["winner"] == original_winner

    def test_commentary_entries_serialisable(self) -> None:
        """Commentary must be JSON-serialisable (dicts, not dataclasses)."""
        from engine.tv_pipeline import enrich_tv

        md = _minimal_match_data()
        enrich_tv(md, results_dir="results", patterns_dir="data/rival_patterns")
        # Should not raise
        json.dumps(md["commentary"])


# -- Cycle 3: --no-tv skips TV in play command -------------------------------


class TestNoTvSkipsPipeline:
    """--no-tv flag prevents TV enrichment."""

    def test_no_tv_flag_skips_tv_keys(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        bots_dir = _setup_bots(tmp_path)
        monkeypatch.chdir(tmp_path)
        _run_main(
            ["play", "--bots-dir", str(bots_dir), "--no-watch", "--no-tv",
             "--seed", "42"],
            capsys,
        )
        results_dir = tmp_path / "results"
        json_files = sorted(results_dir.glob("*.json"))
        assert len(json_files) >= 1
        data = json.loads(json_files[-1].read_text())
        assert "commentary" not in data

    def test_tv_enabled_by_default_produces_keys(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        bots_dir = _setup_bots(tmp_path)
        monkeypatch.chdir(tmp_path)
        _run_main(
            ["play", "--bots-dir", str(bots_dir), "--no-watch", "--seed", "42"],
            capsys,
        )
        results_dir = tmp_path / "results"
        json_files = sorted(results_dir.glob("*.json"))
        assert len(json_files) >= 1
        data = json.loads(json_files[-1].read_text())
        assert "commentary" in data
        assert "highlights" in data
        assert "profiles" in data
        assert "rivalries" in data


# -- Helpers -----------------------------------------------------------------


def _pos(emoji: str, x: int, y: int, alive: bool = True, hp: int = 100) -> dict:
    return {"emoji": emoji, "x": x, "y": y, "alive": alive, "hp": hp, "energy": 5}


def _player(emoji: str, name: str, author: str) -> dict:
    return {"emoji": emoji, "name": name, "bio": name, "author": author, "glyph": emoji, "character": {}}


def _minimal_match_data() -> dict:
    """Return a minimal match_data dict for unit tests."""
    return {
        "match_id": 1, "date": "2026-01-01T00:00:00", "grid_size": 5,
        "players": [_player("A", "AlphaBot", "author_a"), _player("B", "BetaBot", "author_b")],
        "rounds": [
            {"round": 1, "storm_border": 0,
             "positions": [_pos("A", 1, 1), _pos("B", 3, 3)], "events": []},
            {"round": 2, "storm_border": 0,
             "positions": [_pos("A", 2, 2), _pos("B", 3, 3, alive=False, hp=0)],
             "events": [{"type": "hit", "attacker": "A", "target": "B", "damage": 100}]},
        ],
        "eliminations": [{"emoji": "B", "round": 2, "killed_by": "A", "cause": "damage"}],
        "winner": "A",
        "stats": {
            "A": {"kills": 1, "damage_dealt": 100, "damage_taken": 0, "rounds_survived": 2, "score": 100},
            "B": {"kills": 0, "damage_dealt": 0, "damage_taken": 100, "rounds_survived": 1, "score": 0},
        },
        "duration_rounds": 2,
    }
