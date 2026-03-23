"""Tests for agentgrounds wars upload CLI command."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture()
def valid_bot(tmp_path: Path) -> Path:
    """Create a minimal valid bot file."""
    bot = tmp_path / "my_bot.py"
    bot.write_text(
        'BOT_NAME = "TestBot"\n'
        'BOT_EMOJI = "T"\n'
        "def decide(state):\n"
        '    return {"action": "move", "dx": 1, "dy": 0}\n'
    )
    return bot


@pytest.fixture()
def invalid_bot(tmp_path: Path) -> Path:
    """Create a bot that imports a blocked module."""
    bot = tmp_path / "bad_bot.py"
    bot.write_text("import os\ndef decide(state): pass\n")
    return bot


class TestCLIIntegration:
    """Test upload is registered in the CLI."""

    def test_upload_registered_in_cli(self) -> None:
        from agentgrounds.wars.cli import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["upload", "my_bot.py"])
        assert args.bot_file == "my_bot.py"


class TestRegister:
    """Tests for register() subparser setup."""

    def test_register_adds_upload_subcommand(self) -> None:
        from agentgrounds.wars.cli.cmd_upload import register

        parser = argparse.ArgumentParser()
        subs = parser.add_subparsers()
        register(subs)
        args = parser.parse_args(["upload", "my_bot.py"])
        assert args.bot_file == "my_bot.py"

    def test_register_default_no_join_false(self) -> None:
        from agentgrounds.wars.cli.cmd_upload import register

        parser = argparse.ArgumentParser()
        subs = parser.add_subparsers()
        register(subs)
        args = parser.parse_args(["upload", "my_bot.py"])
        assert args.no_join is False

    def test_register_no_join_flag(self) -> None:
        from agentgrounds.wars.cli.cmd_upload import register

        parser = argparse.ArgumentParser()
        subs = parser.add_subparsers()
        register(subs)
        args = parser.parse_args(["upload", "my_bot.py", "--no-join"])
        assert args.no_join is True

    def test_register_server_flag(self) -> None:
        from agentgrounds.wars.cli.cmd_upload import register

        parser = argparse.ArgumentParser()
        subs = parser.add_subparsers()
        register(subs)
        args = parser.parse_args(["upload", "bot.py", "--server", "http://x:9000"])
        assert args.server == "http://x:9000"

    def test_register_api_key_flag(self) -> None:
        from agentgrounds.wars.cli.cmd_upload import register

        parser = argparse.ArgumentParser()
        subs = parser.add_subparsers()
        register(subs)
        args = parser.parse_args(["upload", "bot.py", "--api-key", "abc123"])
        assert args.api_key == "abc123"


class TestRunValidation:
    """Tests for run() local validation before upload."""

    def test_missing_bot_file_exits(self, tmp_path: Path) -> None:
        from agentgrounds.wars.cli.cmd_upload import run

        args = argparse.Namespace(
            bot_file=str(tmp_path / "nonexistent.py"),
            server=None, api_key=None, no_join=True,
        )
        with pytest.raises(SystemExit, match="1"):
            run(args)

    def test_invalid_bot_rejected_locally(self, invalid_bot: Path) -> None:
        from agentgrounds.wars.cli.cmd_upload import run

        args = argparse.Namespace(
            bot_file=str(invalid_bot),
            server=None, api_key=None, no_join=True,
        )
        with pytest.raises(SystemExit, match="1"):
            run(args)


class TestUpload:
    """Tests for successful upload flow (HTTP mocked)."""

    def _make_args(
        self, bot_file: str, *, no_join: bool = True,
        server: str | None = None, api_key: str | None = None,
    ) -> argparse.Namespace:
        return argparse.Namespace(
            bot_file=bot_file, server=server, api_key=api_key, no_join=no_join,
        )

    @patch("agentgrounds.wars.cli.cmd_upload._post_json")
    def test_upload_sends_source(
        self, mock_post: MagicMock, valid_bot: Path,
    ) -> None:
        from agentgrounds.wars.cli.cmd_upload import run

        mock_post.return_value = {"bot_id": "b1", "job_id": "j1"}
        args = self._make_args(str(valid_bot), server="http://test:8000")
        run(args)

        mock_post.assert_called_once()
        call_url, call_data, _ = mock_post.call_args[0]
        assert call_url == "http://test:8000/api/submit-bot"
        assert "def decide" in call_data["source"]

    @patch("agentgrounds.wars.cli.cmd_upload._post_json")
    def test_upload_passes_api_key(
        self, mock_post: MagicMock, valid_bot: Path,
    ) -> None:
        from agentgrounds.wars.cli.cmd_upload import run

        mock_post.return_value = {"bot_id": "b1"}
        args = self._make_args(
            str(valid_bot), server="http://test:8000", api_key="key123",
        )
        run(args)

        _, _, passed_key = mock_post.call_args[0]
        assert passed_key == "key123"

    @patch("agentgrounds.wars.cli.cmd_upload._post_json")
    def test_no_join_skips_lobby(
        self, mock_post: MagicMock, valid_bot: Path,
    ) -> None:
        from agentgrounds.wars.cli.cmd_upload import run

        mock_post.return_value = {"bot_id": "b1"}
        args = self._make_args(str(valid_bot), no_join=True)
        run(args)

        # Only one call (submit-bot), no lobby/join
        assert mock_post.call_count == 1

    @patch("agentgrounds.wars.cli.cmd_upload._post_json")
    def test_join_lobby_called_when_no_join_false(
        self, mock_post: MagicMock, valid_bot: Path,
    ) -> None:
        from agentgrounds.wars.cli.cmd_upload import run

        # First call: submit-bot, second call: lobby/join
        mock_post.side_effect = [
            {"bot_id": "b1"},
            {"message": "joined"},
        ]
        args = self._make_args(str(valid_bot), no_join=False, server="http://s:8000")

        # Patch _poll_for_match to avoid sleeping
        with patch("agentgrounds.wars.cli.cmd_upload._poll_for_match"):
            run(args)

        assert mock_post.call_count == 2
        second_url = mock_post.call_args_list[1][0][0]
        assert "lobby/join" in second_url


class TestConfig:
    """Tests for config save/load."""

    def test_save_and_load(self, tmp_path: Path) -> None:
        from agentgrounds.wars.cli import cmd_upload

        with (
            patch.object(cmd_upload, "_CONFIG_DIR", tmp_path),
            patch.object(cmd_upload, "_CONFIG_FILE", tmp_path / "config.json"),
        ):
            cmd_upload._save_config({"server": "http://x:8000", "api_key": "k1"})
            cfg = cmd_upload._load_config()
            assert cfg["server"] == "http://x:8000"
            assert cfg["api_key"] == "k1"

    def test_load_missing_returns_empty(self, tmp_path: Path) -> None:
        from agentgrounds.wars.cli import cmd_upload

        with patch.object(
            cmd_upload, "_CONFIG_FILE", tmp_path / "nope.json",
        ):
            assert cmd_upload._load_config() == {}

    @patch("agentgrounds.wars.cli.cmd_upload._post_json")
    def test_api_key_saved_on_new_player(
        self, mock_post: MagicMock, valid_bot: Path, tmp_path: Path,
    ) -> None:
        from agentgrounds.wars.cli import cmd_upload
        from agentgrounds.wars.cli.cmd_upload import run

        mock_post.return_value = {"bot_id": "b1", "api_key": "new-key-abc"}

        with (
            patch.object(cmd_upload, "_CONFIG_DIR", tmp_path),
            patch.object(cmd_upload, "_CONFIG_FILE", tmp_path / "config.json"),
        ):
            args = argparse.Namespace(
                bot_file=str(valid_bot), server="http://s:8000",
                api_key=None, no_join=True,
            )
            run(args)

            cfg = json.loads((tmp_path / "config.json").read_text())
            assert cfg["api_key"] == "new-key-abc"
            assert cfg["server"] == "http://s:8000"
