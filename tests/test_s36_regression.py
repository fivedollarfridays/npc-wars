"""S36 balance regression -- ability-using bots must be competitive but not dominant."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

RESULTS_PATH = (
    Path(__file__).resolve().parent.parent / "tools" / "ability_balance_results.json"
)

_HAS_RESULTS = RESULTS_PATH.exists()


@pytest.mark.skipif(not _HAS_RESULTS, reason="ability_balance_results.json not generated")
class TestAbilityBalance:
    """Verify ability-equipped bots are balanced."""

    def test_no_bot_above_65_percent(self) -> None:
        data = json.loads(RESULTS_PATH.read_text())
        for name, stats in data.items():
            if name.startswith("_"):
                continue
            wr = stats["win_rate"]
            assert wr < 66.0, f"{name} win rate {wr}% exceeds 65% cap"

    def test_all_bots_have_games(self) -> None:
        data = json.loads(RESULTS_PATH.read_text())
        for name, stats in data.items():
            if name.startswith("_"):
                continue
            assert stats["total"] >= 20, f"{name} has too few games ({stats['total']})"

    def test_mage_has_games(self) -> None:
        """The Mage must participate in the sim."""
        data = json.loads(RESULTS_PATH.read_text())
        assert "Mage" in data, "Mage not found in results"
        assert data["Mage"]["total"] >= 20, (
            f"Mage has too few games ({data['Mage']['total']})"
        )
