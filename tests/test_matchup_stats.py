"""Tests for matchup stats computation from match history."""

import json
import os
from typing import Any

from data.matchup_stats import compute_matchup_profile


def _write_match(tmpdir: str, match_id: int, data: dict[str, Any]) -> None:
    """Write a match JSON file to the temp directory."""
    path = os.path.join(tmpdir, f"match_{match_id:03d}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)


def _make_match(
    match_id: int,
    winner: str,
    players: list[dict[str, str]],
    stats: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Build a minimal match dict with archetypes in stats."""
    return {
        "match_id": match_id,
        "date": "2026-03-22T00:00:00+00:00",
        "grid_size": 11,
        "players": players,
        "rounds": [],
        "eliminations": [],
        "winner": winner,
        "stats": stats,
        "duration_rounds": 10,
    }


def test_empty_results_dir(tmp_path: Any) -> None:
    """Empty directory returns empty matchup dict."""
    result = compute_matchup_profile("A", str(tmp_path))
    assert result == {}


def test_nonexistent_dir(tmp_path: Any) -> None:
    """Nonexistent directory returns empty matchup dict."""
    result = compute_matchup_profile("A", str(tmp_path / "nope"))
    assert result == {}


def test_bot_not_in_any_match(tmp_path: Any) -> None:
    """Bot not found in any match returns empty dict."""
    match = _make_match(
        1, "B",
        [{"emoji": "B", "name": "B"}, {"emoji": "C", "name": "C"}],
        {"B": {"archetype": "Bruiser"}, "C": {"archetype": "Tank"}},
    )
    _write_match(str(tmp_path), 1, match)
    result = compute_matchup_profile("A", str(tmp_path))
    assert result == {}


def test_single_win_against_archetype(tmp_path: Any) -> None:
    """Single match win tracked against opponent archetype."""
    match = _make_match(
        1, "A",
        [{"emoji": "A", "name": "A"}, {"emoji": "B", "name": "B"}],
        {"A": {"archetype": "Assassin"}, "B": {"archetype": "Tank"}},
    )
    _write_match(str(tmp_path), 1, match)
    result = compute_matchup_profile("A", str(tmp_path))
    assert "Tank" in result
    assert result["Tank"]["wins"] == 1
    assert result["Tank"]["losses"] == 0
    assert result["Tank"]["rate"] == 100.0


def test_loss_tracked(tmp_path: Any) -> None:
    """Loss tracked against opponent archetype."""
    match = _make_match(
        1, "B",
        [{"emoji": "A", "name": "A"}, {"emoji": "B", "name": "B"}],
        {"A": {"archetype": "Bruiser"}, "B": {"archetype": "Controller"}},
    )
    _write_match(str(tmp_path), 1, match)
    result = compute_matchup_profile("A", str(tmp_path))
    assert result["Controller"]["wins"] == 0
    assert result["Controller"]["losses"] == 1
    assert result["Controller"]["rate"] == 0.0


def test_multiple_matches_aggregate(tmp_path: Any) -> None:
    """Multiple matches aggregate wins/losses per archetype."""
    players = [{"emoji": "A", "name": "A"}, {"emoji": "B", "name": "B"}]
    # Win vs Tank
    _write_match(str(tmp_path), 1, _make_match(
        1, "A", players,
        {"A": {"archetype": "Assassin"}, "B": {"archetype": "Tank"}},
    ))
    # Loss vs Tank
    _write_match(str(tmp_path), 2, _make_match(
        2, "B", players,
        {"A": {"archetype": "Assassin"}, "B": {"archetype": "Tank"}},
    ))
    # Win vs Tank
    _write_match(str(tmp_path), 3, _make_match(
        3, "A", players,
        {"A": {"archetype": "Assassin"}, "B": {"archetype": "Tank"}},
    ))
    result = compute_matchup_profile("A", str(tmp_path))
    assert result["Tank"]["wins"] == 2
    assert result["Tank"]["losses"] == 1
    assert result["Tank"]["rate"] == round(2 / 3 * 100, 1)


def test_multiple_opponents_per_match(tmp_path: Any) -> None:
    """Battle royale: multiple opponents in one match."""
    match = _make_match(
        1, "A",
        [{"emoji": "A", "name": "A"}, {"emoji": "B", "name": "B"},
         {"emoji": "C", "name": "C"}],
        {"A": {"archetype": "Bruiser"}, "B": {"archetype": "Tank"},
         "C": {"archetype": "Controller"}},
    )
    _write_match(str(tmp_path), 1, match)
    result = compute_matchup_profile("A", str(tmp_path))
    # Win against both opponent archetypes
    assert result["Tank"]["wins"] == 1
    assert result["Controller"]["wins"] == 1


def test_matches_without_archetype_skipped(tmp_path: Any) -> None:
    """Older matches without archetype field are gracefully skipped."""
    match = _make_match(
        1, "A",
        [{"emoji": "A", "name": "A"}, {"emoji": "B", "name": "B"}],
        {"A": {"kills": 1}, "B": {"kills": 0}},  # no archetype
    )
    _write_match(str(tmp_path), 1, match)
    result = compute_matchup_profile("A", str(tmp_path))
    assert result == {}
