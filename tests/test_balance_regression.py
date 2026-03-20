"""Regression tests for 25/25/25/25 balanced builds.

Verifies that default balanced bots produce reasonable gameplay after
balance tuning. Uses seeded RNG for determinism.
"""

import pytest

from engine.game import run_match
from engine.stats import DEFAULT_ALLOCATION, calculate_derived

from tests.conftest import chase_and_attack


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SEEDS = list(range(1, 11))  # deterministic seeds 1-10


def _balanced_config(index: int) -> dict:
    """Create a balanced (25/25/25/25) bot config."""
    emojis = ["A1", "B2", "C3", "D4"]
    return {
        "name": f"Balanced{index}",
        "emoji": emojis[index],
        "bio": "balanced test bot",
        "author": "regression",
        "decide_func": chase_and_attack,
    }


def _run_seeded_match(seed: int) -> dict:
    """Run a single 4-bot balanced match with a given seed."""
    configs = [_balanced_config(i) for i in range(4)]
    return run_match(configs, match_id=1, seed=seed)


def _collect_match_stats(seeds: list[int]) -> dict:
    """Run matches for all seeds and collect aggregate stats."""
    all_hits: list[float] = []
    all_misses: int = 0
    all_crits: int = 0
    all_attacks: int = 0
    rounds_per_match: list[int] = []
    winners: list[str] = []

    for seed in seeds:
        data = _run_seeded_match(seed)
        rounds_per_match.append(len(data["rounds"]))
        winners.append(data.get("winner", "none"))

        for rnd in data["rounds"]:
            for evt in rnd.get("events", []):
                evt_type = evt.get("type", "")
                if evt_type == "hit":
                    all_hits.append(float(evt.get("damage", 0)))
                    all_attacks += 1
                    if evt.get("is_crit"):
                        all_crits += 1
                elif evt_type == "attack_miss":
                    all_misses += 1
                    all_attacks += 1

    return {
        "hits": all_hits,
        "misses": all_misses,
        "crits": all_crits,
        "total_attacks": all_attacks,
        "rounds": rounds_per_match,
        "winners": winners,
    }


# ---------------------------------------------------------------------------
# Fixture: run once, share across tests
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def match_stats() -> dict:
    """Run 10 seeded matches and return aggregate stats."""
    return _collect_match_stats(SEEDS)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestBalancedBuildHP:
    """Verify HP calculation for balanced builds."""

    def test_balanced_hp_is_145(self):
        """25/25/25/25 should yield 145 HP (50 base + 20 armor + 75 versatility)."""
        derived = calculate_derived(DEFAULT_ALLOCATION)
        assert derived.max_hp == 145


class TestBalancedMatchCompletion:
    """Verify matches complete without crashes or hangs."""

    @pytest.mark.parametrize("seed", SEEDS)
    def test_match_completes_with_winner(self, seed: int):
        """Each seeded match should finish and produce a winner."""
        data = _run_seeded_match(seed)
        assert data.get("winner") not in (None, "", "none"), (
            f"Seed {seed}: no winner found"
        )
        assert len(data["rounds"]) > 0, f"Seed {seed}: match had 0 rounds"


class TestBalancedMatchStats:
    """Statistical ranges for balanced build gameplay."""

    def test_average_match_length(self, match_stats: dict):
        """Average match length should be 8-80 rounds.

        Aggressive chase_and_attack bots finish faster than passive ones.
        Lower bound accommodates high-damage balanced builds (35-55 dmg range).
        """
        rounds = match_stats["rounds"]
        avg = sum(rounds) / len(rounds)
        assert 8 <= avg <= 80, (
            f"Average match length {avg:.1f} outside expected range [8, 80]"
        )

    def test_average_damage_per_hit(self, match_stats: dict):
        """Average damage per hit should be 15-55."""
        hits = match_stats["hits"]
        assert len(hits) > 0, "No hits recorded across 10 matches"
        avg = sum(hits) / len(hits)
        assert 15 <= avg <= 55, (
            f"Average damage per hit {avg:.1f} outside expected range [15, 55]"
        )

    def test_miss_rate(self, match_stats: dict):
        """Miss rate should be 15-35% of total attacks."""
        total = match_stats["total_attacks"]
        assert total > 0, "No attacks recorded across 10 matches"
        miss_rate = match_stats["misses"] / total * 100
        assert 15 <= miss_rate <= 35, (
            f"Miss rate {miss_rate:.1f}% outside expected range [15, 35]%"
        )

    def test_crit_rate(self, match_stats: dict):
        """Crit rate should be 3-15% of total attacks that hit."""
        hits = match_stats["hits"]
        assert len(hits) > 0, "No hits recorded across 10 matches"
        crit_rate = match_stats["crits"] / len(hits) * 100
        assert 3 <= crit_rate <= 15, (
            f"Crit rate {crit_rate:.1f}% outside expected range [3, 15]%"
        )

    def test_every_match_has_winner(self, match_stats: dict):
        """All 10 matches should produce a winner."""
        for i, winner in enumerate(match_stats["winners"]):
            assert winner not in (None, "", "none"), (
                f"Match with seed {SEEDS[i]}: no winner"
            )
