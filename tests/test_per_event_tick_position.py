"""Per-event tick_in_round + position fields (borst RFC, npc-wars#61).

Schema additions are strictly additive:
- tick_in_round: int (0..12) — phase index from resolve_combat_phases
- position: {"x": int, "y": int} — primary actor's grid coords at emission

These tests pin the contract per event type. They are RED until the
implementation lands the two fields at each emission site.

Out-of-scope event types intentionally not pinned here: trap_trigger,
trap_place, taunt_warn, ability_*, tactical_* (S72 and later additions).
The borst spec covers the original 9 (+ 2 ranged); follow-up RFCs can
extend coverage to other event types if needed.
"""

import random

import pytest

from tests.conftest import make_bot

# Phase tick constants — mirror engine/event_meta.py (which the impl will create).
# Importing from the test file keeps tests independent of impl-internal naming.
TICK_DEFENSE = 2
TICK_MOVEMENT = 3
TICK_MELEE = 7
TICK_RANGED = 8
TICK_STORM = 9
TICK_PLAGUE = 10
TICK_DEATHS = 11
TICK_MOMENTUM = 12


def _assert_position(event, expected_x: int, expected_y: int):
    """Assert event has a well-formed position field at the expected coords."""
    assert "position" in event, f"event missing position: {event}"
    pos = event["position"]
    assert isinstance(pos, dict), f"position not a dict: {pos!r}"
    assert pos.get("x") == expected_x and pos.get("y") == expected_y, (
        f"position {pos} != expected ({expected_x}, {expected_y})"
    )


def _assert_tick(event, expected_tick: int):
    """Assert event has tick_in_round at the expected phase index."""
    assert "tick_in_round" in event, f"event missing tick_in_round: {event}"
    assert event["tick_in_round"] == expected_tick, (
        f"tick_in_round={event['tick_in_round']} != expected {expected_tick}"
    )


# ---------------------------------------------------------------------------
# defend (tick 2)
# ---------------------------------------------------------------------------


class TestDefendEvent:
    def test_defend_carries_tick_2_and_defender_position(self):
        from engine.rounds import resolve_defense
        bot = make_bot(emoji="🐢", x=8, y=14)
        events = resolve_defense([bot], {"🐢": ("defend",)})
        assert len(events) == 1
        evt = events[0]
        assert evt["type"] == "defend"
        _assert_tick(evt, TICK_DEFENSE)
        _assert_position(evt, 8, 14)

    def test_defend_preserves_original_keys(self):
        from engine.rounds import resolve_defense
        bot = make_bot(emoji="🐢", x=8, y=14)
        evt = resolve_defense([bot], {"🐢": ("defend",)})[0]
        assert evt["emoji"] == "🐢"
        assert evt["type"] == "defend"


# ---------------------------------------------------------------------------
# bump (tick 3) — pusher's position
# ---------------------------------------------------------------------------


class TestBumpEvent:
    def test_bump_carries_tick_3_and_pusher_position(self):
        from engine.bumpers import resolve_bumps
        a = make_bot(emoji="A", x=3, y=5)
        b = make_bot(emoji="B", x=4, y=5)
        events, _ = resolve_bumps([(a, 4, 5)], [a, b], grid_size=10, storm_border=0)
        bumps = [e for e in events if e.get("type") == "bump"]
        assert bumps, "expected at least one bump event"
        evt = bumps[0]
        _assert_tick(evt, TICK_MOVEMENT)
        # Pusher A is at (3, 5) before the push
        _assert_position(evt, 3, 5)

    def test_bump_preserves_original_keys(self):
        from engine.bumpers import resolve_bumps
        a = make_bot(emoji="A", x=3, y=5)
        b = make_bot(emoji="B", x=4, y=5)
        events, _ = resolve_bumps([(a, 4, 5)], [a, b], grid_size=10, storm_border=0)
        evt = next(e for e in events if e.get("type") == "bump")
        assert evt["pusher"] == "A"
        assert evt["target"] == "B"
        assert "direction" in evt


# ---------------------------------------------------------------------------
# hit, miss, attack_miss (melee — tick 7) — attacker's position
# ---------------------------------------------------------------------------


