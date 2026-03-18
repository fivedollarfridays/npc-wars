"""Tests for npcwars init command (T14.4)."""
from __future__ import annotations

import tomllib

import pytest

from agentgrounds.wars.builtin_bots import list_builtin_bots


def _run_main(argv: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[str, int]:
    """Run main() and return (stdout, exit_code)."""
    from agentgrounds.wars.cli import main

    try:
        main(argv)
        return capsys.readouterr().out, 0
    except SystemExit as exc:
        return capsys.readouterr().out, exc.code


class TestInitCreatesStructure:
    """Init creates expected directories and files."""

    def test_creates_bots_dir(self, tmp_path: object) -> None:
        from agentgrounds.wars.cli.cmd_init import run
        import argparse

        args = argparse.Namespace(dir=str(tmp_path), force=False)
        run(args)
        assert (tmp_path / "bots").is_dir()

    def test_creates_replays_dir(self, tmp_path: object) -> None:
        from agentgrounds.wars.cli.cmd_init import run
        import argparse

        args = argparse.Namespace(dir=str(tmp_path), force=False)
        run(args)
        assert (tmp_path / "replays").is_dir()

    def test_creates_config_file(self, tmp_path: object) -> None:
        from agentgrounds.wars.cli.cmd_init import run
        import argparse

        args = argparse.Namespace(dir=str(tmp_path), force=False)
        run(args)
        assert (tmp_path / "agentgrounds.toml").is_file()

    def test_config_is_valid_toml(self, tmp_path: object) -> None:
        from agentgrounds.wars.cli.cmd_init import run
        import argparse

        args = argparse.Namespace(dir=str(tmp_path), force=False)
        run(args)
        with open(tmp_path / "agentgrounds.toml", "rb") as f:
            data = tomllib.load(f)
        assert isinstance(data, dict)


class TestInitCopiesBots:
    """Init copies built-in bots to bots/ directory."""

    def test_template_bot_exists(self, tmp_path: object) -> None:
        from agentgrounds.wars.cli.cmd_init import run
        import argparse

        args = argparse.Namespace(dir=str(tmp_path), force=False)
        run(args)
        assert (tmp_path / "bots" / "template.py").is_file()

    def test_all_builtin_bots_copied(self, tmp_path: object) -> None:
        from agentgrounds.wars.cli.cmd_init import run
        import argparse

        args = argparse.Namespace(dir=str(tmp_path), force=False)
        run(args)
        for name in list_builtin_bots():
            assert (tmp_path / "bots" / f"{name}.py").is_file(), f"Missing {name}.py"

    def test_builtin_bots_count(self) -> None:
        assert len(list_builtin_bots()) == 7

    def test_bot_files_contain_bot_name(self, tmp_path: object) -> None:
        from agentgrounds.wars.cli.cmd_init import run
        import argparse

        args = argparse.Namespace(dir=str(tmp_path), force=False)
        run(args)
        for name in list_builtin_bots():
            content = (tmp_path / "bots" / f"{name}.py").read_text()
            assert "BOT_NAME" in content, f"{name}.py missing BOT_NAME"

    def test_bot_files_contain_decide(self, tmp_path: object) -> None:
        from agentgrounds.wars.cli.cmd_init import run
        import argparse

        args = argparse.Namespace(dir=str(tmp_path), force=False)
        run(args)
        for name in list_builtin_bots():
            content = (tmp_path / "bots" / f"{name}.py").read_text()
            assert "def decide" in content, f"{name}.py missing def decide"


class TestInitIdempotency:
    """Running init twice behaves correctly."""

    def test_second_init_skips_without_force(self, tmp_path: object, capsys: pytest.CaptureFixture[str]) -> None:
        from agentgrounds.wars.cli.cmd_init import run
        import argparse

        args = argparse.Namespace(dir=str(tmp_path), force=False)
        run(args)
        # Modify a bot file to verify it's not overwritten
        marker = tmp_path / "bots" / "template.py"
        marker.write_text("# custom content")

        with pytest.raises(SystemExit) as exc_info:
            run(args)
        assert exc_info.value.code == 0
        out = capsys.readouterr().out
        assert "already initialized" in out
        # File should NOT be overwritten
        assert marker.read_text() == "# custom content"

    def test_force_overwrites_existing(self, tmp_path: object) -> None:
        from agentgrounds.wars.cli.cmd_init import run
        import argparse

        args_no_force = argparse.Namespace(dir=str(tmp_path), force=False)
        run(args_no_force)
        marker = tmp_path / "bots" / "template.py"
        marker.write_text("# custom content")

        args_force = argparse.Namespace(dir=str(tmp_path), force=True)
        run(args_force)
        assert marker.read_text() != "# custom content"


class TestInitDirFlag:
    """--dir flag and default directory."""

    def test_dir_flag_via_dispatcher(self, tmp_path: object, capsys: pytest.CaptureFixture[str]) -> None:
        out, code = _run_main(["init", "--dir", str(tmp_path)], capsys)
        assert code == 0
        assert (tmp_path / "bots").is_dir()
        assert (tmp_path / "replays").is_dir()
        assert (tmp_path / "agentgrounds.toml").is_file()

    def test_default_target_is_cwd(
        self, tmp_path: object, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(tmp_path)
        out, code = _run_main(["init"], capsys)
        assert code == 0
        assert (tmp_path / "bots").is_dir()

    def test_force_flag_via_dispatcher(self, tmp_path: object, capsys: pytest.CaptureFixture[str]) -> None:
        _run_main(["init", "--dir", str(tmp_path)], capsys)
        # Write marker
        (tmp_path / "bots" / "template.py").write_text("# marker")
        out, code = _run_main(["init", "--dir", str(tmp_path), "--force"], capsys)
        assert code == 0
        assert (tmp_path / "bots" / "template.py").read_text() != "# marker"
