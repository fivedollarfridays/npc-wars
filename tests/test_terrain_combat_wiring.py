"""Tests for terrain combat wiring into rounds_combat and rounds (T37.3)."""

from __future__ import annotations

import random

from tests.conftest import make_bot
from engine.terrain import TerrainMap, OPEN, WALL, WATER, HIGH_GROUND, COVER
from engine.rounds_combat import resolve_attacks, resolve_ranged_attacks
from engine.rounds import apply_energy_and_rest
from engine.combat import REST_HEAL


# ── Helpers ──────────────────────────────────────────────────────────


def _make_map(tile: str, size: int = 10) -> TerrainMap:
    """Build a uniform terrain map filled with *tile*."""
    tiles = [[tile] * size for _ in range(size)]
    return TerrainMap("test", size, tiles)


def _make_los_blocked_map(size: int = 10) -> TerrainMap:
    """Map with wall at x=4 to block ranged LoS east-west."""
    tiles = [[OPEN] * size for _ in range(size)]
    for y in range(size):
        tiles[y][4] = WALL
    return TerrainMap("wall_test", size, tiles)


# ── Melee: terrain to-hit and damage wiring ──────────────────────────


def test_melee_high_ground_increases_to_hit() -> None:
    """Attacker on high_ground gets +2 to modifier in CombatResult."""
    attacker = make_bot(emoji="A", hp=100, energy=100, x=2, y=3)
    target = make_bot(emoji="T", hp=100, energy=100, x=3, y=3)
    actions = {"A": ("attack", "east"), "T": ("rest",)}
    rng = random.Random(42)
    terrain = _make_map(HIGH_GROUND)

    events_terrain = resolve_attacks(
        [attacker, target], actions, rng=rng, terrain=terrain,
    )

    # Reset for baseline
    attacker2 = make_bot(emoji="A", hp=100, energy=100, x=2, y=3)
    target2 = make_bot(emoji="T", hp=100, energy=100, x=3, y=3)
    rng2 = random.Random(42)
    events_no_terrain = resolve_attacks(
        [attacker2, target2], actions, rng=rng2,
    )

    evt_t = events_terrain[0]
    evt_n = events_no_terrain[0]
    # With terrain, modifier should be 2 higher
    assert evt_t["modifier"] == evt_n["modifier"] + 2


def test_melee_water_decreases_to_hit() -> None:
    """Attacker on water gets -2 to modifier."""
    attacker = make_bot(emoji="A", hp=100, energy=100, x=2, y=3)
    target = make_bot(emoji="T", hp=100, energy=100, x=3, y=3)
    actions = {"A": ("attack", "east"), "T": ("rest",)}
    rng = random.Random(42)
    terrain = _make_map(WATER)

    events_terrain = resolve_attacks(
        [attacker, target], actions, rng=rng, terrain=terrain,
    )

    attacker2 = make_bot(emoji="A", hp=100, energy=100, x=2, y=3)
    target2 = make_bot(emoji="T", hp=100, energy=100, x=3, y=3)
    rng2 = random.Random(42)
    events_no_terrain = resolve_attacks(
        [attacker2, target2], actions, rng=rng2,
    )

    evt_t = events_terrain[0]
    evt_n = events_no_terrain[0]
    assert evt_t["modifier"] == evt_n["modifier"] - 2


def test_melee_cover_increases_defender_ac() -> None:
    """Defender on cover gets +3 AC."""
    attacker = make_bot(emoji="A", hp=100, energy=100, x=2, y=3)
    target = make_bot(emoji="T", hp=100, energy=100, x=3, y=3)
    actions = {"A": ("attack", "east"), "T": ("rest",)}

    # Target on cover
    tiles = [[OPEN] * 10 for _ in range(10)]
    tiles[3][3] = COVER  # target position
    terrain = TerrainMap("cover_test", 10, tiles)

    rng = random.Random(42)
    events_terrain = resolve_attacks(
        [attacker, target], actions, rng=rng, terrain=terrain,
    )

    attacker2 = make_bot(emoji="A", hp=100, energy=100, x=2, y=3)
    target2 = make_bot(emoji="T", hp=100, energy=100, x=3, y=3)
    rng2 = random.Random(42)
    events_no_terrain = resolve_attacks(
        [attacker2, target2], actions, rng=rng2,
    )

    evt_t = events_terrain[0]
    evt_n = events_no_terrain[0]
    assert evt_t["ac"] == evt_n["ac"] + 3


