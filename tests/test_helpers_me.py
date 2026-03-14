"""Tests for npcwars.helpers — Me class with movement & defense methods."""

def _make_state(**overrides):
    """Build a minimal state dict for testing."""
    me = {
        "x": 5, "y": 5, "hp": 100, "energy": 100,
        "attack_power": 25, "defense": 0,
        "unlocked_actions": ["attack", "defend", "move", "rest"],
        "line_budget": 50, "win_streak": 0,
    }
    me.update(overrides.pop("me_overrides", {}))
    state = {
        "me": me,
        "enemies": [],
        "round": 1,
        "grid_size": 10,
        "storm_border": 0,
        "bumps_last_round": [],
    }
    state.update(overrides)
    return state


# --- _direction_toward ---

class TestDirectionToward:
    def test_east(self):
        from npcwars._util import direction_toward as _direction_toward
        assert _direction_toward(0, 0, 3, 0) == "east"

    def test_west(self):
        from npcwars._util import direction_toward as _direction_toward
        assert _direction_toward(5, 5, 2, 5) == "west"

    def test_north(self):
        from npcwars._util import direction_toward as _direction_toward
        assert _direction_toward(5, 5, 5, 2) == "north"

    def test_south(self):
        from npcwars._util import direction_toward as _direction_toward
        assert _direction_toward(5, 5, 5, 8) == "south"

    def test_tie_breaks_x_axis(self):
        """When |dx| == |dy|, prefer x-axis (east/west)."""
        from npcwars._util import direction_toward as _direction_toward
        assert _direction_toward(0, 0, 3, 3) == "east"
        assert _direction_toward(3, 3, 0, 0) == "west"

    def test_same_position_returns_north(self):
        from npcwars._util import direction_toward as _direction_toward
        assert _direction_toward(5, 5, 5, 5) == "north"


# --- _is_in_storm ---

class TestIsInStorm:
    def test_no_storm(self):
        from npcwars._util import is_in_storm as _is_in_storm
        assert _is_in_storm(0, 0, 10, 0) is False

    def test_in_storm_left_edge(self):
        from npcwars._util import is_in_storm as _is_in_storm
        assert _is_in_storm(0, 5, 10, 2) is True

    def test_in_storm_right_edge(self):
        from npcwars._util import is_in_storm as _is_in_storm
        assert _is_in_storm(8, 5, 10, 2) is True

    def test_in_storm_top_edge(self):
        from npcwars._util import is_in_storm as _is_in_storm
        assert _is_in_storm(5, 1, 10, 2) is True

    def test_in_storm_bottom_edge(self):
        from npcwars._util import is_in_storm as _is_in_storm
        assert _is_in_storm(5, 9, 10, 2) is True

    def test_safe_center(self):
        from npcwars._util import is_in_storm as _is_in_storm
        assert _is_in_storm(5, 5, 10, 2) is False


# --- Me properties ---

class TestMeProperties:
    def test_basic_properties(self):
        from npcwars.helpers import Me
        state = _make_state()
        me = Me(state)
        assert me.x == 5
        assert me.y == 5
        assert me.hp == 100
        assert me.energy == 100
        assert me.attack_power == 25
        assert me.defense == 0

    def test_global_properties(self):
        from npcwars.helpers import Me
        state = _make_state(grid_size=20, storm_border=3, round=7)
        me = Me(state)
        assert me.grid_size == 20
        assert me.storm_border == 3
        assert me.round == 7


# --- Me.rest() and Me.defend() ---

class TestMeSimpleActions:
    def test_rest(self):
        from npcwars.helpers import Me
        me = Me(_make_state())
        assert me.rest() == ("rest",)

    def test_defend(self):
        from npcwars.helpers import Me
        me = Me(_make_state())
        assert me.defend() == ("defend",)


# --- Me.flee_storm() and Me.move_toward_center() ---

class TestMeMovementCenter:
    def test_flee_storm_moves_toward_center(self):
        """Bot at (0, 5) on 10x10 grid: center ~(4.5, 4.5), should go east."""
        from npcwars.helpers import Me
        state = _make_state(me_overrides={"x": 0, "y": 5}, storm_border=2)
        me = Me(state)
        assert me.flee_storm() == ("move", "east")

    def test_move_toward_center_from_top(self):
        """Bot at (5, 0) on 10x10 grid: center ~(4.5, 4.5), should go south."""
        from npcwars.helpers import Me
        state = _make_state(me_overrides={"x": 5, "y": 0})
        me = Me(state)
        assert me.move_toward_center() == ("move", "south")

    def test_move_toward_center_at_center(self):
        """Bot already at center returns a valid move tuple."""
        from npcwars.helpers import Me
        state = _make_state(me_overrides={"x": 5, "y": 5})
        me = Me(state)
        result = me.move_toward_center()
        assert result[0] == "move"
        assert result[1] in ("north", "south", "east", "west")


