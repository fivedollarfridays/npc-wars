"""S46 Integration Gate — Cosmetic system validation."""

from __future__ import annotations

from pathlib import Path


class TestCosmeticCatalog:
    def test_catalog_exists(self) -> None:
        from server.cosmetics import COSMETIC_CATALOG
        assert len(COSMETIC_CATALOG) >= 20

    def test_all_types_represented(self) -> None:
        from server.cosmetics import COSMETIC_CATALOG
        types = {v["type"] for v in COSMETIC_CATALOG.values()}
        assert "color_palette" in types
        assert "glow_effect" in types
        assert "weapon_skin" in types
        assert "death_effect" in types
        assert "trail_effect" in types


class TestCosmeticDB:
    def test_db_functions_exist(self) -> None:
        from server.cosmetic_db import (
            purchase_cosmetic, get_player_inventory,
            equip_cosmetic, get_equipped_cosmetics,
            award_coins, get_coin_balance,
        )
        assert all(callable(f) for f in [
            purchase_cosmetic, get_player_inventory,
            equip_cosmetic, get_equipped_cosmetics,
            award_coins, get_coin_balance,
        ])


class TestStoreAPI:
    def test_cosmetics_route_exists(self) -> None:
        from server.routes.cosmetics import router
        assert router is not None

    def test_coin_rewards_exist(self) -> None:
        from server.coin_rewards import award_match_coins
        assert callable(award_match_coins)


class TestViewerRendering:
    def test_shapes_handles_cosmetics(self) -> None:
        content = Path("viewer/js/shapes.js").read_text()
        assert "cosmetics" in content.lower() or "cosmetic" in content.lower()

    def test_store_page_exists(self) -> None:
        assert Path("server/static/store.html").exists()


class TestModules:
    def test_cosmetics_module(self) -> None:
        import server.cosmetics  # noqa: F401

    def test_cosmetic_db_module(self) -> None:
        import server.cosmetic_db  # noqa: F401

    def test_coin_rewards_module(self) -> None:
        import server.coin_rewards  # noqa: F401
