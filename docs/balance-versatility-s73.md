# Versatility Bonus Retune — T73.6

## Problem

The versatility bonus in `engine/stats.py` rewards balanced (low-variance) stat
allocations with bonus HP and flat damage. The `25/25/25/25` build has variance 0,
so it received the **full** bonus, while every specialist (variance ≥ the cap)
received **none**. The pre-retune values were so large that the balanced build was
strictly dominant:

- Balanced HP = `50 (base) + 25·0.8 (armor) + 75 (versatility) = 145`
- TankBot HP = 90 (no bonus)

Measured archetype duels (balanced vs each specialist, stats-only chase policy,
30 fixed seeds) showed balanced winning **70–87%** vs every specialist — far above
the target 40–60% band.

## Constants: old → new

| Constant | Old | New | Notes |
|----------|-----|-----|-------|
| `_VERSATILITY_HP_MAX` | 75 | **32** | bonus HP at zero variance |
| `_VERSATILITY_DMG_BONUS` | 20 | **13** | flat damage bonus at zero variance |
| `_VERSATILITY_VARIANCE_CAP` | 100.0 | 100.0 | unchanged |

Derived `25/25/25/25` values: HP `145 → 102`, damage `35–55 → 28–48`.
The bonus stays **meaningful** (balanced still gets +32 HP, +13 dmg) — versatility
remains a viable strategy, it is simply no longer dominant.

The variance cap was deliberately left at 100.0. Raising it (to give high-variance
archetypes a partial bonus) was tested and rejected: it pushes the combat
specialists back out of band (a cap of 200 dropped bruiser/assassin to 35–40%
balanced-win, i.e. they become over-strong) while doing almost nothing for the mage
(see below).

## Measured duel matrix (balanced win %, 30 fixed seeds)

Each cell is balanced's win rate vs that specialist. Target band: **40–60%**.

| Specialist | Allocation (P/S/A/M) | BEFORE | AFTER | In band? |
|------------|----------------------|--------|-------|----------|
| tank       | 15/15/50/20          | 76.7%  | 40.0% | ✅ |
| bruiser    | 40/20/15/25          | 70.0%  | 46.7% | ✅ |
| assassin   | 30/40/10/20          | 73.3%  | 46.7% | ✅ |
| mage       | 15/20/20/45          | 86.7%  | 86.7% | ❌ (see below) |

Confirmed stable at 40 fixed seeds: tank 42.5%, bruiser 50.0%, assassin 47.5%,
mage 90.0%. All measurements are deterministic across repeated runs.

## The mage is an AC blocker, not a regression

The mage archetype (15/20/20/45) **cannot** be brought into band by retuning the
versatility constants. Its high mind allocation only buys `max_energy` and
`energy_regen`, which have **no offensive value** in a 1v1 melee duel driven by a
stats-only chase policy (the shared decide func never rests to bank energy or casts
abilities, so mind is dead weight). Mage's derived combat profile is HP 66 /
damage 9–21 — strictly worse than balanced's 102 / 28–48.

Levers tested and their effect on mage:

- Lowering HP/dmg bonus: helps the combat specialists, leaves mage at ~80–90%
  (mage already gets ratio ≈ 0, so lowering balanced's bonus barely closes the gap
  because mage still has no offense).
- Raising the variance cap to grant mage a bonus (cap 300–600): mage stays at
  70–87% **and** the combat trio falls out of band — strictly worse overall.

Fixing the mage requires a **combat-model** change (making mind matter in duels —
e.g. energy-gated abilities exercised by the policy), which is out of scope for a
derived-stat constant retune (`engine/stats.py` ONLY). This is pinned by
`tests/test_versatility_balance.py::test_mage_documented_structural_weakness` so a
future combat change that makes mind relevant will surface here.

## Built-in pool baseline (`builtin_bots`, 30 matches, seed 1)

Per-bot win rate, old → new (`data/balance_baseline.json` regenerated, deterministic
across two runs):

| Bot | Old | New | Δ |
|-----|-----|-----|---|
| 🤖 | 0.067 | 0.167 | +0.100 |
| 🎯 | 0.067 | 0.033 | −0.033 |
| 🎲 | 0.067 | 0.100 | +0.033 |
| 🐢 | 0.167 | 0.267 | +0.100 |
| 🧠 | 0.200 | 0.133 | −0.067 |
| 🌟 | 0.433 | 0.300 | −0.133 |

🌟 is the Starter (balanced 25/25/25/25) — its dominance dropped from 0.433 to
0.300. Uniform share for 6 bots is 0.167; 2× = 0.333. No bot exceeds 0.333, so AC
item 2 (no archetype's pool rate > 2× uniform share) **passes** on the built-in
pool. Caveat: the built-in pool is thin (6 bots, only one is the balanced
archetype), so this check has limited statistical power and the per-bot rates are
noisy at 30 matches.
