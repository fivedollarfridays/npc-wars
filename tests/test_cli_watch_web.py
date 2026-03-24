"""Tests for the watch-web CLI command."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import patch

import pytest


# -- Registration -----------------------------------------------------------


class TestWatchWebRegistered:
    """watch-web subcommand is registered in the CLI."""

    def test_appears_in_help(self, capsys: pytest.CaptureFixture[str]) -> None:
        from agentgrounds.wars.cli import main

        with pytest.raises(SystemExit):
            main(["--help"])
        out = capsys.readouterr().out
        assert "watch-web" in out

    def test_register_adds_subparser(self) -> None:
        from agentgrounds.wars.cli.cmd_watch_web import register

        parser = argparse.ArgumentParser()
        subs = parser.add_subparsers()
        register(subs)
        args = parser.parse_args(["watch-web", "test.json"])
        assert args.match_file == "test.json"

    def test_port_defaults_to_8080(self) -> None:
        from agentgrounds.wars.cli.cmd_watch_web import register

        parser = argparse.ArgumentParser()
        subs = parser.add_subparsers()
        register(subs)
        args = parser.parse_args(["watch-web"])
        assert args.port == 8080


# -- _find_latest_match -----------------------------------------------------


class TestFindLatestMatch:
    """_find_latest_match finds the most recent match JSON."""

    def test_returns_none_when_no_results_dir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.chdir(tmp_path)
        from agentgrounds.wars.cli.cmd_watch_web import _find_latest_match

        assert _find_latest_match() is None

    def test_returns_none_when_empty_results(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        (tmp_path / "results").mkdir()
        monkeypatch.chdir(tmp_path)
        from agentgrounds.wars.cli.cmd_watch_web import _find_latest_match

        assert _find_latest_match() is None

    def test_returns_most_recent_match(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        results = tmp_path / "results"
        results.mkdir()
        (results / "match_001.json").write_text("{}")
        (results / "match_002.json").write_text("{}")
        monkeypatch.chdir(tmp_path)
        from agentgrounds.wars.cli.cmd_watch_web import _find_latest_match

        result = _find_latest_match()
        assert result is not None
        assert "match_002" in result


# -- _find_viewer_dir -------------------------------------------------------


class TestFindViewerDir:
    """_find_viewer_dir locates the viewer directory."""

    def test_returns_none_when_no_viewer(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.chdir(tmp_path)
        from agentgrounds.wars.cli import cmd_watch_web

        # Temporarily override __file__ so pkg-relative lookup misses
        orig = cmd_watch_web.__file__
        try:
            cmd_watch_web.__file__ = str(tmp_path / "fake" / "cmd_watch_web.py")
            result = cmd_watch_web._find_viewer_dir()
            assert result is None
        finally:
            cmd_watch_web.__file__ = orig

    def test_finds_cwd_viewer(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from agentgrounds.wars.cli import cmd_watch_web

        viewer = tmp_path / "viewer"
        viewer.mkdir()
        (viewer / "index.html").write_text("<html></html>")
        monkeypatch.chdir(tmp_path)

        orig = cmd_watch_web.__file__
        try:
            cmd_watch_web.__file__ = str(tmp_path / "fake" / "cmd_watch_web.py")
            result = cmd_watch_web._find_viewer_dir()
            assert result is not None
            assert (result / "index.html").exists()
        finally:
            cmd_watch_web.__file__ = orig


# -- run error paths --------------------------------------------------------


class TestWatchWebErrors:
    """Error paths in run()."""

    def test_no_match_file_exits(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.chdir(tmp_path)
        from agentgrounds.wars.cli.cmd_watch_web import run

        args = argparse.Namespace(match_file=None, port=8080)
        with pytest.raises(SystemExit):
            run(args)

    def test_missing_file_exits(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.chdir(tmp_path)
        from agentgrounds.wars.cli.cmd_watch_web import run

        args = argparse.Namespace(match_file="nonexistent.json", port=8080)
        with pytest.raises(SystemExit):
            run(args)

    def test_no_viewer_prints_manual_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        match = tmp_path / "match_001.json"
        match.write_text(json.dumps({"winner": "A"}))
        monkeypatch.chdir(tmp_path)
        from agentgrounds.wars.cli.cmd_watch_web import run

        args = argparse.Namespace(match_file=str(match), port=8080)
        with patch(
            "agentgrounds.wars.cli.cmd_watch_web._find_viewer_dir",
            return_value=None,
        ):
            run(args)
        out = capsys.readouterr()
        assert "manually" in out.out.lower() or "manually" in out.err.lower()
