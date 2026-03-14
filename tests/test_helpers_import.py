"""Import smoke tests for npcwars package wiring."""

from __future__ import annotations


# --- Direct imports from npcwars.helpers ---


def test_import_me_from_helpers():
    from npcwars.helpers import Me

    assert Me is not None


def test_import_enemies_from_helpers():
    from npcwars.helpers import Enemies

    assert Enemies is not None


def test_import_storm_from_helpers():
    from npcwars.helpers import Storm

    assert Storm is not None


# --- Re-exports from npcwars top-level ---


def test_import_me_from_top_level():
    from npcwars import Me

    assert Me is not None


def test_import_enemies_from_top_level():
    from npcwars import Enemies

    assert Enemies is not None


def test_import_storm_from_top_level():
    from npcwars import Storm

    assert Storm is not None


def test_import_all_from_top_level():
    from npcwars import Enemies, Me, Storm

    assert Me is not None
    assert Enemies is not None
    assert Storm is not None


def test_import_helpers_module():
    from npcwars import helpers

    assert hasattr(helpers, "Me")
    assert hasattr(helpers, "Enemies")
    assert hasattr(helpers, "Storm")


def test_reexports_are_same_objects():
    """Top-level re-exports should be the exact same class objects."""
    from npcwars import Enemies as TopEnemies
    from npcwars import Me as TopMe
    from npcwars import Storm as TopStorm
    from npcwars.helpers import Enemies, Me, Storm

    assert TopMe is Me
    assert TopEnemies is Enemies
    assert TopStorm is Storm


# --- Preset imports ---


def test_import_generate_preset():
    from npcwars.presets import generate_preset

    assert callable(generate_preset)


def test_import_preset_names():
    from npcwars.presets import PRESET_NAMES

    assert isinstance(PRESET_NAMES, tuple)
    assert len(PRESET_NAMES) > 0


# --- Callability with mock state ---


_MOCK_STATE: dict = {
    "me": {
        "x": 5,
        "y": 5,
        "hp": 100,
        "energy": 50,
        "attack_power": 10,
        "defense": 5,
    },
    "enemies": [
        {"name": "bot_a", "x": 6, "y": 5, "hp": 80},
    ],
    "grid_size": 20,
    "storm_border": 2,
    "round": 3,
}


def test_me_callable():
    from npcwars import Me

    me = Me(_MOCK_STATE)
    assert me.hp == 100
    assert me.x == 5


def test_enemies_callable():
    from npcwars import Enemies

    foes = Enemies(_MOCK_STATE)
    assert foes.count == 1


def test_storm_callable():
    from npcwars import Storm

    storm = Storm(_MOCK_STATE)
    assert storm.active is True
