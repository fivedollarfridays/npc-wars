"""Tests for npcwars.helpers — Storm class."""


def _make_state(mx=5, my=5, grid_size=10, storm_border=0):
    return {
        "me": {
            "x": mx, "y": my, "hp": 100, "energy": 100,
            "attack_power": 25, "defense": 0,
            "unlocked_actions": ["attack", "defend", "move", "rest"],
            "line_budget": 50, "win_streak": 0,
        },
        "enemies": [],
        "round": 1,
        "grid_size": grid_size,
        "storm_border": storm_border,
        "bumps_last_round": [],
    }


class TestStormActive:
    def test_active_false_when_no_storm(self):
        from npcwars.helpers import Storm

        s = Storm(_make_state(storm_border=0))
        assert s.active is False

    def test_active_true_when_storm_present(self):
        from npcwars.helpers import Storm

        s = Storm(_make_state(storm_border=2))
        assert s.active is True


class TestStormDanger:
    def test_danger_false_no_storm_center(self):
        from npcwars.helpers import Storm

        s = Storm(_make_state(mx=5, my=5, storm_border=0))
        assert s.danger is False

    def test_danger_true_when_in_storm(self):
        from npcwars.helpers import Storm

        # storm_border=2 means x<2 is storm; position x=1 is in storm
        s = Storm(_make_state(mx=1, my=5, storm_border=2))
        assert s.danger is True

    def test_danger_true_one_tile_from_storm_edge(self):
        from npcwars.helpers import Storm

        # storm_border=2, so storm covers x<2. Position x=2 is safe for
        # border=2, but _is_in_storm(2,5,10,3) with border+1=3 catches x<3.
        s = Storm(_make_state(mx=2, my=5, storm_border=2))
        assert s.danger is True

    def test_danger_false_safely_in_center_during_storm(self):
        from npcwars.helpers import Storm

        s = Storm(_make_state(mx=5, my=5, storm_border=2))
        assert s.danger is False


class TestStormBorder:
    def test_border_returns_raw_value(self):
        from npcwars.helpers import Storm

        s = Storm(_make_state(storm_border=3))
        assert s.border == 3

    def test_border_zero(self):
        from npcwars.helpers import Storm

        s = Storm(_make_state(storm_border=0))
        assert s.border == 0


class TestStormSafeZoneCenter:
    def test_safe_zone_center_grid_10(self):
        from npcwars.helpers import Storm

        s = Storm(_make_state(grid_size=10))
        assert s.safe_zone_center() == (5, 5)

    def test_safe_zone_center_grid_20(self):
        from npcwars.helpers import Storm

        s = Storm(_make_state(grid_size=20))
        assert s.safe_zone_center() == (10, 10)


class TestStormInAll:
    def test_storm_in_all(self):
        from npcwars.helpers import __all__

        assert "Storm" in __all__
