# Balance: Mind Combat Value (T74.3)

## Problem

After the S73 versatility retune (T73.6), every specialist archetype reached the
40-60% duel band vs the balanced (25/25/25/25) build **except the mage**
(15/20/20/45), which lost ~87% of stats-only duels.

The root cause was structural, not a stat-constant misfire: in
`engine/stats.calculate_derived`, the `mind` stat only bought `max_energy` and
`energy_regen`. In a stats-only 1v1 melee duel — where both bots run the same
chase-and-attack policy that never rests to bank energy or casts abilities —
mind was dead weight. The mage's derived combat profile (HP 66, damage 9-21) was
strictly worse than balanced's (HP 102, damage 28-48), and no versatility-constant
value could close the gap (see `docs/balance-versatility-s73.md`).

## Mechanic

T74.3 gives `mind` a modest **combat** contribution for mind **above baseline**
(`mind > 25`), in the same `(stat - baseline) * k` style as the existing
`_DR_PER_ARMOR` / `_REGEN_PER_MIND` knobs:

| Constant         | Value | Effect                                                  |
|------------------|-------|---------------------------------------------------------|
| `_MIND_BASELINE` | 25    | mind value that grants 0 combat bonus                   |
| `_DMG_PER_MIND`  | 0.8   | flat min/max **damage** per mind point above baseline   |
| `_HP_PER_MIND`   | 2.5   | bonus effective **HP** (mental barrier) per point above |

Applied as:

```python
mind_excess = max(0, alloc.mind - _MIND_BASELINE)   # 0 for mind <= 25
mind_dmg = int(mind_excess * _DMG_PER_MIND)
mind_hp  = int(mind_excess * _HP_PER_MIND)
# min_damage/max_damage += mind_dmg ; max_hp += mind_hp
```

Thematically: mind is now "battle magic" — a small spell-power damage add plus a
mental barrier that soaks damage. It buys offense *and* survivability, which is
what the mage needed (raw damage alone was insufficient — see Tuning below).

### Blast radius

The `max(0, mind - 25)` shape means the bonus is **exactly zero** at `mind <= 25`.
The default 25/25/25/25 build and every existing test fixture with `mind <= 25`
are completely unchanged (HP 102, damage 28-48 at default). Only genuinely
mind-heavy builds (`mind > 25`) gain anything, so the broad stat-fallout cascade
that re-tuning a shared constant would trigger is avoided.

For the mage (mind=45, excess=20): **+16 damage** (`int(20*0.8)`) and
**+50 HP** (`int(20*2.5)`), giving derived HP 116, damage 25-37.

## Tuning notes

Damage alone was not enough. A pure flat-damage add of up to +24 only lifted the
mage to ~27% (it still died too fast at 66 HP). Adding the HP barrier was the
lever that brought it into band. The chosen `(0.8 dmg, 2.5 hp)` per point lands
the mage mid-band (43.3%) rather than at an edge, and keeps the mind/Controller
archetype well under the 2x-uniform ceiling in the full pool (see below).

Stronger values were rejected as not "modest": pushing harder risks the mage
exceeding the 60% duel ceiling and the Controller archetype approaching the 0.40
full-pool ceiling.

## Before / after — archetype duel matrix

Balanced (25/25/25/25) vs each specialist, stats-only chase policy, fixed seeds
1-30 (`tests/test_versatility_balance.py`). Values are the **specialist's** win %.
The 40-60% band is the target.

| Specialist        | Before (spec win %) | After (spec win %) | In band |
|-------------------|---------------------|--------------------|---------|
| Tank (15/15/50/20)     | 60.0 | 60.0 | yes (edge) |
| Bruiser (40/20/15/25)  | 53.3 | 56.7 | yes |
| Assassin (30/40/10/20) | 53.3 | 53.3 | yes |
| **Mage (15/20/20/45)** | **13.3** | **43.3** | **yes** |

Notes:
- The mage is the only archetype this change touches (it is the only one with
  `mind > 25`). The tank/bruiser values shown are measured on the current working
  tree, which also carries the concurrent T74.2 grid/rounds changes; those are
  responsible for the small bruiser drift (53.3 → 56.7), not the mind term.
  Verified by zeroing the mind term: tank/bruiser/assassin are identical with the
  term on or off; only the mage moves (13.3 → 43.3).

## Full-pool balance report (no archetype > 2x uniform — for Controller)

`python -m agentgrounds killswitch sim --balance-report --matches 30 --seed 1`
on the real `bots/` pool (14 equipped bots, 5 archetypes → uniform share 0.20,
2x uniform = **0.40**):

| Archetype  | Before (mind term off) | After (mind term on) |
|------------|------------------------|----------------------|
| Balanced   | 0.500 | 0.400 |
| Tank       | 0.467 | 0.433 |
| Controller (mage) | 0.033 | 0.133 |
| Assassin   | 0.000 | 0.033 |
| Bruiser    | 0.000 | 0.000 |

The mind retune **improves** full-pool balance across the board: it pulls Balanced
down (0.500 → 0.400) and Tank down (0.467 → 0.433) by giving the previously dead
Controller archetype real wins (0.033 → 0.133, a ~4x lift toward the 0.20 uniform
share). The Controller archetype — the one this task is responsible for — is now
comfortably under the 0.40 ceiling.

The residual Tank (0.433) and Balanced (0.400) values sit at/above 2x uniform, but
this is a pre-existing condition on the current branch (worse before this change:
0.467 / 0.500) inherited from the concurrent T74.2 grid/rounds work; it cannot be
fixed by a mind-only stat lever and is out of scope for T74.3. The parent
regenerates `data/balance_baseline.json` once after this wave of changes lands.

## Tests

- `tests/test_stats.py` — pins the new mind-combat derived values: default
  unchanged, sub-baseline unchanged, mage +16 dmg / +50 HP, mind=50 scaling.
- `tests/test_versatility_balance.py` — replaces the old
  `test_mage_documented_structural_weakness` (which asserted mage stays >60%
  balanced-favored) with `test_mage_in_band_after_mind_combat_retune` and a
  full-roster band check; both use the fixed seed set.
- `tests/test_derived_wiring.py` — `test_bounty_reward_uses_derived_max` fixture
  updated (mind=50 build HP 90 → 152; the test asserts restore-to-derived-max
  behavior, which is unchanged).