# ── Ranged: LoS blocking ────────────────────────────────────────────


def test_ranged_wall_blocks_los() -> None:
    """Wall between attacker and target generates ranged_miss event."""
    attacker = make_bot(emoji="A", hp=100, energy=100, x=3, y=3)
    target = make_bot(emoji="T", hp=100, energy=100, x=5, y=3)
    actions = {"A": ("ranged_attack", "east"), "T": ("rest",)}
    terrain = _make_los_blocked_map()  # wall at x=4

    rng = random.Random(42)
    events = resolve_ranged_attacks(
        [attacker, target], actions, rng=rng, terrain=terrain,
    )
    assert len(events) == 1
    assert events[0]["type"] == "terrain_blocked"


def test_ranged_no_wall_succeeds() -> None:
    """Without wall, ranged attack resolves normally."""
    attacker = make_bot(emoji="A", hp=100, energy=100, x=3, y=3)
    target = make_bot(emoji="T", hp=100, energy=100, x=5, y=3)
    actions = {"A": ("ranged_attack", "east"), "T": ("rest",)}
    terrain = _make_map(OPEN)

    rng = random.Random(42)
    events = resolve_ranged_attacks(
        [attacker, target], actions, rng=rng, terrain=terrain,
    )
    assert len(events) == 1
    assert events[0]["type"] in ("ranged_hit", "ranged_attack_miss")


# ── No terrain (backward compat) ────────────────────────────────────


def test_resolve_attacks_no_terrain_backward_compat() -> None:
    """resolve_attacks with no terrain parameter works as before."""
    attacker = make_bot(emoji="A", hp=100, energy=100, x=2, y=3)
    target = make_bot(emoji="T", hp=100, energy=100, x=3, y=3)
    actions = {"A": ("attack", "east"), "T": ("rest",)}
    rng = random.Random(42)

    events = resolve_attacks([attacker, target], actions, rng=rng)
    assert len(events) == 1
    assert events[0]["type"] in ("hit", "attack_miss")


def test_resolve_ranged_no_terrain_backward_compat() -> None:
    """resolve_ranged_attacks with no terrain parameter works as before."""
    attacker = make_bot(emoji="A", hp=100, energy=100, x=3, y=3)
    target = make_bot(emoji="T", hp=100, energy=100, x=5, y=3)
    actions = {"A": ("ranged_attack", "east"), "T": ("rest",)}
    rng = random.Random(42)

    events = resolve_ranged_attacks([attacker, target], actions, rng=rng)
    assert len(events) == 1
    assert events[0]["type"] in ("ranged_hit", "ranged_attack_miss")


# ── Rest healing: water blocks ───────────────────────────────────────


def test_rest_on_water_no_hp_heal() -> None:
    """Bot resting on water doesn't heal HP."""
    bot = make_bot(emoji="B", hp=50, energy=50, x=2, y=2)
    bot.hp = 50.0
    actions = {"B": ("rest",)}
    terrain = _make_map(WATER)

    apply_energy_and_rest([bot], actions, set(), terrain=terrain)

    # Energy should still restore, but HP should NOT heal
    assert bot.hp == 50.0


def test_rest_on_open_heals_normally() -> None:
    """Bot resting on open terrain heals HP normally."""
    bot = make_bot(emoji="B", hp=50, energy=50, x=2, y=2)
    bot.hp = 50.0
    actions = {"B": ("rest",)}
    terrain = _make_map(OPEN)

    apply_energy_and_rest([bot], actions, set(), terrain=terrain)

    assert bot.hp == 50.0 + REST_HEAL
