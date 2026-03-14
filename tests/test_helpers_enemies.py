"""Tests for the Enemies helper class."""

from __future__ import annotations

from npcwars.helpers import Enemies


def _make_state(mx: int = 5, my: int = 5, enemies: list | None = None) -> dict:
    return {
        "me": {
            "x": mx, "y": my, "hp": 100, "energy": 100,
            "attack_power": 25, "defense": 0,
            "unlocked_actions": ["attack", "defend", "move", "rest"],
            "line_budget": 50, "win_streak": 0,
        },
        "enemies": enemies or [],
        "round": 1,
        "grid_size": 10,
        "storm_border": 0,
        "bumps_last_round": [],
    }


def _enemy(name: str = "Foe", x: int = 6, y: int = 5, hp: int = 80) -> dict:
    return {"name": name, "emoji": "👾", "x": x, "y": y, "hp": hp}


# --- count ---

class TestCount:
    def test_empty(self) -> None:
        e = Enemies(_make_state(enemies=[]))
        assert e.count == 0

    def test_multiple(self) -> None:
        e = Enemies(_make_state(enemies=[_enemy(), _enemy(name="B")]))
        assert e.count == 2


# --- closest ---

class TestClosest:
    def test_empty_returns_none(self) -> None:
        e = Enemies(_make_state(enemies=[]))
        assert e.closest() is None

    def test_single_enemy(self) -> None:
        foe = _enemy(x=7, y=5)
        e = Enemies(_make_state(mx=5, my=5, enemies=[foe]))
        assert e.closest() is foe

    def test_picks_nearest(self) -> None:
        far = _enemy(name="Far", x=9, y=9)
        near = _enemy(name="Near", x=5, y=6)
        e = Enemies(_make_state(mx=5, my=5, enemies=[far, near]))
        assert e.closest() is near

    def test_tie_returns_first(self) -> None:
        a = _enemy(name="A", x=6, y=5)  # dist 1
        b = _enemy(name="B", x=4, y=5)  # dist 1
        e = Enemies(_make_state(mx=5, my=5, enemies=[a, b]))
        assert e.closest() is a


# --- weakest ---

class TestWeakest:
    def test_empty_returns_none(self) -> None:
        e = Enemies(_make_state(enemies=[]))
        assert e.weakest() is None

    def test_single(self) -> None:
        foe = _enemy(hp=30)
        e = Enemies(_make_state(enemies=[foe]))
        assert e.weakest() is foe

    def test_picks_lowest_hp(self) -> None:
        strong = _enemy(name="Strong", hp=90)
        weak = _enemy(name="Weak", hp=10)
        e = Enemies(_make_state(enemies=[strong, weak]))
        assert e.weakest() is weak


# --- wounded ---

class TestWounded:
    def test_empty_returns_empty_list(self) -> None:
        e = Enemies(_make_state(enemies=[]))
        assert e.wounded() == []

    def test_default_threshold_50(self) -> None:
        low = _enemy(name="Low", hp=30)
        high = _enemy(name="High", hp=80)
        e = Enemies(_make_state(enemies=[low, high]))
        result = e.wounded()
        assert result == [low]

    def test_custom_threshold(self) -> None:
        a = _enemy(name="A", hp=60)
        b = _enemy(name="B", hp=90)
        e = Enemies(_make_state(enemies=[a, b]))
        assert e.wounded(threshold=70) == [a]

    def test_none_wounded(self) -> None:
        e = Enemies(_make_state(enemies=[_enemy(hp=80)]))
        assert e.wounded(threshold=50) == []


# --- adjacent ---

class TestAdjacent:
    def test_empty(self) -> None:
        e = Enemies(_make_state(enemies=[]))
        assert e.adjacent() == []

    def test_distance_one(self) -> None:
        adj = _enemy(name="Adj", x=6, y=5)  # dist 1 from (5,5)
        far = _enemy(name="Far", x=8, y=5)  # dist 3
        e = Enemies(_make_state(mx=5, my=5, enemies=[adj, far]))
        assert e.adjacent() == [adj]

    def test_diagonal_not_adjacent(self) -> None:
        diag = _enemy(x=6, y=6)  # manhattan dist 2
        e = Enemies(_make_state(mx=5, my=5, enemies=[diag]))
        assert e.adjacent() == []


# --- nearby ---

class TestNearby:
    def test_empty(self) -> None:
        e = Enemies(_make_state(enemies=[]))
        assert e.nearby() == []

    def test_default_radius_2(self) -> None:
        close = _enemy(name="Close", x=6, y=5)   # dist 1
        mid = _enemy(name="Mid", x=7, y=5)        # dist 2
        far = _enemy(name="Far", x=9, y=9)        # dist 8
        e = Enemies(_make_state(mx=5, my=5, enemies=[close, mid, far]))
        assert e.nearby() == [close, mid]

    def test_custom_radius(self) -> None:
        a = _enemy(name="A", x=8, y=5)  # dist 3
        b = _enemy(name="B", x=9, y=9)  # dist 8
        e = Enemies(_make_state(mx=5, my=5, enemies=[a, b]))
        assert e.nearby(radius=3) == [a]
