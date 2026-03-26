"""Tests for the /guide player guide page (T51.3)."""

from fastapi.testclient import TestClient

from server.app import app

client = TestClient(app)


def test_guide_returns_200():
    resp = client.get("/guide")
    assert resp.status_code == 200


def test_guide_is_html():
    resp = client.get("/guide")
    assert "text/html" in resp.headers["content-type"]


def test_guide_has_quick_start():
    resp = client.get("/guide")
    assert "Quick Start" in resp.text


def test_guide_has_decide_reference():
    resp = client.get("/guide")
    assert "decide" in resp.text


def test_guide_has_actions():
    resp = client.get("/guide")
    body = resp.text.lower()
    assert "attack" in body
    assert "rest" in body
    assert "defend" in body


def test_guide_has_state_dict_section():
    resp = client.get("/guide")
    body = resp.text.lower()
    assert "state" in body
    assert "enemies" in body


def test_guide_has_equipment_section():
    resp = client.get("/guide")
    body = resp.text.lower()
    assert "equipment" in body
    assert "weapon" in body


def test_guide_has_strategy_tips():
    resp = client.get("/guide")
    body = resp.text.lower()
    assert "strategy" in body or "tips" in body


def test_landing_page_has_guide_link():
    resp = client.get("/")
    assert "/guide" in resp.text
    assert "Guide" in resp.text