# --- Me.move_toward() ---

class TestMeMoveToward:
    def test_move_toward_enemy_dict(self):
        from npcwars.helpers import Me
        state = _make_state(me_overrides={"x": 2, "y": 2})
        me = Me(state)
        enemy = {"name": "E", "x": 5, "y": 2, "hp": 80}
        assert me.move_toward(enemy) == ("move", "east")

    def test_move_toward_tuple(self):
        from npcwars.helpers import Me
        state = _make_state(me_overrides={"x": 5, "y": 5})
        me = Me(state)
        assert me.move_toward((5, 1)) == ("move", "north")


# --- Me.move_away_from() ---

class TestMeMoveAwayFrom:
    def test_move_away_opposite_direction(self):
        """Enemy east, should flee west."""
        from npcwars.helpers import Me
        state = _make_state(me_overrides={"x": 3, "y": 5})
        me = Me(state)
        enemy = {"x": 7, "y": 5}
        assert me.move_away_from(enemy) == ("move", "west")

    def test_move_away_from_tuple(self):
        """Enemy south, should flee north."""
        from npcwars.helpers import Me
        state = _make_state(me_overrides={"x": 5, "y": 3})
        me = Me(state)
        assert me.move_away_from((5, 8)) == ("move", "north")

    def test_move_away_same_position(self):
        """Same position: direction_toward returns 'north', opposite is 'south'."""
        from npcwars.helpers import Me
        state = _make_state(me_overrides={"x": 5, "y": 5})
        me = Me(state)
        assert me.move_away_from((5, 5)) == ("move", "south")


# --- Me.dist_to() ---

class TestMeDistTo:
    def test_dist_to_dict(self):
        from npcwars.helpers import Me
        me = Me(_make_state(me_overrides={"x": 2, "y": 3}))
        assert me.dist_to({"x": 5, "y": 7}) == 7

    def test_dist_to_tuple(self):
        from npcwars.helpers import Me
        me = Me(_make_state(me_overrides={"x": 0, "y": 0}))
        assert me.dist_to((3, 4)) == 7

    def test_dist_to_same_position(self):
        from npcwars.helpers import Me
        me = Me(_make_state(me_overrides={"x": 5, "y": 5}))
        assert me.dist_to({"x": 5, "y": 5}) == 0


# --- Me.attack() ---

class TestMeAttack:
    def test_attack_east(self):
        from npcwars.helpers import Me
        me = Me(_make_state(me_overrides={"x": 3, "y": 5}))
        assert me.attack({"x": 6, "y": 5}) == ("attack", "east")

    def test_attack_north(self):
        from npcwars.helpers import Me
        me = Me(_make_state(me_overrides={"x": 5, "y": 5}))
        assert me.attack({"x": 5, "y": 2}) == ("attack", "north")

    def test_attack_south(self):
        from npcwars.helpers import Me
        me = Me(_make_state(me_overrides={"x": 5, "y": 5}))
        assert me.attack({"x": 5, "y": 8}) == ("attack", "south")

    def test_attack_west(self):
        from npcwars.helpers import Me
        me = Me(_make_state(me_overrides={"x": 5, "y": 5}))
        assert me.attack({"x": 2, "y": 5}) == ("attack", "west")


# --- Me.adjacent_enemies() ---

class TestMeAdjacentEnemies:
    def test_no_enemies(self):
        from npcwars.helpers import Me
        me = Me(_make_state(me_overrides={"x": 5, "y": 5}, enemies=[]))
        assert me.adjacent_enemies() == []

    def test_one_adjacent_one_far(self):
        from npcwars.helpers import Me
        enemies = [
            {"x": 6, "y": 5, "hp": 50},  # adjacent (dist 1)
            {"x": 8, "y": 5, "hp": 30},  # far (dist 3)
        ]
        me = Me(_make_state(me_overrides={"x": 5, "y": 5}, enemies=enemies))
        adj = me.adjacent_enemies()
        assert len(adj) == 1
        assert adj[0]["x"] == 6

    def test_diagonal_not_adjacent(self):
        """Diagonal neighbor (dist 2) should NOT be adjacent."""
        from npcwars.helpers import Me
        enemies = [{"x": 6, "y": 6, "hp": 50}]
        me = Me(_make_state(me_overrides={"x": 5, "y": 5}, enemies=enemies))
        assert me.adjacent_enemies() == []


