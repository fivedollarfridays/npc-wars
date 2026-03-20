"""Tests for diverse stat allocations on all bot files.

Verifies that bots/ and agentgrounds/wars/builtin_bots/ have correct
BOT_POWER, BOT_SPEED, BOT_ARMOR, BOT_MIND constants matching their
intended archetypes, and that BOT_GLYPH is present where required.
"""

from __future__ import annotations

import os

import pytest

from engine.bot_scanner import load_bot_module

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
BOTS_DIR = os.path.join(PROJECT_ROOT, "bots")
BUILTIN_DIR = os.path.join(PROJECT_ROOT, "agentgrounds", "wars", "builtin_bots")


def _load_bot(directory: str, filename: str):
    """Load a bot module from a directory."""
    path = os.path.join(directory, filename)
    return load_bot_module(path, f"bot_{filename.replace('.py', '')}")


# --- Expected allocations ---
# Format: (power, speed, armor, mind)
EXPECTED_STATS: dict[str, tuple[int, int, int, int]] = {
    "example_aggro.py": (40, 20, 15, 25),
    "example_tank.py": (15, 15, 50, 20),
    "example_kiter.py": (20, 45, 15, 20),
    "example_random.py": (25, 25, 25, 25),
    "starter.py": (25, 25, 25, 25),
}

EXPECTED_GLYPHS: dict[str, str] = {
    "example_aggro.py": "\u2694",   # sword
    "example_tank.py": "\u25a0",    # solid square
    "example_kiter.py": "\u27a4",   # arrow
    "example_random.py": "\u25cb",  # circle
    "starter.py": "\u25c6",        # solid diamond
}

# bots/ directory specific bots
BOTS_EXPECTED_STATS: dict[str, tuple[int, int, int, int]] = {
    "goose_loose.py": (15, 20, 20, 45),
    "reaper.py": (30, 25, 20, 25),
}

BOTS_EXPECTED_GLYPHS: dict[str, str] = {
    "goose_loose.py": "\u25c6",  # diamond
    "reaper.py": "\u2620",       # skull and crossbones
}


class TestBuiltinBotStats:
    """Verify builtin bots in agentgrounds/wars/builtin_bots/ have correct stats."""

    @pytest.mark.parametrize("filename,expected", list(EXPECTED_STATS.items()))
    def test_stat_values(self, filename: str, expected: tuple[int, int, int, int]):
        mod = _load_bot(BUILTIN_DIR, filename)
        power, speed, armor, mind = expected
        assert mod.BOT_POWER == power, f"{filename} BOT_POWER"
        assert mod.BOT_SPEED == speed, f"{filename} BOT_SPEED"
        assert mod.BOT_ARMOR == armor, f"{filename} BOT_ARMOR"
        assert mod.BOT_MIND == mind, f"{filename} BOT_MIND"

    @pytest.mark.parametrize("filename,expected", list(EXPECTED_STATS.items()))
    def test_stats_sum_to_100(self, filename: str, expected: tuple[int, int, int, int]):
        mod = _load_bot(BUILTIN_DIR, filename)
        total = mod.BOT_POWER + mod.BOT_SPEED + mod.BOT_ARMOR + mod.BOT_MIND
        assert total == 100, f"{filename} stats sum to {total}, expected 100"

    @pytest.mark.parametrize("filename,expected", list(EXPECTED_STATS.items()))
    def test_stats_in_range(self, filename: str, expected: tuple[int, int, int, int]):
        mod = _load_bot(BUILTIN_DIR, filename)
        for attr in ("BOT_POWER", "BOT_SPEED", "BOT_ARMOR", "BOT_MIND"):
            val = getattr(mod, attr)
            assert 5 <= val <= 80, f"{filename} {attr}={val} not in [5, 80]"


class TestBotsDirStats:
    """Verify bots in bots/ directory have correct stats."""

    @pytest.mark.parametrize("filename,expected", list(EXPECTED_STATS.items()))
    def test_shared_bot_stats(self, filename: str, expected: tuple[int, int, int, int]):
        """Bots that exist in both dirs should have matching stats."""
        mod = _load_bot(BOTS_DIR, filename)
        power, speed, armor, mind = expected
        assert mod.BOT_POWER == power, f"bots/{filename} BOT_POWER"
        assert mod.BOT_SPEED == speed, f"bots/{filename} BOT_SPEED"
        assert mod.BOT_ARMOR == armor, f"bots/{filename} BOT_ARMOR"
        assert mod.BOT_MIND == mind, f"bots/{filename} BOT_MIND"

    @pytest.mark.parametrize("filename,expected", list(BOTS_EXPECTED_STATS.items()))
    def test_unique_bot_stats(self, filename: str, expected: tuple[int, int, int, int]):
        """Bots only in bots/ dir should have correct stats."""
        mod = _load_bot(BOTS_DIR, filename)
        power, speed, armor, mind = expected
        assert mod.BOT_POWER == power, f"bots/{filename} BOT_POWER"
        assert mod.BOT_SPEED == speed, f"bots/{filename} BOT_SPEED"
        assert mod.BOT_ARMOR == armor, f"bots/{filename} BOT_ARMOR"
        assert mod.BOT_MIND == mind, f"bots/{filename} BOT_MIND"

    @pytest.mark.parametrize("filename,expected", list(BOTS_EXPECTED_STATS.items()))
    def test_unique_bot_stats_sum(self, filename: str, expected: tuple[int, int, int, int]):
        mod = _load_bot(BOTS_DIR, filename)
        total = mod.BOT_POWER + mod.BOT_SPEED + mod.BOT_ARMOR + mod.BOT_MIND
        assert total == 100, f"bots/{filename} stats sum to {total}"


class TestBotGlyphs:
    """Verify BOT_GLYPH is present on bots/ dir bots."""

    @pytest.mark.parametrize("filename,glyph", list(BOTS_EXPECTED_GLYPHS.items()))
    def test_bots_dir_glyphs(self, filename: str, glyph: str):
        mod = _load_bot(BOTS_DIR, filename)
        assert hasattr(mod, "BOT_GLYPH"), f"bots/{filename} missing BOT_GLYPH"
        assert mod.BOT_GLYPH == glyph

    def test_template_no_stats(self):
        """template.py should NOT have stat constants (bare template)."""
        mod = _load_bot(BOTS_DIR, "template.py")
        assert not hasattr(mod, "BOT_POWER"), "template should not have BOT_POWER"


class TestAllBotsLoad:
    """Verify all bots load without errors through the loader."""

    def test_bots_dir_loads(self):
        from engine.loader import load_bots
        configs = load_bots(BOTS_DIR)
        names = [c["name"] for c in configs]
        assert "AggroBot" in names
        assert "TankBot" in names
        assert "KiteBot" in names
        assert "ChaosBot" in names
        assert "GooseLoose" in names

    def test_builtin_dir_loads(self):
        from engine.loader import load_bots
        configs = load_bots(BUILTIN_DIR)
        names = [c["name"] for c in configs]
        assert "AggroBot" in names
        assert "TankBot" in names
