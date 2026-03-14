"""Tests for bots/example_vibes.py — Cognify vibes DSL bot."""

import importlib.util
import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BOT_PATH = os.path.join(_PROJECT_ROOT, "bots", "example_vibes.py")


def _load_bot():
    """Load the example_vibes bot module."""
    spec = importlib.util.spec_from_file_location("example_vibes", _BOT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _make_state(
    me_x=5, me_y=5, me_hp=100, me_energy=100,
    enemies=None, grid_size=10, storm_border=0, rnd=1,
):
    """Build a mock state dict."""
    return {
        "me": {
            "x": me_x, "y": me_y, "hp": me_hp, "energy": me_energy,
            "attack_power": 15, "defense": 0,
        },
        "enemies": enemies or [],
        "round": rnd,
        "grid_size": grid_size,
        "storm_border": storm_border,
    }


# --- Attribute tests ---

class TestBotAttributes:
    def test_has_bot_name(self):
        mod = _load_bot()
        assert mod.BOT_NAME == "Cognify"

    def test_has_bot_emoji(self):
        mod = _load_bot()
        assert mod.BOT_EMOJI == "\U0001f9e0"

    def test_has_decide_callable(self):
        mod = _load_bot()
        assert callable(mod.decide)

    def test_has_bot_author(self):
        mod = _load_bot()
        assert mod.BOT_AUTHOR == "kevin"


# --- Decision tests ---

class TestStormEscape:
    """P0: flee storm when in danger."""

    def test_flees_storm_when_in_storm_zone(self):
        state = _make_state(me_x=0, me_y=0, storm_border=2, grid_size=10)
        mod = _load_bot()
        action = mod.decide(state)
        assert action[0] == "move", "Should move to flee storm"

    def test_flees_storm_even_with_adjacent_enemy(self):
        enemies = [{"name": "Foe", "emoji": "X", "x": 1, "y": 0, "hp": 10}]
        state = _make_state(me_x=0, me_y=0, storm_border=2, enemies=enemies)
        mod = _load_bot()
        action = mod.decide(state)
        assert action[0] == "move", "Storm escape overrides attack"


class TestEnergyCrisis:
    """P1: rest when low energy and no killable adjacent."""

    def test_rests_when_low_energy_no_kills(self):
        enemies = [{"name": "Foe", "emoji": "X", "x": 8, "y": 8, "hp": 80}]
        state = _make_state(me_energy=10, enemies=enemies)
        mod = _load_bot()
        action = mod.decide(state)
        assert action == ("rest",)


class TestFinishKills:
    """P2: attack killable adjacent enemies."""

    def test_attacks_killable_adjacent(self):
        enemies = [{"name": "Weak", "emoji": "X", "x": 6, "y": 5, "hp": 10}]
        state = _make_state(enemies=enemies)
        mod = _load_bot()
        action = mod.decide(state)
        assert action[0] == "attack"

    def test_picks_lowest_hp_killable(self):
        enemies = [
            {"name": "A", "emoji": "X", "x": 6, "y": 5, "hp": 15},
            {"name": "B", "emoji": "X", "x": 4, "y": 5, "hp": 5},
        ]
        state = _make_state(enemies=enemies)
        mod = _load_bot()
        action = mod.decide(state)
        # Should attack toward B (west) since B has lower hp
        assert action == ("attack", "west")


class TestDefendOrCounter:
    """P3: defend or counter adjacent threats."""

    def test_defends_when_low_hp(self):
        enemies = [{"name": "Foe", "emoji": "X", "x": 6, "y": 5, "hp": 80}]
        state = _make_state(me_hp=30, enemies=enemies)
        mod = _load_bot()
        action = mod.decide(state)
        assert action == ("defend",)

    def test_defends_when_outnumbered(self):
        enemies = [
            {"name": "A", "emoji": "X", "x": 6, "y": 5, "hp": 80},
            {"name": "B", "emoji": "X", "x": 4, "y": 5, "hp": 80},
        ]
        state = _make_state(me_hp=100, enemies=enemies)
        mod = _load_bot()
        action = mod.decide(state)
        assert action == ("defend",)

    def test_attacks_weak_adjacent_when_healthy(self):
        enemies = [{"name": "Foe", "emoji": "X", "x": 6, "y": 5, "hp": 40}]
        state = _make_state(me_hp=100, enemies=enemies)
        mod = _load_bot()
        action = mod.decide(state)
        assert action[0] == "attack"


class TestRestWhenSafe:
    """P4: rest when safe and low energy."""

    def test_rests_when_low_energy_no_adjacent(self):
        enemies = [{"name": "Foe", "emoji": "X", "x": 9, "y": 9, "hp": 80}]
        state = _make_state(me_energy=20, enemies=enemies)
        mod = _load_bot()
        action = mod.decide(state)
        assert action == ("rest",)


class TestChaseWounded:
    """P5: chase wounded enemies when healthy."""

    def test_chases_nearby_wounded(self):
        enemies = [{"name": "Hurt", "emoji": "X", "x": 8, "y": 5, "hp": 30}]
        state = _make_state(me_hp=80, me_energy=50, enemies=enemies)
        mod = _load_bot()
        action = mod.decide(state)
        assert action[0] == "move"
        assert action[1] == "east"


class TestDriftCenter:
    """P6: drift toward center as default."""

    def test_drifts_center_when_nothing_else(self):
        state = _make_state(me_x=0, me_y=0, me_hp=100, me_energy=100)
        mod = _load_bot()
        action = mod.decide(state)
        assert action[0] == "move"


class TestValidateBot:
    """Bot passes the validate_bot script."""

    def test_validate_bot_passes(self):
        if _PROJECT_ROOT not in sys.path:
            sys.path.insert(0, _PROJECT_ROOT)
        from scripts.validate_bot import validate_bot
        ok, errors = validate_bot(_BOT_PATH)
        assert ok, f"validate_bot failed: {errors}"
