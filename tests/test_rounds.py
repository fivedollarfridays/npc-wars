"""Tests for engine/rounds.py — forced-rest healing timing and position map collisions."""

from tests.conftest import make_bot
from engine.rounds import resolve_decisions, apply_energy_and_rest, resolve_attacks
from engine.combat import REST_HEAL, REST_ENERGY_RESTORE


# ---------------------------------------------------------------------------
# Bug 1: Forced-rest double healing
# ---------------------------------------------------------------------------

def test_forced_rest_heals_same_time_as_explicit_rest():
    """Forced-rest bot should NOT get early healing buffer before storm damage.

    Both forced-rest and explicit-rest bots should receive healing in
    apply_energy_and_rest (Phase 6+7), not during resolve_decisions (Phase 1).
    """
    # Bot A: forced rest (energy=0, so can_act() returns False)
    bot_a = make_bot(name="ForcedRester", emoji="A", hp=50, energy=0, x=0, y=0)
    # Bot B: explicit rest (has energy, decides to rest)
    bot_b = make_bot(name="ExplicitRester", emoji="B", hp=50, energy=100, x=5, y=5)

    alive_bots = [bot_a, bot_b]
    all_bots = [bot_a, bot_b]

    # Phase 1: resolve decisions
    actions, forced_rest, _ = resolve_decisions(alive_bots, all_bots, round_num=1,
                                             grid_size=10, storm_border=0)

    # After Phase 1, forced-rest bot should NOT have been healed yet.
    # If bug exists, bot_a.hp will be 60 (50 + REST_HEAL).
    assert bot_a.hp == 50, (
        f"Forced-rest bot was healed during resolve_decisions (hp={bot_a.hp}), "
        "but healing should only happen in apply_energy_and_rest"
    )


def test_forced_rest_skips_energy_deduction():
    """Forced-rest bot should not get energy deducted for resting."""
    bot = make_bot(name="ForcedRester", emoji="A", hp=50, energy=0, x=5, y=5)
    actions = {bot.emoji: ("rest",)}
    forced_rest = {bot.emoji}

    apply_energy_and_rest([bot], actions, forced_rest)

    # Energy should not go negative — rest cost is 0 anyway, but the bot
    # should be excluded from the deduction loop.
    assert bot.energy >= 0


def test_forced_rest_gets_healing_in_apply_energy_and_rest():
    """After the fix, forced-rest bots should receive healing in apply_energy_and_rest."""
    bot = make_bot(name="ForcedRester", emoji="A", hp=50, energy=0, x=5, y=5)
    actions = {bot.emoji: ("rest",)}
    forced_rest = {bot.emoji}

    apply_energy_and_rest([bot], actions, forced_rest)

    # Forced-rest bot SHOULD get healing here (after fix removes forced_rest exclusion)
    assert bot.hp == 50 + REST_HEAL, (
        f"Forced-rest bot did not get healing in apply_energy_and_rest (hp={bot.hp})"
    )
    assert bot.energy == 0 + REST_ENERGY_RESTORE, (
        f"Forced-rest bot did not get energy restore in apply_energy_and_rest (energy={bot.energy})"
    )


# ---------------------------------------------------------------------------
# Bug 2: Position map collision — two bots on same tile
# ---------------------------------------------------------------------------

def test_two_bots_same_tile_both_targetable():
    """When two bots share a tile and the second one is dead, the first should be hit.

    With buggy dict pos_map, the second bot overwrites the first. If the second
    bot is dead (alive=False), pos_map lookup finds dead bot, the alive check
    fails, and the attack misses — even though a living bot is at that position.
    """
    # Two bots at (3, 3): first alive, second dead
    bot_alive_target = make_bot(name="AliveTarget", emoji="V", hp=100, energy=100, x=3, y=3)
    bot_dead = make_bot(name="DeadBot", emoji="D", hp=0, energy=0, x=3, y=3)
    bot_dead.alive = False

    bot_shooter = make_bot(name="Shooter", emoji="S", hp=100, energy=100, x=2, y=3)

    # alive_bots includes the dead bot in the list for pos_map building
    # (the game passes all bots that were alive at start of round)
    alive_bots = [bot_alive_target, bot_dead, bot_shooter]
    actions = {
        bot_alive_target.emoji: ("defend",),
        bot_dead.emoji: ("nothing",),
        bot_shooter.emoji: ("attack", "east"),  # targets (3, 3)
    }

    events = resolve_attacks(alive_bots, actions)

    # With buggy dict: pos_map[(3,3)] = bot_dead (overwrites bot_alive_target)
    # Attack check: target.alive is False -> miss. But alive target IS there.
    hit_events = [e for e in events if e["type"] == "hit"]
    assert len(hit_events) == 1, (
        f"Expected 1 hit on alive target at (3,3), got events: {events}"
    )
    assert hit_events[0]["target"] == "V"


def test_attack_hits_correct_target_when_stacked():
    """Dead bot at same tile should not block attacks on alive bot behind it.

    With buggy dict pos_map, the dead bot (inserted second) overwrites the alive
    target. Shooter attacks that tile, finds only the dead bot, alive check fails,
    and attack misses. With list-based pos_map, shooter finds the alive target.
    """
    bot_target = make_bot(name="Target", emoji="T", hp=80, energy=100, x=5, y=5)
    bot_dead_blocker = make_bot(name="Blocker", emoji="B", hp=0, energy=0, x=5, y=5)
    bot_dead_blocker.alive = False

    bot_shooter = make_bot(name="Shooter", emoji="S", hp=100, energy=100, x=4, y=5)

    alive_bots = [bot_target, bot_dead_blocker, bot_shooter]
    actions = {
        bot_target.emoji: ("rest",),
        bot_dead_blocker.emoji: ("nothing",),
        bot_shooter.emoji: ("attack", "east"),  # targets (5, 5)
    }

    events = resolve_attacks(alive_bots, actions)

    hit_events = [e for e in events if e["type"] == "hit"]
    assert len(hit_events) == 1, (
        f"Expected hit on T at (5,5) despite dead B at same pos, got: {events}"
    )
    assert hit_events[0]["target"] == "T"
    assert hit_events[0]["attacker"] == "S"
