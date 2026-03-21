"""Tests for equipment loading in bot loader and game bot creation."""

import logging
import types
from typing import Any
from unittest.mock import patch

import pytest

from engine.equipment import EQUIPMENT_DEFAULTS, EquipmentBonuses, compute_equipment_bonuses
from engine.loader import _load_single_bot


def _make_bot_module(
    name: str = "TestBot",
    emoji: str = "T",
    equipment: dict | None = None,
    *,
    include_equipment: bool = True,
) -> types.ModuleType:
    """Create a fake bot module for testing."""
    mod = types.ModuleType(f"bot_{name.lower()}")
    mod.BOT_NAME = name  # type: ignore[attr-defined]
    mod.BOT_EMOJI = emoji  # type: ignore[attr-defined]
    mod.decide = lambda state: ("rest",)  # type: ignore[attr-defined]
    if include_equipment and equipment is not None:
        mod.BOT_EQUIPMENT = equipment  # type: ignore[attr-defined]
    return mod


# ── Cycle 1: Bot with BOT_EQUIPMENT loads correctly ─────────────


def test_equipment_present_in_config() -> None:
    """Bot with BOT_EQUIPMENT gets it included in config dict."""
    equipment = {"weapon": "dagger", "armor": "leather", "accessories": [], "tactical": None}
    mod = _make_bot_module(equipment=equipment)
    with patch("engine.loader.load_bot_module", return_value=mod):
        config = _load_single_bot("/fake/path.py", "test.py")
    assert config is not None
    assert "equipment" in config
    assert config["equipment"]["weapon"] == "dagger"


# ── Cycle 2: Bot without BOT_EQUIPMENT gets defaults ────────────


def test_no_equipment_gets_defaults() -> None:
    """Bot without BOT_EQUIPMENT attribute gets EQUIPMENT_DEFAULTS."""
    mod = _make_bot_module(include_equipment=False)
    with patch("engine.loader.load_bot_module", return_value=mod):
        config = _load_single_bot("/fake/path.py", "test.py")
    assert config is not None
    assert config["equipment"] == EQUIPMENT_DEFAULTS


# ── Cycle 3: Invalid equipment falls back to defaults ────────────


def test_invalid_equipment_falls_back(caplog: pytest.LogCaptureFixture) -> None:
    """Invalid equipment (over budget) falls back to defaults with warning."""
    over_budget = {
        "weapon": "axe",
        "armor": "plate",
        "accessories": ["amulet_of_crit", "ring_of_haste"],
        "tactical": "teleport",
    }
    mod = _make_bot_module(equipment=over_budget)
    with patch("engine.loader.load_bot_module", return_value=mod):
        with caplog.at_level(logging.WARNING):
            config = _load_single_bot("/fake/path.py", "test.py")
    assert config is not None
    assert config["equipment"] == EQUIPMENT_DEFAULTS
    assert any("equipment" in r.message.lower() for r in caplog.records)


# ── Cycle 4: Equipment bonuses applied during bot creation ───────


def test_equipment_bonuses_applied_in_create_bots() -> None:
    """_create_bots applies equipment bonuses (HP increase from ring_of_health)."""
    from engine.game import _create_bots

    equipment = {
        "weapon": "sword",
        "armor": "leather",
        "accessories": ["ring_of_health"],
        "tactical": None,
    }
    config: dict[str, Any] = {
        "name": "Equipped",
        "emoji": "E",
        "bio": "test",
        "author": "test",
        "decide_func": lambda state: ("rest",),
        "equipment": equipment,
    }
    bots = _create_bots([config], [(5, 5)])
    bot = bots[0]
    # ring_of_health gives +10 max_hp
    bonuses = compute_equipment_bonuses(equipment)
    assert bonuses.max_hp == 10
    assert bot.hp > 100  # base HP (100 for default stats) + 10
    assert bot.equipment == equipment
    assert bot.equipment_bonuses is not None
    assert bot.equipment_bonuses.max_hp == 10


# ── Cycle 5: Default equipment produces valid bonuses ────────────


def test_default_equipment_bonuses() -> None:
    """Default equipment (sword + leather) produces valid EquipmentBonuses."""
    bonuses = compute_equipment_bonuses(EQUIPMENT_DEFAULTS)
    assert isinstance(bonuses, EquipmentBonuses)
    # sword: to_hit=1, min_dmg=3, max_dmg=5
    assert bonuses.to_hit == 1
    assert bonuses.min_damage == 3
    # leather: dr=2
    assert bonuses.dr == 2
    # No accessories -> no HP/energy bonus
    assert bonuses.max_hp == 0
    assert bonuses.max_energy == 0


def test_create_bots_default_equipment() -> None:
    """Bot without equipment key in config gets defaults applied."""
    from engine.game import _create_bots

    config: dict[str, Any] = {
        "name": "Plain",
        "emoji": "P",
        "bio": "test",
        "author": "test",
        "decide_func": lambda state: ("rest",),
        # no "equipment" key
    }
    bots = _create_bots([config], [(5, 5)])
    bot = bots[0]
    assert bot.equipment == EQUIPMENT_DEFAULTS
    assert bot.equipment_bonuses is not None
