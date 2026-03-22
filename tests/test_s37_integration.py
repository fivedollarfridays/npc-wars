"""S37 Integration Gate — terrain system end-to-end tests."""

from __future__ import annotations


from engine.game import run_match
from engine.terrain import (
    HIGH_GROUND, OPEN, WALL, WATER,
    MAP_NAMES, TerrainMap, build_map,
)


class TestTerrainMaps:
    def test_all_maps_build(self) -> None:
        for name in MAP_NAMES:
            t = build_map(name, 10)
            assert isinstance(t, TerrainMap)
            assert t.grid_size == 10

    def test_arena_all_open(self) -> None:
        t = build_map("arena", 10)
        for y in range(10):
            for x in range(10):
                assert t.get_tile(x, y) == OPEN

    def test_fortress_has_walls(self) -> None:
        t = build_map("fortress", 10)
        walls = t.get_tiles_of_type(WALL)
        assert len(walls) > 0

    def test_highlands_has_features(self) -> None:
        t = build_map("highlands", 10)
        assert len(t.get_tiles_of_type(HIGH_GROUND)) > 0
        assert len(t.get_tiles_of_type(WATER)) > 0

    def test_maps_scale(self) -> None:
        for size in (10, 12, 15):
            t = build_map("fortress", size)
            assert t.grid_size == size
            assert len(t.tiles) == size


class TestMovementWithTerrain:
    def test_match_on_fortress(self) -> None:
        configs = [
            {"name": "A", "emoji": "A", "bio": "a", "decide_func": lambda s: ("attack", "east")},
            {"name": "B", "emoji": "B", "bio": "b", "decide_func": lambda s: ("attack", "west")},
        ]
        result = run_match(configs, match_id=1, seed=42, map_name="fortress")
        assert result["winner"] != ""
        assert result["map"] == "fortress"

    def test_match_on_highlands(self) -> None:
        configs = [
            {"name": "A", "emoji": "A", "bio": "a", "decide_func": lambda s: ("rest",)},
            {"name": "B", "emoji": "B", "bio": "b", "decide_func": lambda s: ("rest",)},
        ]
        result = run_match(configs, match_id=1, seed=42, map_name="highlands")
        assert result["map"] == "highlands"

    def test_arena_backward_compat(self) -> None:
        configs = [
            {"name": "A", "emoji": "A", "bio": "a", "decide_func": lambda s: ("rest",)},
            {"name": "B", "emoji": "B", "bio": "b", "decide_func": lambda s: ("rest",)},
        ]
        result = run_match(configs, match_id=1, seed=42)
        assert result["map"] == "arena"


class TestCombatWithTerrain:
    def test_terrain_data_in_match_json(self) -> None:
        configs = [
            {"name": "A", "emoji": "A", "bio": "a", "decide_func": lambda s: ("rest",)},
            {"name": "B", "emoji": "B", "bio": "b", "decide_func": lambda s: ("rest",)},
        ]
        result = run_match(configs, match_id=1, seed=42, map_name="fortress")
        assert "terrain_tiles" in result
        assert "map" in result


class TestStateDict:
    def test_self_dict_has_terrain(self) -> None:
        from engine.combat import Bot
        bot = Bot(name="T", emoji="T", bio="t", author="t",
                  decide_func=lambda s: ("rest",), x=3, y=3)
        d = bot.to_self_dict()
        assert "on_terrain" in d
        assert "terrain" in d
        assert d["on_terrain"] == "open"  # no terrain = open

    def test_enemy_dict_has_on_terrain(self) -> None:
        from engine.combat import Bot
        bot = Bot(name="T", emoji="T", bio="t", author="t",
                  decide_func=lambda s: ("rest",), x=3, y=3)
        d = bot.to_enemy_dict()
        assert "on_terrain" in d


class TestFeedFormatters:
    def test_terrain_formatters_registered(self) -> None:
        from agentgrounds.wars.cli.feed import _FORMATTERS
        for event_type in ("wall_blocked", "crystal_pickup"):
            assert event_type in _FORMATTERS, f"Missing {event_type}"


class TestNoDeadCode:
    def test_terrain_exports(self) -> None:
        import engine.terrain as mod
        for name in mod.__all__:
            assert getattr(mod, name) is not None

    def test_terrain_combat_exports(self) -> None:
        import engine.terrain_combat as mod
        for name in mod.__all__:
            assert getattr(mod, name) is not None

    def test_build_map_used_in_game(self) -> None:
        from pathlib import Path
        source = Path("engine/game.py").read_text()
        assert "build_map" in source
