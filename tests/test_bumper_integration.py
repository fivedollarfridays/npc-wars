"""Integration tests: bumper physics wired into resolve_movement and _execute_round."""

from tests.conftest import make_bot
from engine.rounds import resolve_movement


class TestResolveMovementBumps:
    """Tests for bump events returned by resolve_movement."""

    def test_resolve_movement_returns_bump_events(self) -> None:
        """Two bots; one moves into the other's tile -> bump event returned."""
        mover = make_bot(emoji="M", x=3, y=3)
        target = make_bot(emoji="T", x=4, y=3)
        alive = [mover, target]
        actions = {"M": ("move", "east"), "T": ("rest",)}

        events = resolve_movement(alive, actions, grid_size=10)
        assert isinstance(events, list)
        bump_types = [e["type"] for e in events]
        assert "bump" in bump_types

    def test_resolve_movement_no_bump_empty_tile(self) -> None:
        """Bot moves to an empty tile -> no bump events."""
        mover = make_bot(emoji="M", x=3, y=3)
        alive = [mover]
        actions = {"M": ("move", "east")}

        events = resolve_movement(alive, actions, grid_size=10)
        assert isinstance(events, list)
        assert len(events) == 0

    def test_movement_still_works_after_refactor(self) -> None:
        """Regression guard: bot moving to empty tile still updates position."""
        mover = make_bot(emoji="M", x=3, y=3)
        alive = [mover]
        actions = {"M": ("move", "east")}

        resolve_movement(alive, actions, grid_size=10)
        assert mover.x == 4
        assert mover.y == 3


class TestBumpDamage:
    """Tests for HP effects from bumper collisions."""

    def test_wall_splat_damage_applied_to_hp(self) -> None:
        """Bot pushed into wall during bump loses WALL_SPLAT_DAMAGE HP."""
        from engine.combat import WALL_SPLAT_DAMAGE

        # Mover at (8,3) moves east into target at (9,3).
        # Target gets pushed east but (10,3) is out of bounds on grid_size=10
        # (valid positions 0..9), so target gets wall-splatted.
        mover = make_bot(emoji="M", x=8, y=3)
        target = make_bot(emoji="T", x=9, y=3, hp=100)
        alive = [mover, target]
        actions = {"M": ("move", "east"), "T": ("rest",)}

        hp_before = target.hp
        events = resolve_movement(alive, actions, grid_size=10)
        assert target.hp == hp_before - WALL_SPLAT_DAMAGE

        wall_splats = [e for e in events if e["type"] == "wall_splat"]
        assert len(wall_splats) >= 1


class TestBumpEventsInRound:
    """Tests for bump events appearing in round data via _execute_round."""

    def test_bump_events_in_round_record(self) -> None:
        """Bump events from movement phase appear in round data events list."""
        from engine.combat import Bot
        from engine.game import _execute_round

        # Place two bots so mover bumps into target
        bots = [
            Bot(name="Mover", emoji="M", bio="", author="t",
                decide_func=lambda s: ("move", "east"), x=3, y=3),
            Bot(name="Target", emoji="T", bio="", author="t",
                decide_func=lambda s: ("rest",), x=4, y=3),
        ]
        round_data, _, _ = _execute_round(bots, round_num=1, grid_size=10, storm_border=0)
        event_types = [e["type"] for e in round_data["events"]]
        assert "bump" in event_types
