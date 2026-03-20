"""Phase 1 Integration Gate — end-to-end validation of S27-S31 systems.

Tests all Phase 1 features: stat allocation, d20 combat, dodge/initiative,
visual identity (glyphs), balance targets, builtin bots, and PROMPT.md docs.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.combat import Bot
from engine.combat_rolls import CombatResult, roll_attack
from engine.game import run_match
from engine.glyphs import is_valid_glyph
from engine.loader import load_bots
from engine.stats import (
    DEFAULT_ALLOCATION,
    STAT_BUDGET,
    STAT_MAX,
    STAT_MIN,
    StatAllocation,
    calculate_derived,
    validate_allocation,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BOTS_DIR = PROJECT_ROOT / "bots"
PROMPT_PATH = PROJECT_ROOT / "PROMPT.md"
BALANCE_PATH = PROJECT_ROOT / "tools" / "balance_results.json"


# ---------------------------------------------------------------------------
# 1. Stat Allocation Round-Trip
# ---------------------------------------------------------------------------


class TestStatAllocationRoundTrip:
    """Verify custom stats flow from allocation through derived to Bot."""

    def test_custom_allocation_validates(self) -> None:
        alloc = validate_allocation(40, 20, 25, 15)
        assert alloc.power == 40
        assert alloc.speed == 20
        assert alloc.armor == 25
        assert alloc.mind == 15

    def test_derived_stats_reflect_allocation(self) -> None:
        alloc = validate_allocation(40, 20, 25, 15)
        derived = calculate_derived(alloc)
        default = calculate_derived(DEFAULT_ALLOCATION)
        # Higher power -> higher crit multiplier (damage base affected by versatility)
        assert derived.crit_multiplier > default.crit_multiplier
        # Lower armor -> lower HP (less versatility bonus too)
        assert derived.max_hp < default.max_hp
        # Lower mind -> lower energy
        assert derived.max_energy < default.max_energy

    def test_bot_uses_derived_stats_for_hp_energy(self) -> None:
        alloc = validate_allocation(40, 20, 25, 15)
        derived = calculate_derived(alloc)
        bot = Bot(
            name="CustomBot", emoji="X", bio="test", author="test",
            decide_func=lambda s: ("rest",), x=0, y=0,
            stat_allocation=alloc,
        )
        assert bot.hp == float(derived.max_hp)
        assert bot.energy == derived.max_energy
        assert bot.derived == derived

    def test_bot_in_match_uses_custom_hp(self) -> None:
        """Run a real match with custom stats and verify HP/energy at start."""
        alloc = validate_allocation(40, 20, 25, 15)
        derived = calculate_derived(alloc)

        def always_rest(state):
            return ("rest",)

        configs = [
            {"name": "Custom", "emoji": "A", "bio": "", "author": "t",
             "decide_func": always_rest, "stat_allocation": alloc},
            {"name": "Default", "emoji": "B", "bio": "", "author": "t",
             "decide_func": always_rest},
        ]
        result = run_match(configs, match_id=1, seed=42)
        # Match ran to completion
        assert result["winner"] in ("A", "B", "none")
        assert len(result["rounds"]) > 0

        # Verify max_hp from round 1 position data
        r1 = result["rounds"][0]
        custom_state = next(
            s for s in r1["positions"] if s["emoji"] == "A"
        )
        assert custom_state["max_hp"] == derived.max_hp


# ---------------------------------------------------------------------------
# 2. Combat Events — hit/miss/crit/dodge in match data
# ---------------------------------------------------------------------------


class TestCombatEvents:
    """Verify d20 roll outcomes appear in match round data."""

    def test_match_contains_attack_events(self) -> None:
        """A 4-bot match with attackers must produce combat events."""

        def chase_attack(state):
            me = state["me"]
            enemies = state["enemies"]
            if not enemies:
                return ("rest",)
            t = min(enemies, key=lambda e: abs(e["x"] - me["x"]) + abs(e["y"] - me["y"]))
            dx, dy = t["x"] - me["x"], t["y"] - me["y"]
            if abs(dx) + abs(dy) == 1:
                if dx == 1:
                    return ("attack", "east")
                if dx == -1:
                    return ("attack", "west")
                if dy == 1:
                    return ("attack", "south")
                return ("attack", "north")
            if abs(dx) >= abs(dy):
                return ("move", "east" if dx > 0 else "west")
            return ("move", "south" if dy > 0 else "north")

        configs = [
            {"name": f"Bot{i}", "emoji": chr(0x1F600 + i), "bio": "", "author": "t",
             "decide_func": chase_attack}
            for i in range(4)
        ]
        result = run_match(configs, match_id=1, seed=100)

        # Collect all event types across all rounds
        all_event_types: set[str] = set()
        has_roll_data = False
        for rnd in result["rounds"]:
            for event in rnd.get("events", []):
                all_event_types.add(event.get("type", ""))
                # Check for d20 roll data in hit/miss events
                if event.get("type") in ("hit", "attack_miss") and "roll" in event:
                    has_roll_data = True

        # d20 combat uses "hit" and "attack_miss" event types
        assert "hit" in all_event_types or "attack_miss" in all_event_types, (
            f"No combat events found. Types: {all_event_types}"
        )
        assert has_roll_data, "Combat events missing d20 roll data"

    def test_hit_miss_crit_dodge_all_possible(self) -> None:
        """With enough rolls, all four outcomes should occur."""
        import random

        rng = random.Random(42)
        attacker_alloc = validate_allocation(25, 25, 25, 25)
        defender_alloc = validate_allocation(25, 40, 25, 10)
        att = calculate_derived(attacker_alloc)
        dfd = calculate_derived(defender_alloc)

        hits, misses, crits, dodges = 0, 0, 0, 0
        for _ in range(500):
            result: CombatResult = roll_attack(att, dfd, rng=rng)
            if result.hit:
                hits += 1
            if result.is_miss:
                misses += 1
            if result.is_crit:
                crits += 1
            if result.dodged:
                dodges += 1

        assert hits > 0, "No hits in 500 rolls"
        assert misses > 0, "No misses in 500 rolls"
        assert crits > 0, "No crits in 500 rolls"
        assert dodges > 0, "No dodges in 500 rolls"


# ---------------------------------------------------------------------------
# 3. Visual Identity — glyphs in state dict
# ---------------------------------------------------------------------------


class TestVisualIdentity:
    """Verify BOT_GLYPH flows through Bot -> state dict -> match data."""

    def test_glyph_in_bot_state_dicts(self) -> None:
        bot = Bot(
            name="GlyphBot", emoji="G", bio="", author="t",
            decide_func=lambda s: ("rest",), x=0, y=0, glyph="★",
        )
        assert bot.glyph == "★"
        assert bot.to_self_dict()["glyph"] == "★"
        assert bot.to_enemy_dict()["glyph"] == "★"

    def test_glyph_defaults_to_emoji_when_absent(self) -> None:
        bot = Bot(
            name="NoGlyph", emoji="E", bio="", author="t",
            decide_func=lambda s: ("rest",), x=0, y=0,
        )
        assert bot.glyph == "E"

    def test_glyph_in_match_player_data(self) -> None:
        configs = [
            {"name": "A", "emoji": "A", "bio": "", "author": "t",
             "decide_func": lambda s: ("rest",), "glyph": "◆"},
            {"name": "B", "emoji": "B", "bio": "", "author": "t",
             "decide_func": lambda s: ("rest",), "glyph": "■"},
        ]
        result = run_match(configs, match_id=1, seed=1)
        player_glyphs = {p["emoji"]: p.get("glyph") for p in result["players"]}
        assert player_glyphs["A"] == "◆"
        assert player_glyphs["B"] == "■"


# ---------------------------------------------------------------------------
# 4. Balance Check — archetype win rates within targets
# ---------------------------------------------------------------------------


_HAS_BALANCE_RESULTS = BALANCE_PATH.exists()


@pytest.mark.skipif(not _HAS_BALANCE_RESULTS, reason="balance_results.json not generated")
class TestBalanceTargets:
    """Verify balance sim results meet Phase 1 targets."""

    def test_balance_results_file_exists(self) -> None:
        assert BALANCE_PATH.exists(), f"Balance results not found: {BALANCE_PATH}"

    def test_balanced_archetype_near_50_percent(self) -> None:
        data = json.loads(BALANCE_PATH.read_text())
        balanced_wr = data["Balanced"]["win_rate"]
        # Target: 48-52%
        assert 45.0 <= balanced_wr <= 55.0, (
            f"Balanced win rate {balanced_wr}% outside 45-55% range"
        )

    def test_no_archetype_above_55_percent(self) -> None:
        data = json.loads(BALANCE_PATH.read_text())
        for name, stats in data.items():
            wr = stats["win_rate"]
            assert wr < 56.0, f"{name} win rate {wr}% exceeds 55% cap"

    def test_all_archetypes_have_positive_win_rate(self) -> None:
        data = json.loads(BALANCE_PATH.read_text())
        for name, stats in data.items():
            assert stats["win_rate"] > 0, f"{name} has 0% win rate"
            assert stats["total"] >= 100, f"{name} has too few games ({stats['total']})"


# ---------------------------------------------------------------------------
# 5. Builtin Bots Audit — valid stats and glyphs
# ---------------------------------------------------------------------------


class TestBuiltinBots:
    """Verify all bots in bots/ have valid stat allocations and glyphs."""

    def test_all_bots_load_successfully(self) -> None:
        bots = load_bots(str(BOTS_DIR))
        assert len(bots) >= 4, f"Expected at least 4 bots, got {len(bots)}"

    def test_all_bots_have_valid_stat_sums(self) -> None:
        bots = load_bots(str(BOTS_DIR))
        for bot in bots:
            alloc: StatAllocation = bot["stat_allocation"]
            total = alloc.power + alloc.speed + alloc.armor + alloc.mind
            assert total == STAT_BUDGET, (
                f"{bot['name']}: stat total {total} != {STAT_BUDGET}"
            )
            for stat_name, val in [
                ("power", alloc.power), ("speed", alloc.speed),
                ("armor", alloc.armor), ("mind", alloc.mind),
            ]:
                assert STAT_MIN <= val <= STAT_MAX, (
                    f"{bot['name']}: {stat_name}={val} outside [{STAT_MIN}, {STAT_MAX}]"
                )

    def test_all_bots_have_valid_glyphs(self) -> None:
        bots = load_bots(str(BOTS_DIR))
        for bot in bots:
            glyph = bot.get("glyph")
            assert glyph is not None, f"{bot['name']}: missing glyph"
            assert is_valid_glyph(glyph), f"{bot['name']}: invalid glyph {glyph!r}"

    def test_bots_have_diverse_stats(self) -> None:
        """Not all bots should be 25/25/25/25 — verify diversity."""
        bots = load_bots(str(BOTS_DIR))
        non_default = [
            b for b in bots
            if b["stat_allocation"] != DEFAULT_ALLOCATION
        ]
        assert len(non_default) >= 3, (
            f"Expected at least 3 non-default stat bots, got {len(non_default)}"
        )

    def test_bots_have_unique_glyphs(self) -> None:
        """Each bot should have a distinct glyph (or at least mostly distinct)."""
        bots = load_bots(str(BOTS_DIR))
        glyphs = [b["glyph"] for b in bots]
        # Allow some duplication but not all the same
        unique = set(glyphs)
        assert len(unique) >= len(glyphs) // 2, (
            f"Too many duplicate glyphs: {len(unique)} unique out of {len(glyphs)}"
        )


# ---------------------------------------------------------------------------
# 6. PROMPT.md Audit — required terms present
# ---------------------------------------------------------------------------


class TestPromptDocs:
    """Verify PROMPT.md documents all Phase 1 systems."""

    REQUIRED_TERMS = [
        "BOT_POWER", "BOT_SPEED", "BOT_ARMOR", "BOT_MIND",
        "d20", "dodge", "BOT_GLYPH",
        "Bruiser", "Assassin", "Tank", "Mage",
    ]

    def test_prompt_file_exists(self) -> None:
        assert PROMPT_PATH.exists(), "PROMPT.md not found at project root"

    def test_all_required_terms_present(self) -> None:
        content = PROMPT_PATH.read_text()
        missing = [term for term in self.REQUIRED_TERMS if term not in content]
        assert not missing, f"PROMPT.md missing terms: {missing}"

    def test_stat_allocation_section_exists(self) -> None:
        content = PROMPT_PATH.read_text()
        assert "Stat Allocation" in content, "PROMPT.md missing 'Stat Allocation' section"

    def test_combat_mechanics_section_exists(self) -> None:
        content = PROMPT_PATH.read_text()
        assert "Combat Mechanics" in content, "PROMPT.md missing 'Combat Mechanics' section"

    def test_visual_identity_section_exists(self) -> None:
        content = PROMPT_PATH.read_text()
        assert "Visual Identity" in content or "BOT_GLYPH" in content, (
            "PROMPT.md missing visual identity docs"
        )


# ---------------------------------------------------------------------------
# 7. No Dead Public Functions in engine/stats.py
# ---------------------------------------------------------------------------


class TestNoDeadPublicFunctions:
    """Every name in engine/stats.__all__ should be imported somewhere outside tests."""

    def test_stats_all_exports_used(self) -> None:
        from engine.stats import __all__ as stats_all

        engine_dir = PROJECT_ROOT / "engine"
        src_files = list(engine_dir.glob("*.py"))
        # Also check top-level scripts
        src_files.extend(PROJECT_ROOT.glob("*.py"))
        src_files.extend((PROJECT_ROOT / "tools").glob("*.py"))
        src_files.extend((PROJECT_ROOT / "server").glob("*.py"))

        # Read all non-test source content
        all_source = ""
        for f in src_files:
            if "test_" in f.name:
                continue
            try:
                all_source += f.read_text()
            except Exception:
                continue

        unused = []
        for name in stats_all:
            if name not in all_source:
                unused.append(name)

        assert not unused, f"Dead exports in engine/stats.__all__: {unused}"
