"""Load bot modules from the bots/ directory."""

import logging
import os
from typing import Any

from engine.bot_scanner import load_bot_module
from engine.equipment import EQUIPMENT_DEFAULTS, validate_equipment
from engine.glyphs import validate_glyph
from engine.stats import DEFAULT_ALLOCATION, validate_allocation

log = logging.getLogger(__name__)


def _read_equipment(module: Any, filename: str) -> dict[str, Any]:
    """Read and validate BOT_EQUIPMENT from a module, falling back to defaults."""
    raw = getattr(module, "BOT_EQUIPMENT", None)
    if raw is not None:
        valid, msg = validate_equipment(raw)
        if valid:
            return dict(raw)
        log.warning("%s: invalid equipment (%s), using defaults", filename, msg)
    return dict(EQUIPMENT_DEFAULTS)


def _load_single_bot(filepath: str, filename: str) -> dict[str, Any] | None:
    """Load and validate a single bot module. Returns dict or None."""
    try:
        module = load_bot_module(filepath, f"bot_{filename[:-3]}")
    except ValueError as e:
        for msg in str(e).split("; "):
            log.warning("%s: %s", filename, msg)
        log.warning("Skipping %s — blocked by AST pre-scan", filename)
        return None
    except Exception as e:
        log.warning("Failed to load %s: %s", filename, e)
        return None

    name = getattr(module, "BOT_NAME", None)
    emoji = getattr(module, "BOT_EMOJI", None)
    decide = getattr(module, "decide", None)

    if not name or not emoji or not callable(decide):
        log.warning("Skipping %s — missing required attributes", filename)
        return None

    # Read stat allocation constants (default 25 each if absent)
    power = getattr(module, "BOT_POWER", 25)
    speed = getattr(module, "BOT_SPEED", 25)
    armor = getattr(module, "BOT_ARMOR", 25)
    mind = getattr(module, "BOT_MIND", 25)
    try:
        allocation = validate_allocation(power, speed, armor, mind)
    except ValueError as e:
        log.warning("%s: invalid stat allocation (%s), using defaults", filename, e)
        allocation = DEFAULT_ALLOCATION

    # Glyph: prefer BOT_GLYPH, fall back to BOT_EMOJI
    raw_glyph = getattr(module, "BOT_GLYPH", None) or emoji
    glyph = validate_glyph(raw_glyph)

    equipment = _read_equipment(module, filename)

    return {"name": name, "emoji": emoji, "bio": getattr(module, "BOT_BIO", ""),
            "author": getattr(module, "BOT_AUTHOR", "unknown"), "decide_func": decide,
            "stat_allocation": allocation, "glyph": glyph, "equipment": equipment}


def _deduplicate_emojis(bots: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove bots with duplicate emojis, keeping first seen."""
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for bot in bots:
        if bot["emoji"] in seen:
            log.warning("Skipping %s — duplicate emoji %s", bot["name"], bot["emoji"])
            continue
        seen.add(bot["emoji"])
        unique.append(bot)
    return unique


def load_bots(bots_dir: str) -> list[dict[str, Any]]:
    """Load all bot modules from a directory.

    Returns list of dicts with keys: name, emoji, bio, author, decide_func
    """
    bots: list[dict[str, Any]] = []
    for filename in sorted(os.listdir(bots_dir)):
        if not filename.endswith(".py"):
            continue
        if filename.startswith("_") or filename == "template.py":
            continue
        bot = _load_single_bot(os.path.join(bots_dir, filename), filename)
        if bot:
            bots.append(bot)
    return _deduplicate_emojis(bots)