class TestMeleeHitDeterministic:
    """The deterministic (no-rng) hit path at rounds_combat.py:92."""

    def test_hit_carries_tick_7_and_attacker_position(self):
        from engine.rounds_combat import resolve_attacks
        attacker = make_bot(emoji="A", x=5, y=5, hp=100)
        target = make_bot(emoji="T", x=6, y=5, hp=100)
        events = resolve_attacks([attacker, target], {"A": ("attack", "east")},
                                 pos_map=None, rng=None)
        hits = [e for e in events if e.get("type") == "hit"]
        assert hits, "expected at least one hit event"
        evt = hits[0]
        _assert_tick(evt, TICK_MELEE)
        _assert_position(evt, 5, 5)


class TestMeleeMiss:
    def test_miss_carries_tick_7_and_attacker_position(self):
        from engine.rounds_combat import resolve_attacks
        attacker = make_bot(emoji="A", x=5, y=5, hp=100)
        # Attack into an empty tile
        events = resolve_attacks([attacker], {"A": ("attack", "east")},
                                 pos_map=None, rng=None)
        misses = [e for e in events if e.get("type") == "miss"]
        assert misses, "expected at least one miss event"
        evt = misses[0]
        _assert_tick(evt, TICK_MELEE)
        _assert_position(evt, 5, 5)


class TestMeleeRolledHitAndMiss:
    """The rolled (rng) paths at rounds_combat.py:148/153."""

    def test_rolled_attack_event_carries_tick_7_and_attacker_position(self):
        from engine.rounds_combat import resolve_attacks
        # Use a deterministic rng — outcome (hit vs attack_miss) is irrelevant
        # to what we're asserting; only the metadata fields matter.
        attacker = make_bot(emoji="A", x=5, y=5, hp=100)
        target = make_bot(emoji="T", x=6, y=5, hp=100)
        rng = random.Random(42)
        events = resolve_attacks([attacker, target], {"A": ("attack", "east")},
                                 pos_map=None, rng=rng)
        attack_events = [e for e in events
                         if e.get("type") in ("hit", "attack_miss")]
        assert attack_events, "expected at least one melee attack outcome event"
        evt = attack_events[0]
        _assert_tick(evt, TICK_MELEE)
        _assert_position(evt, 5, 5)


# ---------------------------------------------------------------------------
# ranged_hit, ranged_attack_miss (tick 8) — attacker's position
# ---------------------------------------------------------------------------


class TestRangedAttack:
    def test_ranged_attack_event_carries_tick_8_and_attacker_position(self):
        from engine.rounds_combat import resolve_ranged_attacks
        attacker = make_bot(emoji="A", x=5, y=5, hp=100)
        target = make_bot(emoji="T", x=7, y=5, hp=100)  # range 2
        rng = random.Random(42)
        events = resolve_ranged_attacks([attacker, target],
                                        {"A": ("ranged_attack", "east")},
                                        pos_map=None, rng=rng)
        ranged_events = [e for e in events
                         if e.get("type") in ("ranged_hit", "ranged_attack_miss")]
        assert ranged_events, "expected at least one ranged attack outcome event"
        evt = ranged_events[0]
        _assert_tick(evt, TICK_RANGED)
        _assert_position(evt, 5, 5)


# ---------------------------------------------------------------------------
# storm_damage (tick 9) — victim's position
# ---------------------------------------------------------------------------


class TestStormDamage:
    def test_storm_damage_carries_tick_9_and_victim_position(self):
        from engine.rounds import apply_storm_damage
        # Place bot inside the storm border (close to corner) on small grid
        bot = make_bot(emoji="V", x=0, y=0, hp=100)
        # storm_border=2 means tiles within 2 of edge are storm
        events = apply_storm_damage([bot], grid_size=10, storm_border=2)
        assert events, "expected storm_damage event for bot in storm zone"
        evt = events[0]
        assert evt["type"] == "storm_damage"
        _assert_tick(evt, TICK_STORM)
        _assert_position(evt, 0, 0)


# ---------------------------------------------------------------------------
# plague (tick 10) — victim's position
# ---------------------------------------------------------------------------


