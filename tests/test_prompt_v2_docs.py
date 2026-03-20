"""Tests for PROMPT.md v2 content — stat allocation, combat rolls, glyphs, archetypes."""

from __future__ import annotations

from pathlib import Path

from engine.combat import (
    ATTACK_COST,
    DEFEND_COST,
    KILL_BOUNTY_ENERGY,
    MOVE_COST,
    REST_ENERGY_RESTORE,
    REST_HEAL,
    STORM_DAMAGE,
)
from engine.combat_rolls import (
    BASE_AC,
    DEFEND_AC_BONUS,
    RANGED_DAMAGE_SCALE,
    RANGED_HIT_PENALTY,
    REST_HIT_BONUS,
    TAUNT_HIT_PENALTY,
)
from engine.stats import (
    STAT_BUDGET,
    STAT_MAX,
    STAT_MIN,
    DEFAULT_ALLOCATION,
    calculate_derived,
)

PROMPT_PATH = Path(__file__).resolve().parent.parent / "PROMPT.md"


def _read_prompt() -> str:
    assert PROMPT_PATH.exists(), f"PROMPT.md not found at {PROMPT_PATH}"
    return PROMPT_PATH.read_text(encoding="utf-8")


# --- Stat Allocation Section ---


def test_prompt_documents_stat_constants() -> None:
    """PROMPT.md must document the stat budget and bounds from engine/stats.py."""
    text = _read_prompt()
    assert f"sum to {STAT_BUDGET}" in text or f"total {STAT_BUDGET}" in text, (
        f"PROMPT.md must mention stats summing to {STAT_BUDGET}"
    )
    assert str(STAT_MIN) in text, f"PROMPT.md must mention minimum stat {STAT_MIN}"
    assert str(STAT_MAX) in text, f"PROMPT.md must mention maximum stat {STAT_MAX}"


def test_prompt_documents_all_four_stats() -> None:
    """PROMPT.md must document BOT_POWER, BOT_SPEED, BOT_ARMOR, BOT_MIND."""
    text = _read_prompt()
    for stat in ("BOT_POWER", "BOT_SPEED", "BOT_ARMOR", "BOT_MIND"):
        assert stat in text, f"PROMPT.md must document {stat}"


def test_prompt_documents_derived_stats() -> None:
    """PROMPT.md must show derived stats at default (25/25/25/25)."""
    text = _read_prompt()
    derived = calculate_derived(DEFAULT_ALLOCATION)
    # Must show HP, energy, dodge, DR at default allocation
    assert str(derived.max_hp) in text, (
        f"PROMPT.md must show default max_hp={derived.max_hp}"
    )
    assert str(derived.max_energy) in text, (
        f"PROMPT.md must show default max_energy={derived.max_energy}"
    )


# --- Combat Mechanics Section ---


def test_prompt_documents_combat_constants() -> None:
    """PROMPT.md must include accurate combat constants from combat_rolls.py."""
    text = _read_prompt()
    assert f"AC (base {BASE_AC}" in text or "base AC" in text or f"AC = {BASE_AC}" in text, (
        f"PROMPT.md must document base AC={BASE_AC}"
    )
    assert str(DEFEND_AC_BONUS) in text, (
        f"PROMPT.md must document defend AC bonus={DEFEND_AC_BONUS}"
    )
    assert str(REST_HIT_BONUS) in text, (
        f"PROMPT.md must document rest hit bonus=+{REST_HIT_BONUS}"
    )
    assert str(TAUNT_HIT_PENALTY) in text, (
        f"PROMPT.md must document taunt hit penalty=-{TAUNT_HIT_PENALTY}"
    )


def test_prompt_documents_ranged_attack() -> None:
    """PROMPT.md must document ranged attack penalties."""
    text = _read_prompt()
    assert str(RANGED_HIT_PENALTY) in text, (
        f"PROMPT.md must document ranged hit penalty={RANGED_HIT_PENALTY}"
    )
    assert str(RANGED_DAMAGE_SCALE) in text or "60%" in text, (
        f"PROMPT.md must document ranged damage scale={RANGED_DAMAGE_SCALE}"
    )


def test_prompt_documents_dodge_mechanic() -> None:
    """PROMPT.md must explain dodge as partial damage reduction."""
    text = _read_prompt()
    assert "dodge" in text.lower(), "PROMPT.md must document the dodge mechanic"
    # Dodge halves damage
    assert "half" in text.lower() or "50%" in text, (
        "PROMPT.md must mention dodge halving damage"
    )


def test_prompt_documents_crit_threshold() -> None:
    """PROMPT.md must document the crit threshold."""
    text = _read_prompt()
    assert "crit" in text.lower(), "PROMPT.md must document critical hits"
    assert "natural 20" in text.lower() or "nat 20" in text.lower(), (
        "PROMPT.md must mention natural 20 always crits"
    )


# --- Archetype Guide ---


def test_prompt_documents_archetypes() -> None:
    """PROMPT.md must show example archetype builds."""
    text = _read_prompt()
    # Must have at least 4 named archetypes
    archetype_names = ["Bruiser", "Assassin", "Tank", "Mage"]
    found = sum(1 for name in archetype_names if name in text)
    assert found >= 4, (
        f"PROMPT.md must document at least 4 archetypes, found {found}: "
        f"{[n for n in archetype_names if n in text]}"
    )


# --- Glyph Section ---


def test_prompt_documents_bot_glyph() -> None:
    """PROMPT.md must document BOT_GLYPH."""
    text = _read_prompt()
    assert "BOT_GLYPH" in text, "PROMPT.md must document BOT_GLYPH"


# --- State Dict Completeness ---


def test_prompt_documents_v2_state_fields() -> None:
    """PROMPT.md must document new v2 state fields available in state['me']."""
    text = _read_prompt()
    v2_fields = [
        "hit_chance_vs",
        "dodge_chance",
        "damage_reduction",
        "momentum",
        "score",
        "incoming_threat",
    ]
    for field in v2_fields:
        assert field in text, f"PROMPT.md must document state field '{field}'"


# --- Action Costs Accuracy ---


def test_prompt_action_costs_match_code() -> None:
    """PROMPT.md must show action costs that match engine/combat.py constants."""
    text = _read_prompt()
    # Move cost
    assert str(MOVE_COST) in text, f"PROMPT.md must show move cost={MOVE_COST}"
    # Attack cost
    assert str(ATTACK_COST) in text, f"PROMPT.md must show attack cost={ATTACK_COST}"
    # Defend cost
    assert str(DEFEND_COST) in text, f"PROMPT.md must show defend cost={DEFEND_COST}"
    # Rest heal / energy restore
    assert str(REST_HEAL) in text, f"PROMPT.md must show rest heal={REST_HEAL}"
    assert str(REST_ENERGY_RESTORE) in text, (
        f"PROMPT.md must show rest energy={REST_ENERGY_RESTORE}"
    )


def test_prompt_storm_damage_matches_code() -> None:
    """PROMPT.md storm damage must match engine constant."""
    text = _read_prompt()
    assert str(STORM_DAMAGE) in text, (
        f"PROMPT.md must show storm damage={STORM_DAMAGE}"
    )


def test_prompt_kill_bounty_matches_code() -> None:
    """PROMPT.md kill bounty must match engine constant."""
    text = _read_prompt()
    assert str(KILL_BOUNTY_ENERGY) in text, (
        f"PROMPT.md must show kill bounty={KILL_BOUNTY_ENERGY}"
    )
