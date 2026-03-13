"""Tests for dash action — moves 2 tiles, costs 15 energy."""

from tests.conftest import make_bot

from engine.combat import DASH_COST, ACTION_COSTS
from engine.rounds import resolve_movement
from engine.sandbox import validate_action


class TestDashCost:
    """Cycle 2: dash costs 15 energy."""

    def test_dash_cost_is_15(self):
        assert DASH_COST == 15

    def test_dash_in_action_costs(self):
        assert ACTION_COSTS["dash"] == 15


class TestDashValidation:
    """Cycle 1: dash action validation."""

    def test_dash_with_valid_direction_passes(self):
        result = validate_action(("dash", "east"))
        assert result == ("dash", "east")

    def test_dash_with_invalid_direction_fails(self):
        result = validate_action(("dash", "invalid"))
        assert result is None


class TestDashMovement:
    """Cycle 3: dash moves bot 2 tiles, clamps at edge."""

    def test_dash_moves_2_tiles_on_empty_path(self):
        bot = make_bot(x=5, y=5)
        actions = {bot.emoji: ("dash", "east")}
        resolve_movement([bot], actions, grid_size=10, all_bots=[bot])
        assert bot.x == 7
        assert bot.y == 5

    def test_dash_stops_at_1_tile_if_second_oob(self):
        """Bot at x=8 dashing east on 10-wide grid: tile 1 = 9 (valid), tile 2 = 10 (OOB)."""
        bot = make_bot(x=8, y=5)
        actions = {bot.emoji: ("dash", "east")}
        resolve_movement([bot], actions, grid_size=10, all_bots=[bot])
        assert bot.x == 9
        assert bot.y == 5

    def test_dash_no_move_if_first_tile_oob(self):
        """Bot at x=9 dashing east on 10-wide grid: tile 1 = 10 (OOB), no move."""
        bot = make_bot(x=9, y=5)
        actions = {bot.emoji: ("dash", "east")}
        resolve_movement([bot], actions, grid_size=10, all_bots=[bot])
        assert bot.x == 9
        assert bot.y == 5

    def test_dash_generates_event(self):
        bot = make_bot(x=5, y=5)
        actions = {bot.emoji: ("dash", "east")}
        events = resolve_movement([bot], actions, grid_size=10, all_bots=[bot])
        dash_events = [e for e in events if e.get("type") == "dash"]
        assert len(dash_events) == 1
        assert dash_events[0]["emoji"] == bot.emoji
        assert dash_events[0]["from_x"] == 5
        assert dash_events[0]["to_x"] == 7


class TestDashBumps:
    """Cycle 4: dash interacts with bumper physics."""

    def test_dash_bumps_bot_at_destination(self):
        """Dasher lands on occupied tile 2, triggering bump on occupant."""
        dasher = make_bot(emoji="D", x=3, y=5)
        target = make_bot(emoji="T", x=5, y=5)
        all_bots = [dasher, target]
        actions = {dasher.emoji: ("dash", "east")}
        events = resolve_movement([dasher], actions, grid_size=10,
                                  all_bots=all_bots)
        bump_events = [e for e in events if e.get("type") == "bump"]
        assert len(bump_events) == 1
        assert bump_events[0]["pusher"] == "D"
        assert bump_events[0]["target"] == "T"

    def test_dash_bumps_bot_at_intermediate_tile(self):
        """Dasher's destination is tile 2, but if tile 2 is OOB and
        bot sits at tile 1, the dasher goes to tile 1 and bumps."""
        dasher = make_bot(emoji="D", x=7, y=5)
        blocker = make_bot(emoji="B", x=8, y=5)
        all_bots = [dasher, blocker]
        # Dash east: mid=8, end=9 (valid). Destination=9, but blocker at 8
        # is NOT at destination. Dasher goes to x=9. No bump at 8.
        # Actually let's test the edge case: dasher at x=8, dashes east,
        # tile1=9 valid, tile2=10 OOB, dest=9. Blocker at 9.
        dasher = make_bot(emoji="D", x=8, y=5)
        blocker = make_bot(emoji="B", x=9, y=5)
        all_bots = [dasher, blocker]
        actions = {dasher.emoji: ("dash", "east")}
        events = resolve_movement([dasher], actions, grid_size=10,
                                  all_bots=all_bots)
        bump_events = [e for e in events if e.get("type") == "bump"]
        assert len(bump_events) >= 1
        assert bump_events[0]["pusher"] == "D"
        assert bump_events[0]["target"] == "B"

    def test_dash_chain_bump(self):
        """Dasher bumps target, target pushed into another bot -> chain."""
        dasher = make_bot(emoji="D", x=3, y=5)
        bot_a = make_bot(emoji="A", x=5, y=5)
        bot_b = make_bot(emoji="B", x=6, y=5)
        all_bots = [dasher, bot_a, bot_b]
        actions = {dasher.emoji: ("dash", "east")}
        events = resolve_movement([dasher], actions, grid_size=10,
                                  all_bots=all_bots)
        bump_events = [e for e in events if e["type"] in ("bump", "chain_bump")]
        assert len(bump_events) >= 1

    def test_dash_all_four_directions(self):
        """Dash works north, south, east, west."""
        for direction, dx, dy in [
            ("north", 0, -2), ("south", 0, 2),
            ("east", 2, 0), ("west", -2, 0),
        ]:
            bot = make_bot(x=5, y=5)
            actions = {bot.emoji: ("dash", direction)}
            resolve_movement([bot], actions, grid_size=10, all_bots=[bot])
            assert bot.x == 5 + dx, f"Failed for {direction}: x"
            assert bot.y == 5 + dy, f"Failed for {direction}: y"
