"""Tests for cosmetic catalog and inventory system."""

from __future__ import annotations

import sqlite3

import pytest

from server.cosmetic_db import (
    award_coins,
    equip_cosmetic,
    get_coin_balance,
    get_equipped_cosmetics,
    get_player_inventory,
    init_cosmetic_tables,
    purchase_cosmetic,
    unequip_cosmetic,
)


@pytest.fixture()
def conn() -> sqlite3.Connection:
    """In-memory DB with cosmetic tables."""
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    init_cosmetic_tables(db)
    return db


# ── Cycle 1: Catalog validation ─────────────────────────────────────


def test_catalog_has_items_across_all_types() -> None:
    """Catalog must cover all five cosmetic types."""
    from server.cosmetics import COSMETIC_CATALOG

    types_found = {item["type"] for item in COSMETIC_CATALOG.values()}
    expected = {"color_palette", "glow_effect", "weapon_skin", "death_effect", "trail_effect"}
    assert types_found == expected


def test_catalog_has_at_least_20_items() -> None:
    from server.cosmetics import COSMETIC_CATALOG

    assert len(COSMETIC_CATALOG) >= 20


def test_catalog_items_have_required_fields() -> None:
    from server.cosmetics import COSMETIC_CATALOG

    required = {"name", "type", "rarity", "price", "color"}
    for item_id, item in COSMETIC_CATALOG.items():
        missing = required - set(item.keys())
        assert not missing, f"{item_id} missing fields: {missing}"


def test_catalog_rarities_are_valid() -> None:
    from server.cosmetics import COSMETIC_CATALOG

    valid = {"common", "rare", "epic", "legendary"}
    for item_id, item in COSMETIC_CATALOG.items():
        assert item["rarity"] in valid, f"{item_id} has invalid rarity {item['rarity']}"


def test_catalog_prices_are_positive() -> None:
    from server.cosmetics import COSMETIC_CATALOG

    for item_id, item in COSMETIC_CATALOG.items():
        assert item["price"] > 0, f"{item_id} has non-positive price"


# ── Cycle 2: Coin balance ───────────────────────────────────────────


def test_new_player_has_zero_coins(conn: sqlite3.Connection) -> None:
    assert get_coin_balance(conn, "p1") == 0


def test_award_coins_increments_balance(conn: sqlite3.Connection) -> None:
    award_coins(conn, "p1", 50)
    assert get_coin_balance(conn, "p1") == 50
    award_coins(conn, "p1", 30)
    assert get_coin_balance(conn, "p1") == 80


def test_award_coins_separate_players(conn: sqlite3.Connection) -> None:
    award_coins(conn, "p1", 100)
    award_coins(conn, "p2", 200)
    assert get_coin_balance(conn, "p1") == 100
    assert get_coin_balance(conn, "p2") == 200


# ── Cycle 3: Purchase ───────────────────────────────────────────────


def test_purchase_with_sufficient_coins(conn: sqlite3.Connection) -> None:
    award_coins(conn, "p1", 500)
    ok, msg = purchase_cosmetic(conn, "p1", "crimson")  # price 100
    assert ok is True
    assert msg == "Purchased"
    assert get_coin_balance(conn, "p1") == 400


def test_purchase_with_insufficient_coins(conn: sqlite3.Connection) -> None:
    award_coins(conn, "p1", 50)
    ok, msg = purchase_cosmetic(conn, "p1", "crimson")  # price 100
    assert ok is False
    assert "Insufficient" in msg
    assert get_coin_balance(conn, "p1") == 50  # unchanged


def test_purchase_duplicate_fails(conn: sqlite3.Connection) -> None:
    award_coins(conn, "p1", 500)
    purchase_cosmetic(conn, "p1", "crimson")
    ok, msg = purchase_cosmetic(conn, "p1", "crimson")
    assert ok is False
    assert "Already" in msg
    assert get_coin_balance(conn, "p1") == 400  # not charged again


def test_purchase_unknown_item_fails(conn: sqlite3.Connection) -> None:
    award_coins(conn, "p1", 500)
    ok, msg = purchase_cosmetic(conn, "p1", "nonexistent_item")
    assert ok is False
    assert "Unknown" in msg


def test_purchase_appears_in_inventory(conn: sqlite3.Connection) -> None:
    award_coins(conn, "p1", 500)
    purchase_cosmetic(conn, "p1", "crimson")
    inv = get_player_inventory(conn, "p1")
    assert len(inv) == 1
    assert inv[0]["id"] == "crimson"
    assert inv[0]["equipped"] is False


# ── Cycle 4: Equip / Unequip ────────────────────────────────────────


def test_equip_owned_cosmetic(conn: sqlite3.Connection) -> None:
    award_coins(conn, "p1", 500)
    purchase_cosmetic(conn, "p1", "crimson")
    assert equip_cosmetic(conn, "p1", "crimson") is True
    inv = get_player_inventory(conn, "p1")
    assert inv[0]["equipped"] is True


def test_equip_unowned_cosmetic_fails(conn: sqlite3.Connection) -> None:
    assert equip_cosmetic(conn, "p1", "crimson") is False


def test_unequip_cosmetic(conn: sqlite3.Connection) -> None:
    award_coins(conn, "p1", 500)
    purchase_cosmetic(conn, "p1", "crimson")
    equip_cosmetic(conn, "p1", "crimson")
    assert unequip_cosmetic(conn, "p1", "crimson") is True
    inv = get_player_inventory(conn, "p1")
    assert inv[0]["equipped"] is False


def test_unequip_not_equipped_returns_false(conn: sqlite3.Connection) -> None:
    award_coins(conn, "p1", 500)
    purchase_cosmetic(conn, "p1", "crimson")
    assert unequip_cosmetic(conn, "p1", "crimson") is False


def test_equip_new_unequips_same_type(conn: sqlite3.Connection) -> None:
    """Only one cosmetic per type can be equipped."""
    award_coins(conn, "p1", 1000)
    purchase_cosmetic(conn, "p1", "crimson")   # color_palette
    purchase_cosmetic(conn, "p1", "neon")       # color_palette
    equip_cosmetic(conn, "p1", "crimson")
    equip_cosmetic(conn, "p1", "neon")          # should unequip crimson
    equipped = get_equipped_cosmetics(conn, "p1")
    assert "color_palette" in equipped
    assert equipped["color_palette"]["id"] == "neon"


# ── Cycle 5: Equipped cosmetics mapping ─────────────────────────────


def test_get_equipped_cosmetics_returns_type_mapping(conn: sqlite3.Connection) -> None:
    award_coins(conn, "p1", 5000)
    purchase_cosmetic(conn, "p1", "crimson")       # color_palette
    purchase_cosmetic(conn, "p1", "fire_aura")     # glow_effect
    purchase_cosmetic(conn, "p1", "golden_blade")  # weapon_skin
    equip_cosmetic(conn, "p1", "crimson")
    equip_cosmetic(conn, "p1", "fire_aura")
    equip_cosmetic(conn, "p1", "golden_blade")

    equipped = get_equipped_cosmetics(conn, "p1")
    assert len(equipped) == 3
    assert equipped["color_palette"]["id"] == "crimson"
    assert equipped["glow_effect"]["id"] == "fire_aura"
    assert equipped["weapon_skin"]["id"] == "golden_blade"


def test_get_equipped_cosmetics_empty_when_none(conn: sqlite3.Connection) -> None:
    equipped = get_equipped_cosmetics(conn, "p1")
    assert equipped == {}
