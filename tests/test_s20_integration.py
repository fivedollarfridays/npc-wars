"""S20 integration tests — verify the complete experience layer.

Tests:
  1. CLI command registration (play, watch, generate)
  2. TerminalRenderer output quality
  3. PROMPT.md required sections
  4. Starter bot structure and validation
  5. npcwars play e2e subprocess
  6. npcwars watch subprocess with fixture
  7. npcwars generate subprocess
  8. README content verification
  9. No dead public functions
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ── 1. CLI command registration ────────────────────────────────

class TestCLIRegistration:
    """All S20 commands appear in npcwars --help."""

    def test_help_includes_play(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "agentgrounds.wars.cli", "--help"],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        )
        assert "play" in result.stdout

    def test_help_includes_watch(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "agentgrounds.wars.cli", "--help"],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        )
        assert "watch" in result.stdout

    def test_help_includes_generate(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "agentgrounds.wars.cli", "--help"],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        )
        assert "generate" in result.stdout


# ── 2. Renderer produces output ────────────────────────────────

class TestRendererOutput:
    """TerminalRenderer.render_frame() returns string with title, grid, HP."""

    @pytest.fixture()
    def renderer(self):
        from agentgrounds.wars.cli.renderer import TerminalRenderer

        players = [
            {"emoji": "\U0001f916", "name": "Alpha"},
            {"emoji": "\U0001f525", "name": "Bravo"},
        ]
        return TerminalRenderer(players, grid_size=5)

    @pytest.fixture()
    def round_data(self):
        return {
            "round": 1,
            "storm_border": 0,
            "positions": [
                {"emoji": "\U0001f916", "x": 2, "y": 2, "alive": True, "hp": 80, "energy": 60},
                {"emoji": "\U0001f525", "x": 4, "y": 4, "alive": True, "hp": 50, "energy": 40},
            ],
            "events": [],
        }

    def test_frame_contains_title(self, renderer, round_data) -> None:
        frame = renderer.render_frame(round_data, clear=False)
        assert "N P C   W A R S" in frame

    def test_frame_contains_grid_chars(self, renderer, round_data) -> None:
        frame = renderer.render_frame(round_data, clear=False)
        # Grid should contain the dot empty character
        assert "\u00b7" in frame

    def test_frame_contains_hp_info(self, renderer, round_data) -> None:
        frame = renderer.render_frame(round_data, clear=False)
        assert "hp" in frame

    def test_frame_contains_combatants(self, renderer, round_data) -> None:
        frame = renderer.render_frame(round_data, clear=False)
        assert "Combatants" in frame

    def test_frame_contains_kill_feed(self, renderer, round_data) -> None:
        frame = renderer.render_frame(round_data, clear=False)
        assert "Kill Feed" in frame


# ── 3. PROMPT.md required sections ─────────────────────────────

class TestPromptMD:
    """PROMPT.md covers required sections."""

    @pytest.fixture()
    def prompt_text(self) -> str:
        return (PROJECT_ROOT / "PROMPT.md").read_text(encoding="utf-8")

    def test_covers_state_dict(self, prompt_text) -> None:
        assert "State Dict" in prompt_text or "state" in prompt_text.lower()
        assert "state = {" in prompt_text

    def test_covers_actions(self, prompt_text) -> None:
        assert "Actions" in prompt_text
        assert '("move"' in prompt_text or "move" in prompt_text

    def test_covers_decide(self, prompt_text) -> None:
        assert "decide" in prompt_text
        assert "def decide(state)" in prompt_text

    def test_covers_strategies(self, prompt_text) -> None:
        assert "Strateg" in prompt_text

    def test_covers_examples(self, prompt_text) -> None:
        assert "Example" in prompt_text


# ── 4. Starter bot ─────────────────────────────────────────────

class TestStarterBot:
    """Starter bot passes validation, has TODOs, uses helpers DSL."""

    @pytest.fixture()
    def starter_source(self) -> str:
        return (PROJECT_ROOT / "agentgrounds" / "wars" / "builtin_bots" / "starter.py").read_text(
            encoding="utf-8"
        )

    def test_passes_validation(self) -> None:
        from scripts.validate_bot import validate_bot

        ok, errs = validate_bot(
            str(PROJECT_ROOT / "agentgrounds" / "wars" / "builtin_bots" / "starter.py")
        )
        assert ok, f"Starter bot validation failed: {errs}"

    def test_has_seven_or_more_todos(self, starter_source) -> None:
        todo_count = starter_source.count("TODO")
        assert todo_count >= 7, f"Only {todo_count} TODOs, need >= 7"

    def test_uses_helpers_dsl(self, starter_source) -> None:
        assert "from agentgrounds.wars.helpers import" in starter_source

    def test_exists_in_builtin_bots(self) -> None:
        path = PROJECT_ROOT / "agentgrounds" / "wars" / "builtin_bots" / "starter.py"
        assert path.is_file()

    def test_has_required_metadata(self, starter_source) -> None:
        assert "BOT_NAME" in starter_source
        assert "BOT_EMOJI" in starter_source


# ── 5. npcwars play e2e ────────────────────────────────────────

class TestPlayE2E:
    """npcwars play --no-watch --seed 42 exits 0, prints winner."""

    def test_play_exits_zero_with_winner(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "agentgrounds.wars.cli", "play",
             "--no-watch", "--no-tv", "--seed", "42"],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
            timeout=60,
        )
        assert result.returncode == 0, (
            f"play exited {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )
        assert "Winner" in result.stdout or "winner" in result.stdout.lower()


# ── 6. npcwars watch ───────────────────────────────────────────

class TestWatchE2E:
    """npcwars watch with fixture JSON + --speed 100 --no-clear exits 0."""

    @pytest.fixture()
    def fixture_json(self, tmp_path) -> Path:
        """Create a minimal match fixture for watch."""
        match_data = {
            "match_id": 999,
            "grid_size": 5,
            "players": [
                {"emoji": "\U0001f916", "name": "Alpha"},
                {"emoji": "\U0001f525", "name": "Bravo"},
            ],
            "rounds": [
                {
                    "round": 1,
                    "storm_border": 0,
                    "positions": [
                        {"emoji": "\U0001f916", "x": 1, "y": 1, "alive": True,
                         "hp": 100, "energy": 100},
                        {"emoji": "\U0001f525", "x": 3, "y": 3, "alive": True,
                         "hp": 100, "energy": 100},
                    ],
                    "events": [],
                },
            ],
            "winner": "\U0001f916",
            "duration_rounds": 1,
        }
        fp = tmp_path / "fixture_match.json"
        fp.write_text(json.dumps(match_data), encoding="utf-8")
        return fp

    def test_watch_exits_zero(self, fixture_json) -> None:
        result = subprocess.run(
            [
                sys.executable, "-m", "agentgrounds.wars.cli", "watch",
                str(fixture_json), "--speed", "100", "--no-clear",
            ],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
            timeout=30,
        )
        assert result.returncode == 0, (
            f"watch exited {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )


# ── 7. npcwars generate ───────────────────────────────────────

class TestGenerateE2E:
    """npcwars generate prints PROMPT.md content."""

    def test_generate_prints_prompt(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "agentgrounds.wars.cli", "generate"],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
            timeout=15,
        )
        assert result.returncode == 0, (
            f"generate exited {result.returncode}\nstderr: {result.stderr}"
        )
        assert "decide(state)" in result.stdout
        assert "Kill Switch" in result.stdout


# ── 8. README updated ─────────────────────────────────────────

class TestREADME:
    """README contains key S20 references."""

    @pytest.fixture()
    def readme_text(self) -> str:
        return (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    def test_mentions_agentgrounds_killswitch_play(self, readme_text) -> None:
        assert "agentgrounds killswitch play" in readme_text

    def test_mentions_agentgrounds_killswitch_generate(self, readme_text) -> None:
        assert "agentgrounds killswitch generate" in readme_text

    def test_mentions_prompt_md(self, readme_text) -> None:
        assert "PROMPT.md" in readme_text

    def test_mentions_starter(self, readme_text) -> None:
        assert "starter" in readme_text.lower()


# ── 9. No dead public functions ───────────────────────────────

class TestNoDeadCode:
    """TerminalRenderer, cmd_play, cmd_watch, cmd_generate all imported."""

    def test_terminal_renderer_importable(self) -> None:
        from agentgrounds.wars.cli.renderer import TerminalRenderer

        assert TerminalRenderer is not None

    def test_cmd_play_registered(self) -> None:
        from agentgrounds.wars.cli import cmd_play

        assert hasattr(cmd_play, "register")
        assert hasattr(cmd_play, "run")

    def test_cmd_watch_registered(self) -> None:
        from agentgrounds.wars.cli import cmd_watch

        assert hasattr(cmd_watch, "register")
        assert hasattr(cmd_watch, "run")

    def test_cmd_generate_registered(self) -> None:
        from agentgrounds.wars.cli import cmd_generate

        assert hasattr(cmd_generate, "register")
        assert hasattr(cmd_generate, "run")

    def test_all_commands_wired_in_init(self) -> None:
        """Verify __init__.py imports all S20 modules."""
        init_src = (PROJECT_ROOT / "agentgrounds" / "wars" / "cli" / "__init__.py").read_text(
            encoding="utf-8"
        )
        assert "cmd_play" in init_src
        assert "cmd_watch" in init_src
        assert "cmd_generate" in init_src
