"""Tests for cosmetic store API endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from server.app import app
from server.cosmetic_db import award_coins
from server.cosmetics import COSMETIC_CATALOG
from server.db import create_api_key, create_player, init_db


# ── Fixtures ────────────────────────────────────────────────────────


@pytest.fixture()
def client(tmp_path):
    """TestClient with fresh DB."""
    conn = init_db(str(tmp_path / "cosmetic_test.db"))
    old_db = app.state.db
    app.state.db = conn
    yield TestClient(app)
    app.state.db = old_db


def _make_player(conn, name: str = "alice") -> tuple[str, str]:
    """Create player + API key. Returns (player_id, api_key)."""
    pid = f"pid_{name}"
    create_player(conn, pid, name)
    key = create_api_key(conn, pid)
    return pid, key


# ── Cycle 1: GET /api/store ─────────────────────────────────────────


def test_browse_store_returns_catalog(client):
    """GET /api/store returns all 21 items."""
    resp = client.get("/api/store")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == len(COSMETIC_CATALOG)
    # Each item has an id plus catalog fields
    ids = {item["id"] for item in items}
    assert "crimson" in ids
    assert "void" in ids


def test_browse_store_item_has_fields(client):
    """Each store item has name, type, rarity, price, color."""
    resp = client.get("/api/store")
    item = resp.json()[0]
    for field in ("id", "name", "type", "rarity", "price", "color"):
        assert field in item


# ── Cycle 2: GET /api/coins ─────────────────────────────────────────


def test_coin_balance_zero_for_new_player(client):
    """GET /api/coins returns 0 for a player with no coins."""
    conn = app.state.db
    _pid, key = _make_player(conn, "newbie")
    resp = client.get("/api/coins", headers={"X-API-Key": key})
    assert resp.status_code == 200
    assert resp.json()["balance"] == 0


def test_coin_balance_after_award(client):
    """GET /api/coins returns correct balance after awarding coins."""
    conn = app.state.db
    pid, key = _make_player(conn, "rich")
    award_coins(conn, pid, 500)
    resp = client.get("/api/coins", headers={"X-API-Key": key})
    assert resp.status_code == 200
    assert resp.json()["balance"] == 500


def test_coin_balance_requires_auth(client):
    """GET /api/coins without API key returns 401."""
    resp = client.get("/api/coins")
    assert resp.status_code == 401


# ── Cycle 3: POST /api/store/buy ────────────────────────────────────


def test_buy_cosmetic_success(client):
    """POST /api/store/buy with enough coins succeeds."""
    conn = app.state.db
    pid, key = _make_player(conn, "buyer")
    award_coins(conn, pid, 500)
    resp = client.post(
        "/api/store/buy?cosmetic_id=crimson",
        headers={"X-API-Key": key},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True


def test_buy_cosmetic_insufficient_coins(client):
    """POST /api/store/buy with insufficient coins returns 400."""
    conn = app.state.db
    _pid, key = _make_player(conn, "broke")
    resp = client.post(
        "/api/store/buy?cosmetic_id=crimson",
        headers={"X-API-Key": key},
    )
    assert resp.status_code == 400


def test_buy_cosmetic_unknown_item(client):
    """POST /api/store/buy with invalid cosmetic_id returns 400."""
    conn = app.state.db
    _pid, key = _make_player(conn, "confused")
    resp = client.post(
        "/api/store/buy?cosmetic_id=nonexistent",
        headers={"X-API-Key": key},
    )
    assert resp.status_code == 400


def test_buy_cosmetic_already_owned(client):
    """POST /api/store/buy for an already-owned item returns 400."""
    conn = app.state.db
    pid, key = _make_player(conn, "greedy")
    award_coins(conn, pid, 1000)
    client.post("/api/store/buy?cosmetic_id=crimson", headers={"X-API-Key": key})
    resp = client.post(
        "/api/store/buy?cosmetic_id=crimson",
        headers={"X-API-Key": key},
    )
    assert resp.status_code == 400
    assert "Already owned" in resp.json()["detail"]


# ── Cycle 4: GET /api/inventory ──────────────────────────────────────


def test_inventory_empty(client):
    """GET /api/inventory returns empty list for new player."""
    conn = app.state.db
    _pid, key = _make_player(conn, "empty")
    resp = client.get("/api/inventory", headers={"X-API-Key": key})
    assert resp.status_code == 200
    assert resp.json() == []


def test_inventory_after_purchase(client):
    """GET /api/inventory shows purchased item."""
    conn = app.state.db
    pid, key = _make_player(conn, "shopper")
    award_coins(conn, pid, 500)
    client.post("/api/store/buy?cosmetic_id=crimson", headers={"X-API-Key": key})
    resp = client.get("/api/inventory", headers={"X-API-Key": key})
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["id"] == "crimson"


# ── Cycle 5: POST /api/inventory/equip + unequip ────────────────────


def test_equip_owned_cosmetic(client):
    """POST /api/inventory/equip equips an owned cosmetic."""
    conn = app.state.db
    pid, key = _make_player(conn, "equipper")
    award_coins(conn, pid, 500)
    client.post("/api/store/buy?cosmetic_id=crimson", headers={"X-API-Key": key})
    resp = client.post(
        "/api/inventory/equip?cosmetic_id=crimson",
        headers={"X-API-Key": key},
    )
    assert resp.status_code == 200
    assert resp.json()["equipped"] is True


def test_equip_unowned_cosmetic(client):
    """POST /api/inventory/equip for unowned item returns 400."""
    conn = app.state.db
    _pid, key = _make_player(conn, "cheater")
    resp = client.post(
        "/api/inventory/equip?cosmetic_id=crimson",
        headers={"X-API-Key": key},
    )
    assert resp.status_code == 400


def test_unequip_cosmetic(client):
    """POST /api/inventory/unequip removes equip status."""
    conn = app.state.db
    pid, key = _make_player(conn, "unequipper")
    award_coins(conn, pid, 500)
    client.post("/api/store/buy?cosmetic_id=crimson", headers={"X-API-Key": key})
    client.post("/api/inventory/equip?cosmetic_id=crimson", headers={"X-API-Key": key})
    resp = client.post(
        "/api/inventory/unequip?cosmetic_id=crimson",
        headers={"X-API-Key": key},
    )
    assert resp.status_code == 200
    assert resp.json()["unequipped"] is True


def test_unequip_not_equipped(client):
    """POST /api/inventory/unequip on non-equipped item returns 400."""
    conn = app.state.db
    pid, key = _make_player(conn, "confused2")
    award_coins(conn, pid, 500)
    client.post("/api/store/buy?cosmetic_id=crimson", headers={"X-API-Key": key})
    resp = client.post(
        "/api/inventory/unequip?cosmetic_id=crimson",
        headers={"X-API-Key": key},
    )
    assert resp.status_code == 400
