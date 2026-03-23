"""Tests for engine.character — character descriptor engine."""

from __future__ import annotations

import pathlib

import pytest

from engine.stats import StatAllocation
from engine.character import build_character_descriptor


# ── Archetype → shape + color mappings ────────────────────────────


def test_bruiser_hexagon_red() -> None:
    stats = StatAllocation(power=50, speed=20, armor=15, mind=15)
    desc = build_character_descriptor(stats=stats)
    assert desc["shape"] == "hexagon"
    assert desc["color"] == "#ff4444"
    assert desc["archetype"] == "Bruiser"


def test_tank_square_blue() -> None:
    stats = StatAllocation(power=10, speed=10, armor=70, mind=10)
    desc = build_character_descriptor(stats=stats)
    assert desc["shape"] == "square"
    assert desc["color"] == "#4488ff"
    assert desc["archetype"] == "Tank"


def test_balanced_circle_white() -> None:
    stats = StatAllocation(power=25, speed=25, armor=25, mind=25)
    desc = build_character_descriptor(stats=stats)
    assert desc["shape"] == "circle"
    assert desc["color"] == "#e0e0f0"
    assert desc["archetype"] == "Balanced"


def test_assassin_triangle_purple() -> None:
    stats = StatAllocation(power=10, speed=60, armor=15, mind=15)
    desc = build_character_descriptor(stats=stats)
    assert desc["shape"] == "triangle"
    assert desc["color"] == "#aa44ff"


def test_controller_diamond_green() -> None:
    stats = StatAllocation(power=10, speed=10, armor=10, mind=70)
    desc = build_character_descriptor(stats=stats)
    assert desc["shape"] == "diamond"
    assert desc["color"] == "#44ff88"


# ── Weapon indicator ──────────────────────────────────────────────


def test_dagger_dot_indicator() -> None:
    desc = build_character_descriptor(equipment={"weapon": "dagger"})
    assert desc["weapon_indicator"] == "dot"


def test_spear_long_line_indicator() -> None:
    desc = build_character_descriptor(equipment={"weapon": "spear"})
    assert desc["weapon_indicator"] == "long_line"


def test_bow_arc_indicator() -> None:
    desc = build_character_descriptor(equipment={"weapon": "bow"})
    assert desc["weapon_indicator"] == "arc"


# ── Armor border ─────────────────────────────────────────────────


def test_plate_armor_border_3() -> None:
    desc = build_character_descriptor(equipment={"armor": "plate"})
    assert desc["border_thickness"] == 3


def test_leather_armor_border_1() -> None:
    desc = build_character_descriptor(equipment={"armor": "leather"})
    assert desc["border_thickness"] == 1


def test_chain_mail_border_2() -> None:
    desc = build_character_descriptor(equipment={"armor": "chain_mail"})
    assert desc["border_thickness"] == 2


# ── Defaults ─────────────────────────────────────────────────────


def test_default_stats_circle_white_border1() -> None:
    desc = build_character_descriptor()
    assert desc["shape"] == "circle"
    assert desc["color"] == "#e0e0f0"
    assert desc["border_thickness"] == 1
    assert desc["weapon_indicator"] == "line"  # sword default


# ── Size scaling ─────────────────────────────────────────────────


def test_size_scales_with_armor_stat() -> None:
    low_armor = StatAllocation(power=40, speed=30, armor=10, mind=20)
    high_armor = StatAllocation(power=10, speed=10, armor=70, mind=10)
    desc_low = build_character_descriptor(stats=low_armor)
    desc_high = build_character_descriptor(stats=high_armor)
    assert desc_high["size_scale"] > desc_low["size_scale"]


def test_size_at_default_armor_25() -> None:
    desc = build_character_descriptor()
    assert desc["size_scale"] == 14.0  # 14 + (25-25)*0.15


# ── Explicit archetype override ──────────────────────────────────


def test_archetype_override() -> None:
    desc = build_character_descriptor(archetype="Tank")
    assert desc["shape"] == "square"
    assert desc["archetype"] == "Tank"


# ── Integration: character in match JSON ─────────────────────────


@pytest.fixture(scope="module")
def match_data() -> dict:
    """Run one match and return match data."""
    from engine.game import run_match
    from engine.loader import load_bots

    bots_dir = str(
        pathlib.Path(__file__).parent.parent
        / "agentgrounds" / "wars" / "builtin_bots"
    )
    bot_configs = load_bots(bots_dir)
    return run_match(bot_configs, match_id=900, seed=42)


def test_character_descriptor_in_match_players(match_data: dict) -> None:
    """Every player in match JSON has a character descriptor."""
    for player in match_data["players"]:
        assert "character" in player, f"Missing character for {player['name']}"
        char = player["character"]
        assert "shape" in char
        assert "color" in char
        assert "archetype" in char
        assert "weapon_indicator" in char
        assert "border_thickness" in char
        assert "size_scale" in char
