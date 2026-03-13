"""Player profile schema and persistent JSON storage.

Each player has a profile tracking progression: wins, streaks,
unlocked actions, and Watcher encounter stats.
"""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from engine.combat import DEFAULT_LINE_BUDGET, DEFAULT_UNLOCKED_ACTIONS

BUDGET_BASE = DEFAULT_LINE_BUDGET
BUDGET_CAP = 200
BUDGET_PER_WIN = 10
BUDGET_STREAK_REWARDS: dict[int, int] = {3: 15, 5: 25, 10: 50}
BUDGET_WATCHER_BONUS = 20

__all__ = [
    "BUDGET_BASE",
    "BUDGET_CAP",
    "BUDGET_PER_WIN",
    "BUDGET_STREAK_REWARDS",
    "BUDGET_WATCHER_BONUS",
    "PlayerProfile",
    "calculate_line_budget",
    "load_profiles",
    "save_profiles",
    "get_or_create_profile",
    "update_after_match",
    "update_profiles_after_match",
    "update_streak",
]


@dataclass
class PlayerProfile:
    """Persistent player profile with progression fields."""

    player_id: str
    bot_name: str
    emoji: str
    line_budget: int = DEFAULT_LINE_BUDGET
    wins: int = 0
    current_streak: int = 0
    best_streak: int = 0
    unlocked_actions: list[str] = field(
        default_factory=lambda: sorted(DEFAULT_UNLOCKED_ACTIONS)
    )
    watcher_encounters: int = 0
    watcher_wins: int = 0
    watcher_losses: int = 0


def load_profiles(path: Path) -> dict[str, PlayerProfile]:
    """Read JSON file, deserialize to PlayerProfile dict.

    Returns empty dict if file is missing or corrupt.
    """
    try:
        with open(path, encoding="utf-8") as f:
            raw: dict[str, Any] = json.load(f)
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return {}
    return {pid: PlayerProfile(**data) for pid, data in raw.items()}


def save_profiles(profiles: dict[str, PlayerProfile], path: Path) -> None:
    """Serialize profiles dict to JSON. Creates parent dirs if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            {pid: asdict(p) for pid, p in profiles.items()},
            f,
            indent=2,
        )


def get_or_create_profile(
    profiles: dict[str, PlayerProfile],
    player_id: str,
    bot_name: str,
    emoji: str,
) -> PlayerProfile:
    """Return existing profile or create a new one with defaults."""
    if player_id in profiles:
        return profiles[player_id]
    profile = PlayerProfile(player_id=player_id, bot_name=bot_name, emoji=emoji)
    profiles[player_id] = profile
    return profile


def calculate_line_budget(profile: PlayerProfile) -> int:
    """Calculate line budget from wins, best streak, and Watcher wins.

    Formula: BUDGET_BASE + (wins * BUDGET_PER_WIN) + streak_bonus
             + (watcher_wins * BUDGET_WATCHER_BONUS)
    Capped at BUDGET_CAP (200).

    Streak bonus: highest matching threshold from BUDGET_STREAK_REWARDS.
    E.g., best_streak=5 gets the 5-streak bonus (25), NOT the 3-streak bonus.
    """
    total = BUDGET_BASE + (profile.wins * BUDGET_PER_WIN)
    streak_bonus = 0
    for threshold in sorted(BUDGET_STREAK_REWARDS, reverse=True):
        if profile.best_streak >= threshold:
            streak_bonus = BUDGET_STREAK_REWARDS[threshold]
            break
    total += streak_bonus
    total += profile.watcher_wins * BUDGET_WATCHER_BONUS
    return min(total, BUDGET_CAP)


def update_after_match(
    profile: PlayerProfile, is_winner: bool, beat_watcher: bool = False
) -> None:
    """Update profile after a match.

    Increments wins and watcher_wins if applicable, then recalculates
    line_budget. Losers get no stat changes.
    """
    if not is_winner:
        return
    profile.wins += 1
    if beat_watcher:
        profile.watcher_wins += 1
    profile.line_budget = calculate_line_budget(profile)


def update_profiles_after_match(
    profiles_path: Path,
    players: list[dict[str, Any]],
    winner_emoji: str,
) -> None:
    """Update all player profiles after a match completes.

    Loads profiles, creates missing ones, updates streaks/wins/budgets, saves.
    """
    profiles = load_profiles(profiles_path)

    for player in players:
        player_id = player.get("author", player["name"])
        profile = get_or_create_profile(
            profiles, player_id, player["name"], player["emoji"],
        )
        is_winner = player["emoji"] == winner_emoji
        update_streak(profile, is_winner)
        update_after_match(profile, is_winner)

    save_profiles(profiles, profiles_path)


def update_streak(profile: PlayerProfile, is_winner: bool) -> None:
    """Update win streak after a match.

    Win: increment current_streak, update best_streak if new record.
    Loss: reset current_streak to 0 (best_streak preserved).
    """
    if is_winner:
        profile.current_streak += 1
        if profile.current_streak > profile.best_streak:
            profile.best_streak = profile.current_streak
    else:
        profile.current_streak = 0
