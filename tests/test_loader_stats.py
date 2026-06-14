"""Tests for stat allocation loading from bot files."""

from __future__ import annotations

from typing import Any

from engine.stats import DEFAULT_ALLOCATION, StatAllocation


def _write_bot_file(path, *, power=None, speed=None, armor=None, mind=None, extra=""):
    """Helper: write a minimal bot file with optional stat constants."""
    lines = [
        'BOT_NAME = "TestBot"',
        'BOT_EMOJI = "T"',
        'BOT_BIO = "test"',
        'BOT_AUTHOR = "tester"',
    ]
    if power is not None:
        lines.append(f"BOT_POWER = {power}")
    if speed is not None:
        lines.append(f"BOT_SPEED = {speed}")
    if armor is not None:
        lines.append(f"BOT_ARMOR = {armor}")
    if mind is not None:
        lines.append(f"BOT_MIND = {mind}")
    if extra:
        lines.append(extra)
    lines.append("")
    lines.append("def decide(state):")
    lines.append('    return ("rest",)')
    lines.append("")
    path.write_text("\n".join(lines))


# --- Loader tests ---


def test_loader_reads_stat_constants(tmp_path):
    """Bot file with valid stat constants produces correct stat_allocation."""
    _write_bot_file(tmp_path / "bot_a.py", power=40, speed=20, armor=25, mind=15)

    from engine.loader import load_bots

    configs = load_bots(str(tmp_path))
    assert len(configs) == 1
    alloc = configs[0]["stat_allocation"]
    assert isinstance(alloc, StatAllocation)
    assert alloc.power == 40
    assert alloc.speed == 20
    assert alloc.armor == 25
    assert alloc.mind == 15


def test_loader_default_stats_when_missing(tmp_path):
    """Bot file without stat constants gets DEFAULT_ALLOCATION."""
    _write_bot_file(tmp_path / "bot_b.py")

    from engine.loader import load_bots

    configs = load_bots(str(tmp_path))
    assert len(configs) == 1
    assert configs[0]["stat_allocation"] == DEFAULT_ALLOCATION


def test_loader_invalid_stats_falls_back(tmp_path):
    """Bot file with stats summing to 110 falls back to DEFAULT_ALLOCATION."""
    _write_bot_file(tmp_path / "bot_c.py", power=40, speed=30, armor=25, mind=15)

    from engine.loader import load_bots

    configs = load_bots(str(tmp_path))
    assert len(configs) == 1
    assert configs[0]["stat_allocation"] == DEFAULT_ALLOCATION


def test_loader_partial_stats_uses_defaults(tmp_path):
    """Bot file with only some stat constants fills missing with 25."""
    _write_bot_file(tmp_path / "bot_d.py", power=40)

    from engine.loader import load_bots

    configs = load_bots(str(tmp_path))
    assert len(configs) == 1
    # power=40, speed=25, armor=25, mind=25 = 115 -> invalid -> DEFAULT
    assert configs[0]["stat_allocation"] == DEFAULT_ALLOCATION


# --- _create_bots passes stat_allocation to Bot ---


def test_create_bots_passes_stats():
    """_create_bots passes stat_allocation through to Bot object."""
    from engine.game import _create_bots
    from engine.stats import StatAllocation, calculate_derived

    alloc = StatAllocation(power=40, speed=20, armor=25, mind=15)
    config: dict[str, Any] = {
        "name": "TestBot",
        "emoji": "T",
        "bio": "test",
        "author": "tester",
        "decide_func": lambda state: ("rest",),
        "stat_allocation": alloc,
    }
    bots = _create_bots([config], [(0, 0)])
    assert len(bots) == 1
    assert bots[0].stats == alloc
    derived = calculate_derived(alloc)
    assert bots[0].hp == derived.max_hp
    assert bots[0].energy == derived.max_energy


def test_create_bots_default_stats_when_missing():
    """_create_bots without stat_allocation uses defaults."""
    from engine.game import _create_bots

    config: dict[str, Any] = {
        "name": "TestBot",
        "emoji": "T",
        "bio": "test",
        "author": "tester",
        "decide_func": lambda state: ("rest",),
    }
    bots = _create_bots([config], [(0, 0)])
    assert len(bots) == 1
    assert bots[0].stats == DEFAULT_ALLOCATION
    # Default: hp=102 (with versatility bonus), energy=100
    assert bots[0].hp == 102
    assert bots[0].energy == 100
