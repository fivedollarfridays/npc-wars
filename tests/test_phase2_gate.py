"""Phase 2 Balance Gate -- validate unified balance simulation results.

Skips gracefully if phase2_balance_results.json has not been generated yet.
Run tools/phase2_balance_sim.py first to produce the results file.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_PATH = PROJECT_ROOT / "tools" / "phase2_balance_results.json"

_HAS_RESULTS = RESULTS_PATH.exists()
_SKIP_REASON = "phase2_balance_results.json not generated -- run tools/phase2_balance_sim.py"


def _load_results() -> dict:
    return json.loads(RESULTS_PATH.read_text())


# ---------------------------------------------------------------------------
# 1. Per-bot win rate cap
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _HAS_RESULTS, reason=_SKIP_REASON)
class TestBotWinRates:
    """No individual bot should dominate or be useless."""

    def test_no_bot_above_60_percent(self) -> None:
        data = _load_results()
        for name, stats in data["per_bot"].items():
            wr = stats["win_rate"]
            assert wr <= 60.0, f"{name} win rate {wr}% exceeds 60% cap"

    def test_all_bots_have_minimum_matches(self) -> None:
        data = _load_results()
        for name, stats in data["per_bot"].items():
            assert stats["total_matches"] >= 30, (
                f"{name} only played {stats['total_matches']} matches (need >= 30)"
            )


# ---------------------------------------------------------------------------
# 2. Per-archetype balance
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _HAS_RESULTS, reason=_SKIP_REASON)
class TestArchetypeBalance:
    """Archetype win rates should be reasonably balanced."""

    def test_no_archetype_above_60_percent(self) -> None:
        data = _load_results()
        for name, stats in data["per_archetype"].items():
            wr = stats["win_rate"]
            assert wr <= 60.0, f"Archetype {name} win rate {wr}% exceeds 60%"

    def test_balanced_archetype_in_range(self) -> None:
        data = _load_results()
        archetypes = data["per_archetype"]
        if "Balanced" not in archetypes:
            pytest.skip("No Balanced archetype bots loaded")
        wr = archetypes["Balanced"]["win_rate"]
        assert 10.0 <= wr <= 60.0, (
            f"Balanced archetype win rate {wr}% outside 10-60% range"
        )


# ---------------------------------------------------------------------------
# 3. Map coverage
# ---------------------------------------------------------------------------

EXPECTED_MAPS = {"arena", "fortress", "highlands", "maze", "storm_pit"}


@pytest.mark.skipif(not _HAS_RESULTS, reason=_SKIP_REASON)
class TestMapCoverage:
    """All maps must be represented in the simulation."""

    def test_all_maps_present(self) -> None:
        data = _load_results()
        map_names = set(data["per_map"].keys())
        missing = EXPECTED_MAPS - map_names
        assert not missing, f"Missing maps: {missing}"

    def test_maps_have_matches(self) -> None:
        data = _load_results()
        for name, stats in data["per_map"].items():
            assert stats["matches"] > 0, f"Map {name} has no matches"


# ---------------------------------------------------------------------------
# 4. Structural integrity
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _HAS_RESULTS, reason=_SKIP_REASON)
class TestResultsStructure:
    """Results file has expected top-level keys and data shapes."""

    def test_has_required_sections(self) -> None:
        data = _load_results()
        for key in ("per_bot", "per_archetype", "per_map", "per_weapon", "meta"):
            assert key in data, f"Missing section: {key}"

    def test_meta_has_total_matches(self) -> None:
        data = _load_results()
        assert data["meta"]["total_matches"] >= 500, (
            f"Only {data['meta']['total_matches']} matches -- need >= 500"
        )
