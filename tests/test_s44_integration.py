"""S44 Integration Gate — Character system validation."""

from __future__ import annotations

from pathlib import Path

from engine.character import build_character_descriptor
from engine.game import run_match
from engine.stats import StatAllocation


class TestCharacterDescriptor:
    def test_bruiser_shape(self) -> None:
        d = build_character_descriptor(StatAllocation(40, 20, 20, 20))
        assert d["shape"] == "hexagon"
        assert d["color"] == "#ff4444"

    def test_tank_border(self) -> None:
        d = build_character_descriptor(
            StatAllocation(20, 20, 40, 20),
            equipment={"weapon": "mace", "armor": "plate"},
        )
        assert d["border_thickness"] == 3
        assert d["weapon_indicator"] == "circle"

    def test_dagger_indicator(self) -> None:
        d = build_character_descriptor(equipment={"weapon": "dagger", "armor": "leather"})
        assert d["weapon_indicator"] == "dot"


class TestMatchJSON:
    def test_character_in_match_data(self) -> None:
        configs = [
            {"name": "A", "emoji": "A", "bio": "a",
             "decide_func": lambda s: ("rest",),
             "stat_allocation": StatAllocation(40, 20, 20, 20)},
            {"name": "B", "emoji": "B", "bio": "b",
             "decide_func": lambda s: ("rest",)},
        ]
        result = run_match(configs, match_id=1, seed=42)
        for player in result["players"]:
            assert "character" in player, f"{player['name']} missing character"
            assert "shape" in player["character"]
            assert "color" in player["character"]


class TestViewerShapes:
    def test_shapes_has_weapon_indicator(self) -> None:
        content = Path("viewer/js/shapes.js").read_text()
        assert "drawWeaponIndicator" in content

    def test_shapes_has_interpolate_color(self) -> None:
        content = Path("viewer/js/shapes.js").read_text()
        assert "interpolateColor" in content

    def test_shapes_has_preview(self) -> None:
        content = Path("viewer/js/shapes.js").read_text()
        assert "drawCharacterPreview" in content


class TestProfilePreview:
    def test_profile_has_canvas(self) -> None:
        content = Path("server/static/profile.html").read_text()
        assert "character-preview" in content
        assert "canvas" in content

    def test_profile_loads_shapes(self) -> None:
        content = Path("server/static/profile.html").read_text()
        assert "shapes.js" in content


class TestCharacterModule:
    def test_exports(self) -> None:
        import engine.character as mod
        for name in mod.__all__:
            assert getattr(mod, name) is not None