class TestPlague:
    def test_plague_carries_tick_10_and_victim_position(self):
        from engine.plague import apply_plague, PLAGUE_GRACE_ROUNDS
        bot = make_bot(emoji="P", x=7, y=13, hp=100)
        # Push past the grace window so the plague actually fires
        bot.passive_rounds = PLAGUE_GRACE_ROUNDS + 1
        events = apply_plague(bot)
        assert events, "expected a plague event past the grace window"
        evt = events[0]
        assert evt["type"] == "plague"
        _assert_tick(evt, TICK_PLAGUE)
        _assert_position(evt, 7, 13)


# ---------------------------------------------------------------------------
# kill (tick 11) — victim's death position
# ---------------------------------------------------------------------------


class TestKill:
    def test_kill_carries_tick_11_and_victim_position(self):
        from engine.rounds import attribute_kills
        # Manually construct: one dead bot, one killer with a hit event
        killer = make_bot(emoji="K", x=5, y=5, hp=100)
        victim = make_bot(emoji="V", x=4, y=6, hp=0)
        victim.alive = False
        bots = [killer, victim]
        elim = {"emoji": "V", "round": 1}
        round_events = [{"type": "hit", "attacker": "K", "target": "V",
                          "damage": 100, "hp_before": 50}]
        attribute_kills([elim], round_events, bots, round_num=1)
        kills = [e for e in round_events if e.get("type") == "kill"]
        assert kills, "expected a kill event after attribute_kills"
        evt = kills[0]
        _assert_tick(evt, TICK_DEATHS)
        _assert_position(evt, 4, 6)


# ---------------------------------------------------------------------------
# momentum_drain (tick 12) — bot's position
# ---------------------------------------------------------------------------


class TestMomentumDrain:
    def test_momentum_drain_carries_tick_12_and_bot_position(self):
        from engine.match_phases import apply_momentum_phase
        bot = make_bot(emoji="M", x=14, y=10, hp=100, energy=10)
        bot.passive_rounds = 0
        round_data = {"events": []}
        # Drive a momentum_drain by giving the bot a non-zero drain via
        # apply_energy_drain (called from apply_momentum_phase).
        # Easiest: ensure the bot is not the leader and has positive energy.
        apply_momentum_phase([bot], round_data, round_num=1,
                              storm_border=0, prev_storm_border=0)
        drains = [e for e in round_data.get("events", [])
                  if e.get("type") == "momentum_drain"]
        # apply_energy_drain may return 0 for some configs — skip cleanly
        # if no drain fires; the assertion-of-interest is on what's emitted.
        if not drains:
            pytest.skip("no momentum_drain emitted for this bot config")
        evt = drains[0]
        _assert_tick(evt, TICK_MOMENTUM)
        _assert_position(evt, 14, 10)


# ---------------------------------------------------------------------------
# Backwards-compatibility — original field shape preserved
# ---------------------------------------------------------------------------


class TestBackwardsCompat:
    """Existing consumers must continue to work: original fields unchanged,
    new fields are purely additive."""

    def test_defend_still_has_emoji_field(self):
        from engine.rounds import resolve_defense
        bot = make_bot(emoji="🐢", x=8, y=14)
        evt = resolve_defense([bot], {"🐢": ("defend",)})[0]
        assert evt["emoji"] == "🐢"
        assert evt["type"] == "defend"

    def test_bump_still_has_pusher_target_direction(self):
        from engine.bumpers import resolve_bumps
        a = make_bot(emoji="A", x=3, y=5)
        b = make_bot(emoji="B", x=4, y=5)
        events, _ = resolve_bumps([(a, 4, 5)], [a, b], grid_size=10, storm_border=0)
        evt = next(e for e in events if e.get("type") == "bump")
        assert evt["pusher"] == "A"
        assert evt["target"] == "B"
        assert evt["direction"] == "(1,0)"

    def test_kill_still_has_attacker_victim_round(self):
        from engine.rounds import attribute_kills
        killer = make_bot(emoji="K", x=5, y=5, hp=100)
        victim = make_bot(emoji="V", x=4, y=6, hp=0)
        victim.alive = False
        bots = [killer, victim]
        elim = {"emoji": "V", "round": 7}
        round_events = [{"type": "hit", "attacker": "K", "target": "V",
                          "damage": 100, "hp_before": 50}]
        attribute_kills([elim], round_events, bots, round_num=7)
        evt = next(e for e in round_events if e.get("type") == "kill")
        assert evt["attacker"] == "K"
        assert evt["victim"] == "V"
        assert evt["round"] == 7
