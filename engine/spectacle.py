"""Spectacle engine -- drama scoring and effect mapping for NPC Wars."""

from dataclasses import dataclass, field
from typing import Any

__all__ = [
    "SpectacleData",
    "SpectacleEngine",
    "DRAMA_WEIGHTS",
    "TIER_RANGES",
    "TRIGGER_EFFECT_MAP",
]


@dataclass
class SpectacleData:
    """Result of scoring a single round for spectacle value."""

    drama_score: int = 0
    near_deaths: list[str] = field(default_factory=list)
    tier: str = "calm"
    triggers: list[str] = field(default_factory=list)
    effects: list[str] = field(default_factory=list)


DRAMA_WEIGHTS: dict[str, int] = {
    "kill": 3,
    "chain_bump": 2,
    "near_death": 4,
    "kill_streak": 5,
    "watcher_spawn": 5,
    "watcher_kill": 4,
    "watcher_sync": 3,
}

TIER_RANGES: list[tuple[int, float, str]] = [
    (0, 3, "calm"),
    (4, 7, "heating"),
    (8, 12, "intense"),
    (13, 18, "hype"),
    (19, float("inf"), "chaos"),
]

TRIGGER_EFFECT_MAP: dict[str, str] = {
    "kill": "shatter",
    "kill_streak": "fire_border",
    "near_death": "slow_mo",
    "chain_bump": "multiball",
    "last_2": "split_screen",
    "storm_kill": "glitch",
    "watcher_spawn": "dark_entrance",
    "watcher_kill": "skull_flash",
    "watcher_sync": "pulse_wave",
}


def _is_near_death(bot: dict[str, Any]) -> bool:
    """Return True if bot is alive with critically low HP (0 < hp < 5)."""
    return bool(bot.get("alive") and 0 < bot.get("hp", 0) < 5)


def _count_alive(bots: list[dict[str, Any]]) -> int:
    """Count alive bots."""
    return sum(1 for b in bots if b.get("alive"))


class SpectacleEngine:
    """Scores rounds for drama value and selects visual effects."""

    def score_round(
        self,
        events: list[dict[str, Any]],
        bots: list[dict[str, Any]],
    ) -> SpectacleData:
        """Score a round's drama level from events and bot states."""
        score = 0
        near_deaths: list[str] = []

        # Score events by type
        for evt in events:
            evt_type = evt.get("type", "")
            if evt_type in DRAMA_WEIGHTS:
                score += DRAMA_WEIGHTS[evt_type]

        # Detect near-deaths
        for bot in bots:
            if _is_near_death(bot):
                near_deaths.append(bot["emoji"])
                score += DRAMA_WEIGHTS["near_death"]

        tier = self.classify_tier(score)
        triggers = self._detect_triggers(events, bots)
        effects = [TRIGGER_EFFECT_MAP[t] for t in triggers if t in TRIGGER_EFFECT_MAP]

        return SpectacleData(
            drama_score=score,
            near_deaths=near_deaths,
            tier=tier,
            triggers=triggers,
            effects=effects,
        )

    def classify_tier(self, drama_score: int) -> str:
        """Map a drama score to a tier name via TIER_RANGES."""
        for low, high, name in TIER_RANGES:
            if low <= drama_score <= high:
                return name
        return "calm"

    def select_effects(
        self,
        events: list[dict[str, Any]],
        bots: list[dict[str, Any]],
    ) -> list[str]:
        """Check trigger conditions and return matching effect names."""
        triggers = self._detect_triggers(events, bots)
        return [TRIGGER_EFFECT_MAP[t] for t in triggers if t in TRIGGER_EFFECT_MAP]

    def _detect_triggers(
        self,
        events: list[dict[str, Any]],
        bots: list[dict[str, Any]],
    ) -> list[str]:
        """Identify which triggers are active for the given round data."""
        triggers: list[str] = []
        has_kill = False
        has_chain_bump = False
        has_kill_streak = False
        has_watcher_spawn = False
        has_watcher_kill = False
        has_watcher_sync = False
        kill_counts: dict[str, int] = {}

        for evt in events:
            evt_type = evt.get("type", "")
            if evt_type == "kill":
                has_kill = True
                attacker = evt.get("attacker", "")
                kill_counts[attacker] = kill_counts.get(attacker, 0) + 1
                if evt.get("cause") == "storm":
                    if "storm_kill" not in triggers:
                        triggers.append("storm_kill")
            elif evt_type == "kill_streak":
                has_kill_streak = True
            elif evt_type == "chain_bump":
                has_chain_bump = True
            elif evt_type == "watcher_spawn":
                has_watcher_spawn = True
            elif evt_type == "watcher_kill":
                has_watcher_kill = True
            elif evt_type == "watcher_sync":
                has_watcher_sync = True

        if has_kill:
            triggers.append("kill")

        # kill_streak: explicit event OR 3+ kills by same attacker
        if has_kill_streak or any(c >= 3 for c in kill_counts.values()):
            triggers.append("kill_streak")

        # near-death
        if any(_is_near_death(b) for b in bots):
            triggers.append("near_death")

        # chain bump
        if has_chain_bump:
            triggers.append("chain_bump")

        # last 2 alive
        if _count_alive(bots) == 2:
            triggers.append("last_2")

        # watcher events
        if has_watcher_spawn:
            triggers.append("watcher_spawn")
        if has_watcher_kill:
            triggers.append("watcher_kill")
        if has_watcher_sync:
            triggers.append("watcher_sync")

        return triggers
