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
    "kill": 4,
    "chain_bump": 2,
    "near_death": 4,
    "kill_streak": 5,
    "multi_kill": 6,
    "last_two_alive": 5,
    "storm_kill": 3,
    "low_hp_combat": 2,
    "watcher_spawn": 5,
    "watcher_kill": 4,
    "watcher_sync": 3,
}

TIER_RANGES: list[tuple[int, float, str]] = [
    (0, 2, "calm"),
    (3, 5, "heating"),
    (6, 9, "intense"),
    (10, 14, "hype"),
    (15, float("inf"), "chaos"),
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


def _score_situational(
    events: list[dict[str, Any]],
    bots: list[dict[str, Any]],
) -> int:
    """Score bonus drama from situational events (multi-kill, last-2, etc.)."""
    bonus = 0
    kill_count = sum(1 for e in events if e.get("type") == "kill")
    if kill_count >= 2:
        bonus += DRAMA_WEIGHTS["multi_kill"]
    if _count_alive(bots) == 2:
        bonus += DRAMA_WEIGHTS["last_two_alive"]
    if any(e.get("type") == "kill" and e.get("cause") == "storm" for e in events):
        bonus += DRAMA_WEIGHTS["storm_kill"]
    if _has_low_hp_combat(events):
        bonus += DRAMA_WEIGHTS["low_hp_combat"]
    return bonus


def _has_low_hp_combat(events: list[dict[str, Any]]) -> bool:
    """Check if any hit event involves both combatants below 30 HP."""
    for evt in events:
        if evt.get("type") != "hit":
            continue
        attacker_hp = evt.get("attacker_hp", 999)
        target_hp = evt.get("target_hp", 999)
        if attacker_hp < 30 and target_hp < 30:
            return True
    return False


def _scan_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Scan events and return flags and counts for trigger detection."""
    result: dict[str, Any] = {
        "has_kill": False,
        "has_chain_bump": False,
        "has_kill_streak": False,
        "has_watcher_spawn": False,
        "has_watcher_kill": False,
        "has_watcher_sync": False,
        "kill_counts": {},
        "early_triggers": [],
    }
    flag_types = {
        "kill_streak", "chain_bump",
        "watcher_spawn", "watcher_kill", "watcher_sync",
    }
    for evt in events:
        evt_type = evt.get("type", "")
        if evt_type == "kill":
            result["has_kill"] = True
            attacker = evt.get("attacker", "")
            result["kill_counts"][attacker] = result["kill_counts"].get(attacker, 0) + 1
            if evt.get("cause") == "storm" and "storm_kill" not in result["early_triggers"]:
                result["early_triggers"].append("storm_kill")
        elif evt_type in flag_types:
            result[f"has_{evt_type}"] = True
    return result


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

        # Situational bonuses (multi-kill, last-2-alive, storm kill, low HP)
        score += _score_situational(events, bots)

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
        scan = _scan_events(events)
        triggers = list(scan["early_triggers"])

        if scan["has_kill"]:
            triggers.append("kill")
        if scan["has_kill_streak"] or any(c >= 3 for c in scan["kill_counts"].values()):
            triggers.append("kill_streak")
        if any(_is_near_death(b) for b in bots):
            triggers.append("near_death")
        if scan["has_chain_bump"]:
            triggers.append("chain_bump")
        if _count_alive(bots) == 2:
            triggers.append("last_2")
        for wt in ("watcher_spawn", "watcher_kill", "watcher_sync"):
            if scan.get(f"has_{wt}"):
                triggers.append(wt)
        return triggers