# --- Me.nearby_enemies() ---

class TestMeNearbyEnemies:
    def test_nearby_default_radius(self):
        from npcwars.helpers import Me
        enemies = [
            {"x": 6, "y": 5, "hp": 50},  # dist 1
            {"x": 7, "y": 5, "hp": 30},  # dist 2
            {"x": 9, "y": 5, "hp": 10},  # dist 4
        ]
        me = Me(_make_state(me_overrides={"x": 5, "y": 5}, enemies=enemies))
        nearby = me.nearby_enemies()  # default radius=2
        assert len(nearby) == 2

    def test_nearby_custom_radius(self):
        from npcwars.helpers import Me
        enemies = [
            {"x": 6, "y": 5, "hp": 50},  # dist 1
            {"x": 8, "y": 6, "hp": 30},  # dist 4
        ]
        me = Me(_make_state(me_overrides={"x": 5, "y": 5}, enemies=enemies))
        assert len(me.nearby_enemies(3)) == 1
        assert len(me.nearby_enemies(4)) == 2


# --- Me.can_kill_adjacent() ---

class TestMeCanKillAdjacent:
    def test_killable_adjacent(self):
        from npcwars.helpers import Me
        enemies = [{"x": 6, "y": 5, "hp": 20}]
        me = Me(_make_state(
            me_overrides={"x": 5, "y": 5, "attack_power": 25},
            enemies=enemies,
        ))
        assert me.can_kill_adjacent() is True

    def test_not_killable(self):
        from npcwars.helpers import Me
        enemies = [{"x": 6, "y": 5, "hp": 50}]
        me = Me(_make_state(
            me_overrides={"x": 5, "y": 5, "attack_power": 25},
            enemies=enemies,
        ))
        assert me.can_kill_adjacent() is False

    def test_no_adjacent_enemies(self):
        from npcwars.helpers import Me
        enemies = [{"x": 9, "y": 9, "hp": 5}]
        me = Me(_make_state(
            me_overrides={"x": 5, "y": 5, "attack_power": 25},
            enemies=enemies,
        ))
        assert me.can_kill_adjacent() is False


# --- Me.weakest_adjacent() ---

class TestMeWeakestAdjacent:
    def test_returns_weakest(self):
        from npcwars.helpers import Me
        enemies = [
            {"x": 6, "y": 5, "hp": 50},
            {"x": 4, "y": 5, "hp": 20},
        ]
        me = Me(_make_state(me_overrides={"x": 5, "y": 5}, enemies=enemies))
        w = me.weakest_adjacent()
        assert w is not None
        assert w["hp"] == 20

    def test_returns_none_when_no_adjacent(self):
        from npcwars.helpers import Me
        me = Me(_make_state(me_overrides={"x": 5, "y": 5}, enemies=[]))
        assert me.weakest_adjacent() is None


# --- Me.threatened() ---

class TestMeThreatened:
    def test_low_hp_with_adjacent(self):
        from npcwars.helpers import Me
        enemies = [{"x": 6, "y": 5, "hp": 50}]
        me = Me(_make_state(
            me_overrides={"x": 5, "y": 5, "hp": 30},
            enemies=enemies,
        ))
        assert me.threatened() is True

    def test_outnumbered(self):
        from npcwars.helpers import Me
        enemies = [
            {"x": 6, "y": 5, "hp": 50},
            {"x": 4, "y": 5, "hp": 50},
        ]
        me = Me(_make_state(
            me_overrides={"x": 5, "y": 5, "hp": 100},
            enemies=enemies,
        ))
        assert me.threatened() is True

    def test_healthy_single_adjacent(self):
        """High hp with only one adjacent enemy: not threatened."""
        from npcwars.helpers import Me
        enemies = [{"x": 6, "y": 5, "hp": 50}]
        me = Me(_make_state(
            me_overrides={"x": 5, "y": 5, "hp": 100},
            enemies=enemies,
        ))
        assert me.threatened() is False

    def test_no_adjacent_not_threatened(self):
        from npcwars.helpers import Me
        me = Me(_make_state(
            me_overrides={"x": 5, "y": 5, "hp": 10},
            enemies=[],
        ))
        assert me.threatened() is False
