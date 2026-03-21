"""S34 balance regression — trap bot must be competitive but not dominant."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

RESULTS_PATH = Path(__file__).resolve().parent.parent / "tools" / "trap_balance_results.json"

_HAS_RESULTS = RESULTS_PATH.exists()


@pytest.mark.skipif(not _HAS_RESULTS, reason="trap_balance_results.json not generated")
class TestTrapBalance:
    """Verify trap-using bots are balanced."""

    def test_trapper_win_rate_competitive(self) -> None:
        data = json.loads(RESULTS_PATH.read_text())
        trapper_wr = data["Trapper"]["win_rate"]
        assert 10.0 <= trapper_wr <= 65.0, (
            f"Trapper win rate {trapper_wr}% outside 10-65% range"
        )

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
