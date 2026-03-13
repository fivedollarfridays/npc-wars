"""Shared TypedDicts for NPC Wars engine data structures."""

from typing import Any, TypedDict

__all__ = ["EnemyInfo", "SelfInfo", "GameState", "BotConfig", "Event", "MatchData"]


class EnemyInfo(TypedDict):
    name: str
    emoji: str
    x: int
    y: int
    hp: int


class SelfInfo(TypedDict):
    x: int
    y: int
    hp: int
    energy: int
    attack_power: int
    defense: int


class GameState(TypedDict):
    me: SelfInfo
    enemies: list[EnemyInfo]
    round: int
    grid_size: int
    storm_border: int


class BotConfig(TypedDict):
    name: str
    emoji: str
    bio: str
    author: str
    decide_func: Any  # Callable[..., Any] -- user-provided


# Loose event/record types (mixed keys)
Event = dict[str, Any]
MatchData = dict[str, Any]
