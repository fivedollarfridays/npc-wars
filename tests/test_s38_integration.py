"""S38 Integration Gate — post-match experience end-to-end tests."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from engine.archetype import classify_archetype
from engine.game import run_match
from engine.stats import StatAllocation


class TestDiffDisplay:
    def test_diff_formatter_produces_output(self) -> None:
        from agentgrounds.wars.cli.diff_display import format_diff_section
        diff_data = {
            "win_rate": {"classification": "improved", "delta": 5.0, "percentage": 10.0,
                        "lifetime_avg": 50.0, "current": 55.0},
            "avg_kills": {"classification": "neutral", "delta": 0.0, "percentage": 0.0,
                         "lifetime_avg": 2.0, "current": 2.0},
        }
        result = format_diff_section(diff_data)
        assert len(result) > 0
        assert "▲" in result or "improved" in result.lower()

    def test_first_match_message(self) -> None:
        from agentgrounds.wars.cli.diff_display import format_diff_section
        result = format_diff_section(None)
        assert "first" in result.lower() or "First" in result

    def test_progression_shows_level(self) -> None:
        from agentgrounds.wars.cli.diff_display import format_progression
        xp_data = {"total": 100, "leveled_up": True, "new_level": 2}
        result = format_progression(xp_data, old_level=1, new_level=2)
        assert "2" in result

    def test_full_summary_boxed(self) -> None:
        from agentgrounds.wars.cli.diff_display import format_match_summary
        result = format_match_summary(
            bot_name="TestBot", bot_glyph="◆", placement=1,
            kills=3, rounds_survived=25, score=52,
            momentum_name="Battle Fury", diff_data=None,
            xp_data=None, old_level=1, new_level=1,
        )
        assert "┌" in result
        assert "TestBot" in result


class TestArchetype:
    def test_high_power_is_bruiser(self) -> None:
        assert classify_archetype(StatAllocation(40, 20, 20, 20)) == "Bruiser"

    def test_high_speed_is_assassin(self) -> None:
        assert classify_archetype(StatAllocation(20, 40, 20, 20)) == "Assassin"

    def test_high_armor_is_tank(self) -> None:
        assert classify_archetype(StatAllocation(20, 20, 40, 20)) == "Tank"

    def test_high_mind_is_controller(self) -> None:
        assert classify_archetype(StatAllocation(20, 20, 20, 40)) == "Controller"

    def test_balanced_is_balanced(self) -> None:
        assert classify_archetype(StatAllocation(25, 25, 25, 25)) == "Balanced"

    def test_archetype_in_match_json(self) -> None:
        configs = [
            {"name": "A", "emoji": "A", "bio": "a",
             "decide_func": lambda s: ("rest",),
             "stat_allocation": StatAllocation(40, 20, 20, 20)},
            {"name": "B", "emoji": "B", "bio": "b",
             "decide_func": lambda s: ("rest",)},
        ]
        result = run_match(configs, match_id=1, seed=42)
        assert "archetype" in result["stats"]["A"]
        assert result["stats"]["A"]["archetype"] == "Bruiser"


class TestMatchupProfile:
    def test_matchup_from_history(self) -> None:
        from data.matchup_stats import compute_matchup_profile
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock match JSON
            match = {
                "winner": "A",
                "players": [{"emoji": "A"}, {"emoji": "B"}],
                "stats": {
                    "A": {"archetype": "Bruiser", "kills": 1},
                    "B": {"archetype": "Tank", "kills": 0},
                },
            }
            Path(tmpdir, "match_001.json").write_text(json.dumps(match))
            profile = compute_matchup_profile("A", tmpdir)
            assert "Tank" in profile
            assert profile["Tank"]["wins"] == 1

    def test_empty_dir(self) -> None:
        from data.matchup_stats import compute_matchup_profile
        with tempfile.TemporaryDirectory() as tmpdir:
            profile = compute_matchup_profile("A", tmpdir)
            assert profile == {}


class TestGameRefactor:
    def test_run_match_still_works(self) -> None:
        configs = [
            {"name": "A", "emoji": "A", "bio": "a", "decide_func": lambda s: ("rest",)},
            {"name": "B", "emoji": "B", "bio": "b", "decide_func": lambda s: ("rest",)},
        ]
        result = run_match(configs, match_id=1, seed=42)
        assert "winner" in result
        assert "stats" in result
        assert len(result["rounds"]) > 0

    def test_game_py_under_400_lines(self) -> None:
        game_path = Path("engine/game.py")
        lines = len(game_path.read_text().splitlines())
        assert lines < 400, f"game.py has {lines} lines (limit 400)"

    def test_match_phases_exists(self) -> None:
        import engine.match_phases  # noqa: F401

    def test_match_setup_exists(self) -> None:
        import engine.match_setup  # noqa: F401


class TestNoDeadCode:
    def test_diff_display_exports(self) -> None:
        import agentgrounds.wars.cli.diff_display as mod
        for name in mod.__all__:
            assert getattr(mod, name) is not None

    def test_archetype_exports(self) -> None:
        import engine.archetype as mod
        for name in mod.__all__:
            assert getattr(mod, name) is not None

    def test_matchup_stats_importable(self) -> None:
        import data.matchup_stats  # noqa: F401
