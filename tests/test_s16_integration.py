"""Sprint 16 integration gate tests.

Verify all diff-view modules are wired and functional end-to-end.
"""

import os
import re

import pytest

from data.stat_diff import inject_diff_data
from engine.game import run_match
from engine.loader import load_bots

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOTS_DIR = os.path.join(PROJECT_ROOT, "bots")
VIEWER_HTML = os.path.join(PROJECT_ROOT, "viewer", "match.html")


@pytest.fixture()
def viewer_html_content():
    """Read viewer/match.html once for HTML-based tests."""
    with open(VIEWER_HTML, encoding="utf-8") as f:
        return f.read()


# ---- 1. Module wiring: stat_diff exports ----


class TestStatDiffExports:
    """data/stat_diff.py exports compute_diff and inject_diff_data."""

    def test_stat_diff_has_all(self):
        import data.stat_diff as mod

        assert hasattr(mod, "__all__")

    def test_compute_diff_in_all(self):
        import data.stat_diff as mod

        assert "compute_diff" in mod.__all__

    def test_inject_diff_data_in_all(self):
        import data.stat_diff as mod

        assert "inject_diff_data" in mod.__all__


# ---- 2. Module wiring: lifetime_stats exports ----


class TestLifetimeStatsExports:
    """data/lifetime_stats.py exports get_lifetime_stats."""

    def test_lifetime_stats_has_all(self):
        import data.lifetime_stats as mod

        assert hasattr(mod, "__all__")

    def test_get_lifetime_stats_in_all(self):
        import data.lifetime_stats as mod

        assert "get_lifetime_stats" in mod.__all__


# ---- 3. play.py wiring ----


class TestPlayWiring:
    """play.py imports and calls inject_diff_data."""

    def test_play_imports_inject_diff_data(self):
        src = _read_source("play.py")
        assert "inject_diff_data" in src

    def test_play_calls_inject_diff_data(self):
        src = _read_source("play.py")
        # Must have both import and call (not just import)
        assert re.search(r"from\s+data\.stat_diff\s+import\s+inject_diff_data", src)
        assert re.search(r"inject_diff_data\(", src)


# ---- 4. cmd_battle.py wiring ----


class TestCmdBattleWiring:
    """npcwars/cli/cmd_battle.py imports and calls inject_diff_data."""

    def test_cmd_battle_imports_inject_diff_data(self):
        src = _read_source(os.path.join("npcwars", "cli", "cmd_battle.py"))
        assert re.search(r"from\s+data\.stat_diff\s+import\s+inject_diff_data", src)

    def test_cmd_battle_calls_inject_diff_data(self):
        src = _read_source(os.path.join("npcwars", "cli", "cmd_battle.py"))
        # Must have a call site (not just the import)
        lines_with_call = [
            ln for ln in src.splitlines()
            if "inject_diff_data(" in ln and "import" not in ln
        ]
        assert len(lines_with_call) >= 1


# ---- 5. Viewer has overlay function ----


class TestViewerOverlay:
    """viewer/match.html contains showDiffOverlay function."""

    def test_viewer_has_show_diff_overlay(self, viewer_html_content):
        assert "showDiffOverlay" in viewer_html_content

    def test_show_diff_overlay_is_function(self, viewer_html_content):
        assert re.search(r"function\s+showDiffOverlay\s*\(", viewer_html_content)


# ---- 6. Viewer has color coding CSS ----


class TestViewerColorCoding:
    """viewer/match.html has diff row CSS classes."""

    def test_diff_row_improved_css(self, viewer_html_content):
        assert ".diff-row-improved" in viewer_html_content

    def test_diff_row_regressed_css(self, viewer_html_content):
        assert ".diff-row-regressed" in viewer_html_content


# ---- 7. showWinner calls showDiffOverlay ----


class TestShowWinnerWiring:
    """showWinner triggers showDiffOverlay."""

    def test_show_winner_calls_show_diff_overlay(self, viewer_html_content):
        # Extract the showWinner function body
        match = re.search(
            r"function\s+showWinner\s*\([^)]*\)\s*\{(.*?)\n\}",
            viewer_html_content,
            re.DOTALL,
        )
        assert match, "showWinner function not found"
        body = match.group(1)
        assert "showDiffOverlay" in body


# ---- 8. No dead public functions ----


class TestNoDeadPublicFunctions:
    """Every __all__ export has a non-test caller."""

    def test_compute_diff_has_caller(self):
        """compute_diff is called from inject_diff_data in stat_diff.py."""
        src = _read_source(os.path.join("data", "stat_diff.py"))
        calls = [
            ln for ln in src.splitlines()
            if "compute_diff(" in ln and not ln.strip().startswith("def ")
        ]
        assert len(calls) >= 1, "compute_diff has no call site in stat_diff.py"

    def test_inject_diff_data_has_caller_in_play(self):
        """inject_diff_data is called from play.py."""
        src = _read_source("play.py")
        calls = [
            ln for ln in src.splitlines()
            if "inject_diff_data(" in ln and "import" not in ln
        ]
        assert len(calls) >= 1

    def test_inject_diff_data_has_caller_in_cmd_battle(self):
        """inject_diff_data is called from cmd_battle.py."""
        src = _read_source(os.path.join("npcwars", "cli", "cmd_battle.py"))
        calls = [
            ln for ln in src.splitlines()
            if "inject_diff_data(" in ln and "import" not in ln
        ]
        assert len(calls) >= 1

    def test_get_all_lifetime_stats_has_caller(self):
        """get_all_lifetime_stats is called from stat_diff.py (inside inject_diff_data)."""
        src = _read_source(os.path.join("data", "stat_diff.py"))
        calls = [
            ln for ln in src.splitlines()
            if "get_all_lifetime_stats(" in ln and "import" not in ln
        ]
        assert len(calls) >= 1


# ---- 9. E2E smoke test ----


class TestE2ESmoke:
    """Run a match with seed, inject diffs, verify output."""

    def test_smoke_match_with_diff(self, tmp_path):
        results_dir = str(tmp_path / "results")
        os.makedirs(results_dir)

        bot_configs = load_bots(BOTS_DIR)
        assert len(bot_configs) >= 2

        match_data = run_match(bot_configs, match_id=1, seed=12345)
        assert "stats" in match_data

        inject_diff_data(match_data, results_dir)

        assert "diff" in match_data, "inject_diff_data did not add 'diff' key"
        assert len(match_data["diff"]) > 0, "diff dict is empty"

        # All players in stats should have diff entries
        for emoji in match_data["stats"]:
            assert emoji in match_data["diff"], f"Player {emoji} missing from diff"


# ---- helpers ----


def _read_source(relpath: str) -> str:
    """Read a source file relative to project root."""
    fullpath = os.path.join(PROJECT_ROOT, relpath)
    with open(fullpath, encoding="utf-8") as f:
        return f.read()
