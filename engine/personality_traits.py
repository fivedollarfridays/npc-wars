"""Trait detection, archetype variants, and bio generation for personality profiles."""

from __future__ import annotations

from typing import Any

__all__ = ["detect_traits", "archetype_variant", "generate_bio"]

_HIGH_KILLS = 2.5
_HIGH_DAMAGE = 80
_HIGH_SURVIVAL = 30
_HIGH_MOMENTUM = 3
_MODERATE_ACTION_RATIO = 0.25


def detect_traits(agg: dict[str, Any], patterns: dict) -> list[str]:
    """Detect personality traits from aggregated stats and patterns."""
    traits: list[str] = []
    ratios = agg["action_ratios"]
    eq = agg["equipment_freq"]

    if agg["avg_kills"] >= _HIGH_KILLS or agg["avg_damage"] >= _HIGH_DAMAGE:
        traits.append("Aggressive")
    if agg["early_attack_ratio"] >= 0.5:
        traits.append("Aggressive Opener")
    if ratios.get("defend", 0) >= _MODERATE_ACTION_RATIO:
        traits.append("Defensive")
    elif agg["avg_survival"] >= _HIGH_SURVIVAL and agg["avg_kills"] < 1:
        traits.append("Turtle")
    if agg["avg_survival"] >= _HIGH_SURVIVAL:
        traits.append("Survivor")
    if ratios.get("trap", 0) >= _MODERATE_ACTION_RATIO:
        traits.append("Trap Obsessed")
    if ratios.get("ranged_attack", 0) >= _MODERATE_ACTION_RATIO:
        traits.append("Ranged Specialist")
    _check_mobility(traits, ratios)
    _check_equipment(traits, eq)
    if agg["avg_momentum"] >= _HIGH_MOMENTUM:
        traits.append("Momentum Builder")
    if agg["win_rate"] >= 0.6 and agg["matches"] >= 3:
        traits.append("Dominant")
    traits.extend(_pattern_traits(patterns))
    return traits


def _check_mobility(traits: list[str], ratios: dict[str, float]) -> None:
    dash_move = ratios.get("dash", 0) + ratios.get("move", 0)
    if ratios.get("dash", 0) >= 0.15 or dash_move >= 0.6:
        traits.append("Mobile")


_TACTICAL_LABELS = {
    "battle_cry": "Battle Cryer",
    "fortify": "Fortifier",
    "teleport": "Teleporter",
    "overdrive": "Overdriver",
}


def _check_equipment(traits: list[str], eq: dict) -> None:
    tac = eq.get("tactical", {})
    if tac:
        name = max(tac, key=tac.get)
        traits.append(_TACTICAL_LABELS.get(name, "Tactical User"))
    armor = eq.get("armor", {})
    if armor and max(armor, key=armor.get) in ("plate", "reinforced"):
        traits.append("Heavy Armor")


def _pattern_traits(patterns: dict) -> list[str]:
    traits: list[str] = []
    for context, actions in patterns.items():
        total = sum(actions.values())
        if total == 0:
            continue
        top = max(actions, key=actions.get)
        if context == "storm_closing":
            traits.append("Storm Dodger")
        elif context == "after_damage" and top == "attack" and actions[top] / total >= 0.5:
            traits.append("Counter Puncher")
        elif context == "below_30_hp" and top in ("rest", "defend"):
            traits.append("Cautious")
        elif context == "at_range_1" and top == "ranged_attack":
            traits.append("Kiter")
    return traits


_VARIANTS: dict[str, dict[str, str]] = {
    "Bruiser": {"Aggressive": "Berserker", "Survivor": "Juggernaut", "Momentum Builder": "Wrecking Ball", "": "Brawler"},
    "Assassin": {"Mobile": "Ghost", "Aggressive Opener": "Ambusher", "Ranged Specialist": "Marksman", "": "Blade"},
    "Tank": {"Defensive": "Fortress", "Survivor": "Ironclad", "Heavy Armor": "Sentinel", "": "Guardian"},
    "Controller": {"Trap Obsessed": "Trapper", "Ranged Specialist": "Sniper", "Cautious": "Puppeteer", "": "Tactician"},
    "Balanced": {"Dominant": "Champion", "Aggressive": "Scrapper", "Defensive": "Mediator", "": "Generalist"},
}


def archetype_variant(agg: dict[str, Any], traits: list[str]) -> str:
    """Map base archetype + traits to a specific variant name."""
    base = agg["top_archetype"]
    variants = _VARIANTS.get(base, {})
    for trait in traits:
        if trait in variants:
            return variants[trait]
    return variants.get("", base or "Unknown")


_BIO_TEMPLATES: list[tuple[str, str]] = [
    ("Aggressive", "A relentless force that strikes hard and asks questions never."),
    ("Defensive", "Patience is a weapon — this one outlasts them all."),
    ("Trap Obsessed", "The battlefield is a web, and every step is a mistake."),
    ("Survivor", "Still standing when the dust settles, every single time."),
    ("Ranged Specialist", "Keeps distance and lets precision do the talking."),
    ("Mobile", "Never where you expect, always where it hurts."),
    ("Momentum Builder", "Feeds on chaos, growing stronger with every clash."),
    ("Dominant", "Wins aren't lucky — they're inevitable."),
    ("Counter Puncher", "Hits back harder than whatever hit first."),
    ("Storm Dodger", "Reads the storm like a map and dances around it."),
]

_DEFAULT_BIO = "A competitor forging their identity on the battlefield."


def generate_bio(variant: str, traits: list[str]) -> str:
    """Generate a 1-2 sentence template-based bio from traits."""
    for trait, bio in _BIO_TEMPLATES:
        if trait in traits:
            return bio
    return _DEFAULT_BIO
