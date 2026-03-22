"""Tests for archetype classification from stat allocations."""

from engine.archetype import classify_archetype
from engine.stats import StatAllocation, validate_allocation
from tests.conftest import always_rest, bot_config


def test_high_power_is_bruiser() -> None:
    """Power > 35 classifies as Bruiser."""
    stats = StatAllocation(power=40, speed=20, armor=20, mind=20)
    assert classify_archetype(stats) == "Bruiser"


def test_high_speed_is_assassin() -> None:
    """Speed > 35 classifies as Assassin."""
    stats = StatAllocation(power=15, speed=40, armor=25, mind=20)
    assert classify_archetype(stats) == "Assassin"


def test_high_armor_is_tank() -> None:
    """Armor > 35 classifies as Tank."""
    stats = StatAllocation(power=20, speed=15, armor=45, mind=20)
    assert classify_archetype(stats) == "Tank"


def test_high_mind_is_controller() -> None:
    """Mind > 35 classifies as Controller."""
    stats = StatAllocation(power=20, speed=20, armor=20, mind=40)
    assert classify_archetype(stats) == "Controller"


def test_balanced_stats() -> None:
    """All stats 20-30 classifies as Balanced."""
    stats = StatAllocation(power=25, speed=25, armor=25, mind=25)
    assert classify_archetype(stats) == "Balanced"


def test_balanced_at_boundary() -> None:
    """Stats at edges of 20-30 range still Balanced."""
    stats = StatAllocation(power=20, speed=30, armor=20, mind=30)
    assert classify_archetype(stats) == "Balanced"


def test_tie_uses_highest() -> None:
    """When no stat > 35 and not balanced, use highest stat."""
    # power=32, speed=31 — power wins
    stats = StatAllocation(power=32, speed=31, armor=20, mind=17)
    assert classify_archetype(stats) == "Bruiser"


def test_tie_speed_highest() -> None:
    """When speed is highest but not > 35, still maps to Assassin."""
    stats = StatAllocation(power=15, speed=33, armor=32, mind=20)
    assert classify_archetype(stats) == "Assassin"


def test_archetype_names_exported() -> None:
    """ARCHETYPE_NAMES mapping is available for display."""
    from engine.archetype import ARCHETYPE_NAMES
    assert "Bruiser" in ARCHETYPE_NAMES.values()
    assert "Tank" in ARCHETYPE_NAMES.values()
    assert "Assassin" in ARCHETYPE_NAMES.values()
    assert "Controller" in ARCHETYPE_NAMES.values()
    assert "Balanced" in ARCHETYPE_NAMES.values()


def test_archetype_in_match_stats() -> None:
    """Archetype field appears in match JSON stats for each bot."""
    from engine.game import run_match

    tank_alloc = validate_allocation(power=10, speed=10, armor=70, mind=10)
    configs = [
        {**bot_config("Tank", "\U0001f6e1\ufe0f", always_rest),
         "stat_allocation": tank_alloc},
        bot_config("Other", "\U0001f916", always_rest),
    ]
    data = run_match(configs, match_id=1, seed=42)

    # Every bot in stats should have an "archetype" field
    for emoji, bot_stats in data["stats"].items():
        assert "archetype" in bot_stats, f"{emoji} missing archetype"

    # Tank bot should be classified as Tank
    assert data["stats"]["\U0001f6e1\ufe0f"]["archetype"] == "Tank"
