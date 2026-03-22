"""Match setup helpers: bot creation and match preparation."""

import random
from typing import Any

from engine.combat import Bot
from engine.equipment import EQUIPMENT_DEFAULTS, compute_equipment_bonuses
from engine.tactical import apply_overdrive
from engine.callbacks import discover_callbacks
from engine.grid import calculate_grid_size, spawn_positions
from engine.match_modes import MatchMode

__all__ = ["create_bots", "prepare_match"]

_PROGRESSION_FIELDS = ("unlocked_actions", "line_budget", "win_streak")


def create_bots(
    bot_configs: list[dict[str, Any]], positions: list[tuple[int, int]],
) -> list[Bot]:
    """Create Bot instances from configs and spawn positions."""
    bots = []
    for i, config in enumerate(bot_configs):
        x, y = positions[i]
        bot_obj = Bot(
            name=config["name"], emoji=config["emoji"],
            bio=config["bio"], author=config.get("author", "unknown"),
            decide_func=config["decide_func"], x=x, y=y,
            stat_allocation=config.get("stat_allocation"),
            glyph=config.get("glyph"),
        )
        for fld in _PROGRESSION_FIELDS:
            if fld in config:
                setattr(bot_obj, fld, config[fld])
        if "human_adapter" in config:
            bot_obj.human_adapter = config["human_adapter"]
        # Equipment: load selections and apply bonuses
        equipment = config.get("equipment", dict(EQUIPMENT_DEFAULTS))
        bot_obj.equipment = equipment
        bonuses = compute_equipment_bonuses(equipment)
        bot_obj.equipment_bonuses = bonuses
        bot_obj.hp += bonuses.max_hp
        bot_obj.energy += bonuses.max_energy
        # Apply overdrive passive at match start
        apply_overdrive(bot_obj)
        # Discover callbacks from bot module (if available)
        module = config.get("module")
        if module is not None:
            unlocked_cbs = set(config.get("unlocked_callbacks", []))
            # Default: all callbacks unlocked for loaded bots
            if not unlocked_cbs:
                unlocked_cbs = {"setup", "on_kill", "react", "power_up", "evolve"}
            bot_obj.callbacks = discover_callbacks(module, unlocked_cbs)
        bots.append(bot_obj)
    return bots


def prepare_match(
    bot_configs: list[dict[str, Any]], seed: int | None, mode: MatchMode | None = None,
) -> tuple[list[Bot], list[dict[str, Any]], int, random.Random]:
    """Shared match setup: RNG, grid, bots, players. Returns (bots, players, grid_size, rng)."""
    rng = random.Random(seed)
    grid_size = calculate_grid_size(len(bot_configs))
    positions = spawn_positions(len(bot_configs), grid_size, rng)
    bots = create_bots(bot_configs, positions)
    if mode is not None and mode.starting_hp != 100:
        for b in bots:
            b.hp = mode.starting_hp
    players = [{"emoji": b.emoji, "name": b.name, "bio": b.bio, "author": b.author, "glyph": b.glyph} for b in bots]
    return bots, players, grid_size, rng
