"""S39 Integration Gate — Phase 2 completion validation."""

from __future__ import annotations

from pathlib import Path


class TestPhase2Systems:
    """All Phase 2 modules importable and functional."""

    def test_equipment_system(self) -> None:
        from engine.equipment import EQUIPMENT_CATALOG, validate_equipment
        assert len(EQUIPMENT_CATALOG) == 4  # weapon, armor, accessory, tactical
        ok, _ = validate_equipment({"weapon": "sword", "armor": "leather", "accessories": []})
        assert ok

    def test_ability_system(self) -> None:
        from engine.abilities import validate_ability, ABILITY_TYPES
        assert len(ABILITY_TYPES) >= 4
        result = validate_ability({"name": "X", "type": "damage", "potency": 20,
                                   "range": 2, "cooldown": 3, "energy_cost": 15})
        assert result is not None

    def test_tactical_system(self) -> None:
        from engine.tactical import resolve_tactical_activation
        assert callable(resolve_tactical_activation)

    def test_terrain_system(self) -> None:
        from engine.terrain import MAP_NAMES, build_map
        assert len(MAP_NAMES) == 5
        t = build_map("fortress", 10)
        assert t.grid_size == 10

    def test_archetype_system(self) -> None:
        from engine.archetype import classify_archetype
        from engine.stats import StatAllocation
        assert classify_archetype(StatAllocation(40, 20, 20, 20)) == "Bruiser"

    def test_callback_system(self) -> None:
        from engine.callbacks import CALLBACK_NAMES
        assert "setup" in CALLBACK_NAMES
        assert "power_up" in CALLBACK_NAMES
        assert "evolve" in CALLBACK_NAMES

    def test_trap_system(self) -> None:
        from engine.traps import TrapManager
        tm = TrapManager()
        trap = tm.place_trap("A", 5, 5, 30, round_num=1)
        assert trap is not None

    def test_full_match_all_systems(self) -> None:
        from engine.game import run_match
        configs = [
            {"name": "A", "emoji": "A", "bio": "a",
             "decide_func": lambda s: ("attack", "east"),
             "equipment": {"weapon": "mace", "armor": "plate", "accessories": []}},
            {"name": "B", "emoji": "B", "bio": "b",
             "decide_func": lambda s: ("rest",)},
        ]
        result = run_match(configs, match_id=1, seed=42, map_name="fortress")
        assert "winner" in result
        assert result["map"] == "fortress"
        assert "archetype" in result["stats"]["A"]


class TestArchitecture:
    def test_game_py_under_400(self) -> None:
        lines = len(Path("engine/game.py").read_text().splitlines())
        assert lines < 400, f"game.py: {lines} lines"

    def test_feed_py_under_15_functions(self) -> None:
        source = Path("agentgrounds/wars/cli/feed.py").read_text()
        func_count = source.count("\ndef ")
        assert func_count < 15, f"feed.py: {func_count} functions"

    def test_prompt_under_3000_words(self) -> None:
        words = len(Path("PROMPT.md").read_text().split())
        assert words < 3000, f"PROMPT.md: {words} words"


class TestBalance:
    def test_phase2_results_exist(self) -> None:
        assert Path("tools/phase2_balance_results.json").exists()

    def test_no_bot_above_60(self) -> None:
        import json
        data = json.loads(Path("tools/phase2_balance_results.json").read_text())
        for name, stats in data.get("per_bot", {}).items():
            assert stats["win_rate"] < 61, f"{name}: {stats['win_rate']}%"


class TestDocumentation:
    def test_roadmap_phase2_complete(self) -> None:
        source = Path("docs/proposal-wars-v2-one-year.md").read_text()
        assert "Phase 2: Depth" in source
        assert "COMPLETE" in source
