"""End-to-end tests for the npcwars CLI pipeline (T14.10)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)


def _run(*args: str, cwd: str = _PROJECT_ROOT, **kwargs: object) -> subprocess.CompletedProcess[str]:
    """Helper to run npcwars CLI commands."""
    return subprocess.run(
        [sys.executable, "-m", "npcwars.cli", *args],
        capture_output=True, text=True, cwd=cwd, **kwargs,
    )


class TestInitCreatesValidStructure:
    """npcwars init creates expected structure via subprocess."""

    def test_init_creates_bots_dir(self, tmp_path: Path) -> None:
        result = _run("init", "--dir", str(tmp_path))
        assert result.returncode == 0
        assert (tmp_path / "bots").is_dir()

    def test_init_creates_replays_dir(self, tmp_path: Path) -> None:
        _run("init", "--dir", str(tmp_path))
        assert (tmp_path / "replays").is_dir()

    def test_init_creates_config(self, tmp_path: Path) -> None:
        _run("init", "--dir", str(tmp_path))
        assert (tmp_path / "npcwars.toml").is_file()

    def test_init_copies_bot_files(self, tmp_path: Path) -> None:
        _run("init", "--dir", str(tmp_path))
        bot_files = list((tmp_path / "bots").glob("*.py"))
        assert len(bot_files) >= 2


class TestValidateRejectsBadBot:
    """npcwars validate rejects an invalid bot file."""

    def test_bad_syntax_fails(self, tmp_path: Path) -> None:
        bad_bot = tmp_path / "bad_bot.py"
        bad_bot.write_text("def decide(state)\n    return 42\n", encoding="utf-8")
        result = _run("validate", str(bad_bot))
        assert result.returncode != 0

    def test_missing_decide_fails(self, tmp_path: Path) -> None:
        bad_bot = tmp_path / "no_decide.py"
        bad_bot.write_text(
            'BOT_NAME = "Bad"\nBOT_EMOJI = "X"\n\ndef nope():\n    pass\n',
            encoding="utf-8",
        )
        result = _run("validate", str(bad_bot))
        assert result.returncode != 0


class TestWizardBotPassesValidate:
    """A bot created by wizard passes validate."""

    def test_wizard_creates_bot_file(self, tmp_path: Path) -> None:
        bots_dir = tmp_path / "bots"
        bots_dir.mkdir()
        result = _run(
            "wizard", "--non-interactive",
            "--name", "WizBot", "--emoji", "W", "--style", "aggro",
            "--output-dir", str(bots_dir),
        )
        assert result.returncode == 0
        assert (bots_dir / "wizbot.py").is_file()

    def test_wizard_bot_validates_clean(self, tmp_path: Path) -> None:
        bots_dir = tmp_path / "bots"
        bots_dir.mkdir()
        _run(
            "wizard", "--non-interactive",
            "--name", "WizBot", "--emoji", "W", "--style", "aggro",
            "--output-dir", str(bots_dir),
        )
        result = _run("validate", str(bots_dir / "wizbot.py"))
        assert result.returncode == 0
        assert "PASS" in result.stdout


class TestPipelineWithCustomBot:
    """Init, then add a custom bot, validate, and battle."""

    _CUSTOM_BOT = '''\
BOT_NAME = "CustomBot"
BOT_EMOJI = "C"
BOT_BIO = "A hand-written custom bot."
BOT_AUTHOR = "test"

def decide(state):
    return ("rest",)
'''

    def test_custom_bot_validates(self, tmp_path: Path) -> None:
        _run("init", "--dir", str(tmp_path))
        custom = tmp_path / "bots" / "custom.py"
        custom.write_text(self._CUSTOM_BOT, encoding="utf-8")
        result = _run("validate", str(custom))
        assert result.returncode == 0

    def test_custom_bot_battles(self, tmp_path: Path) -> None:
        _run("init", "--dir", str(tmp_path))
        custom = tmp_path / "bots" / "custom.py"
        custom.write_text(self._CUSTOM_BOT, encoding="utf-8")
        result = _run(
            "battle", "--bots-dir", str(tmp_path / "bots"),
            "--seed", "42",
        )
        assert result.returncode == 0
        assert "Winner:" in result.stdout


class TestFullPipelineInitToBattle:
    """The big one: init -> wizard -> validate -> battle."""

    def test_full_pipeline(self, tmp_path: Path) -> None:
        # Step 1: init
        r_init = _run("init", "--dir", str(tmp_path))
        assert r_init.returncode == 0
        assert (tmp_path / "bots").is_dir()
        assert (tmp_path / "npcwars.toml").is_file()
        bot_files = list((tmp_path / "bots").glob("*.py"))
        assert len(bot_files) >= 2

        # Step 2: wizard creates a new bot
        r_wizard = _run(
            "wizard", "--non-interactive",
            "--name", "PipeBot", "--emoji", "P", "--style", "aggro",
            "--output-dir", str(tmp_path / "bots"),
        )
        assert r_wizard.returncode == 0
        pipebot = tmp_path / "bots" / "pipebot.py"
        assert pipebot.is_file()

        # Step 3: validate the wizard bot
        r_validate = _run("validate", str(pipebot))
        assert r_validate.returncode == 0
        assert "PASS" in r_validate.stdout

        # Step 4: battle with all bots
        replay_dir = tmp_path / "replays"
        r_battle = _run(
            "battle", "--bots-dir", str(tmp_path / "bots"),
            "--seed", "42", "--replay", str(replay_dir),
        )
        assert r_battle.returncode == 0
        assert "Winner:" in r_battle.stdout

        # Step 5: verify replay
        replay_files = list(replay_dir.glob("*.json"))
        assert len(replay_files) >= 1
        data = json.loads(replay_files[0].read_text(encoding="utf-8"))
        assert "winner" in data


class TestBattleWithSeedDeterministic:
    """Same seed produces same winner when run twice."""

    def test_same_seed_same_winner(self, tmp_path: Path) -> None:
        _run("init", "--dir", str(tmp_path))
        bots_dir = str(tmp_path / "bots")

        r1 = _run("battle", "--bots-dir", bots_dir, "--seed", "77")
        r2 = _run("battle", "--bots-dir", bots_dir, "--seed", "77")

        assert r1.returncode == 0
        assert r2.returncode == 0

        winner1 = [ln for ln in r1.stdout.splitlines() if "Winner:" in ln][0]
        winner2 = [ln for ln in r2.stdout.splitlines() if "Winner:" in ln][0]
        assert winner1 == winner2


class TestBattleReplayHasExpectedKeys:
    """Replay JSON contains required keys."""

    def test_replay_keys(self, tmp_path: Path) -> None:
        _run("init", "--dir", str(tmp_path))
        replay_dir = tmp_path / "replays"
        result = _run(
            "battle", "--bots-dir", str(tmp_path / "bots"),
            "--seed", "42", "--replay", str(replay_dir),
        )
        assert result.returncode == 0

        replay_files = list(replay_dir.glob("*.json"))
        assert len(replay_files) >= 1
        data = json.loads(replay_files[0].read_text(encoding="utf-8"))

        assert "winner" in data
        assert "duration_rounds" in data
        assert "players" in data
        assert "eliminations" in data
        assert isinstance(data["players"], list)
        assert isinstance(data["eliminations"], list)
        assert isinstance(data["duration_rounds"], int)
