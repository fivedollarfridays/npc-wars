"""Shared test helpers for NPC Wars tests."""

from unittest.mock import AsyncMock, MagicMock

import discord

from engine.combat import Bot


def make_bot(name="TestBot", emoji="🤖", hp=None, energy=None, x=5, y=5,
             stat_allocation=None, glyph=None, **kwargs):
    """Create a Bot with optional overrides."""
    bot = Bot(name=name, emoji=emoji, bio="test", author="tester",
              decide_func=lambda s: ("rest",), x=x, y=y,
              stat_allocation=stat_allocation, glyph=glyph)
    if hp is not None:
        bot.hp = hp
    if energy is not None:
        bot.energy = energy
    for k, v in kwargs.items():
        setattr(bot, k, v)
    return bot


def bot_config(name, emoji, decide_func):
    """Create a bot config dict for run_match."""
    return {"name": name, "emoji": emoji, "bio": "", "author": "test", "decide_func": decide_func}


def always_rest(state):
    return ("rest",)


def chase_and_attack(state):
    """Simple bot: move toward nearest enemy, attack if adjacent."""
    me = state["me"]
    enemies = state["enemies"]
    if not enemies:
        return ("rest",)
    target = min(enemies, key=lambda e: abs(e["x"] - me["x"]) + abs(e["y"] - me["y"]))
    dx = target["x"] - me["x"]
    dy = target["y"] - me["y"]
    if abs(dx) + abs(dy) == 1:
        if dx == 1: return ("attack", "east")
        if dx == -1: return ("attack", "west")
        if dy == 1: return ("attack", "south")
        return ("attack", "north")
    if abs(dx) >= abs(dy):
        return ("move", "east") if dx > 0 else ("move", "west")
    return ("move", "south") if dy > 0 else ("move", "north")


def make_mock_interaction(
    user_id: int | None = None, with_defer: bool = False
) -> MagicMock:
    """Create a mock Discord interaction for command testing."""
    interaction = MagicMock(spec=discord.Interaction)
    if user_id is not None:
        interaction.user = MagicMock()
        interaction.user.id = user_id
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.is_done = MagicMock(return_value=False)
    if with_defer:
        interaction.response.defer = AsyncMock()
        interaction.followup = MagicMock()
        interaction.followup.send = AsyncMock()
    return interaction


def make_bot_config() -> dict:
    """Create a standard NpcWarsBot config dict for testing."""
    return {
        "bot_token": "tok",
        "guild_id": 42,
        "announcement_channel_id": None,
        "results_channel_id": None,
    }
