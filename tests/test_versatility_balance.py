"""Deterministic archetype-duel band test for the versatility retune (T73.6)
and the mind-combat retune (T74.3).

Pins the measured result that, after retuning the versatility bonus
(engine.stats._VERSATILITY_HP_MAX / _DMG_BONUS), each *combat* specialist
archetype (tank, bruiser, assassin) lands inside a 40-60% balanced-win band
head-to-head vs the 25/25/25/25 build, with a fixed seed set.

T74.3 gave the `mind` stat a modest combat contribution
(engine.stats._DMG_PER_MIND / _HP_PER_MIND, applied to mind > 25). The mage
archetype (15/20/20/45) — previously a documented structural weakness because
mind only bought non-combat energy in a stats-only duel — now also lands inside
the 40-60% band. See docs/balance-mind-s74.md for the before/after matrix.
"""

from __future__ import annotations

from engine.game import run_match
from engine.stats import StatAllocation

# Fixed archetype allocations (must match docs/balance-versatility-s73.md).
BALANCED = StatAllocation(25, 25, 25, 25)
SPECIALISTS = {
    "tank": StatAllocation(15, 15, 50, 20),
    "bruiser": StatAllocation(40, 20, 15, 25),
    "assassin": StatAllocation(30, 40, 10, 20),
}
MAGE = StatAllocation(15, 20, 20, 45)

# Fixed seed set — determinism is part of the contract.
SEEDS = tuple(range(1, 31))


def _chase(state: dict) -> tuple:
    """Stats-only melee policy: close on nearest enemy, attack when adjacent.

    Identical for both sides so the *stat allocation* decides the duel, not
    the policy. Never rests/casts, so mind's energy value is not exercised.
    """
    me = state["me"]
    enemies = state["enemies"]
    if not enemies:
        return ("rest",)
    target = min(enemies, key=lambda e: abs(e["x"] - me["x"]) + abs(e["y"] - me["y"]))
    dx = target["x"] - me["x"]
    dy = target["y"] - me["y"]
    if abs(dx) + abs(dy) == 1:
        if dx == 1:
            return ("attack", "east")
        if dx == -1:
            return ("attack", "west")
        if dy == 1:
            return ("attack", "south")
        return ("attack", "north")
    if abs(dx) >= abs(dy):
        return ("move", "east") if dx > 0 else ("move", "west")
    return ("move", "south") if dy > 0 else ("move", "north")


def _balanced_win_pct(spec_alloc: StatAllocation) -> float:
    """Return balanced's win percentage vs a specialist over the fixed seeds."""
    wins = 0
    for seed in SEEDS:
        cfgs = [
            {"name": "Bal", "emoji": "A", "bio": "", "author": "t",
             "decide_func": _chase, "stat_allocation": BALANCED},
            {"name": "Spec", "emoji": "C", "bio": "", "author": "t",
             "decide_func": _chase, "stat_allocation": spec_alloc},
        ]
        md = run_match(cfgs, match_id=seed, seed=seed)
        if md.get("winner") == "A":
            wins += 1
    return 100.0 * wins / len(SEEDS)


def test_combat_specialists_in_band() -> None:
    """Each combat specialist keeps balanced inside the 40-60% win band."""
    for name, alloc in SPECIALISTS.items():
        pct = _balanced_win_pct(alloc)
        assert 40.0 <= pct <= 60.0, f"{name}: balanced won {pct:.1f}% (out of 40-60 band)"


def test_duel_band_is_deterministic() -> None:
    """Re-running the sweep with the same seeds yields identical results."""
    first = {name: _balanced_win_pct(a) for name, a in SPECIALISTS.items()}
    second = {name: _balanced_win_pct(a) for name, a in SPECIALISTS.items()}
    assert first == second


def test_balanced_no_longer_dominant() -> None:
    """The retune removed strict dominance: balanced no longer wins >60% vs all."""
    # Pre-retune, balanced won 70-87% vs every specialist. Post-retune it must
    # not exceed 60% vs any combat specialist.
    assert all(_balanced_win_pct(a) <= 60.0 for a in SPECIALISTS.values())


def test_mage_in_band_after_mind_combat_retune() -> None:
    """Mage now lands in the 40-60% balanced-win band (T74.3 mind-combat value).

    Before T74.3, mind only bought non-combat energy, so balanced won ~87% of
    mage duels (mage was a documented structural weakness). Adding a modest
    mind-fueled damage + effective-HP bonus (engine.stats._DMG_PER_MIND /
    _HP_PER_MIND, mind > 25) brings the mage into the same 40-60% band as the
    combat specialists. Pinned with the fixed SEEDS set so a future regression
    in either the mind constants or the combat model surfaces here.
    """
    pct = _balanced_win_pct(MAGE)
    assert 40.0 <= pct <= 60.0, f"mage: balanced won {pct:.1f}% (out of 40-60 band)"


def test_all_archetypes_including_mage_in_band() -> None:
    """The full archetype roster (combat specialists + mage) is in band.

    Sanity check that the mind retune did not knock any combat specialist out of
    band while bringing the mage in.
    """
    all_specs = {**SPECIALISTS, "mage": MAGE}
    for name, alloc in all_specs.items():
        pct = _balanced_win_pct(alloc)
        assert 40.0 <= pct <= 60.0, f"{name}: balanced won {pct:.1f}% (out of band)"
