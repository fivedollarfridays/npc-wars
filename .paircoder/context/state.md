# Current State

> Last updated: 2026-03-21 S35+S36 planned

## Active Plans

**Plan:** Sprint 35: Equipment System
- **Sprint:** S35 | **Type:** feature | **Status:** Planned (6 tasks, T35.1-T35.6)
- **Part of:** Phase 2 — Depth (S32-S39)

### S35 Tasks

| Task | Title | Cx | Depends On | Status |
|------|-------|----|------------|--------|
| T35.1 | Equipment catalog + validation | 35 | — | done |
| T35.2 | Combat hooks — weapon + armor bonuses | 35 | T35.1 | done |
| T35.3 | Bot loader — equipment loading + defaults | 20 | T35.1 | done |
| T35.4 | State dict + PROMPT.md — equipment exposure | 15 | T35.2, T35.3 | pending |
| T35.5 | Equipment example bots + balance sim | 30 | T35.3, T35.4 | done |
| T35.6 | GATE: Equipment system integration test | 25 | all | pending |

### S35 Wave Plan

```
Wave 1:             T35.1 — equipment catalog + validation       (35 Cx)
Wave 2 (parallel):  T35.2 + T35.3 — combat hooks + loader       (55 Cx)
Wave 3:             T35.4 — state dict + docs                    (15 Cx)
Wave 4:             T35.5 — example bots + balance               (30 Cx)
Wave 5:             T35.6 — INTEGRATION GATE                     (25 Cx)
```

---

**Plan:** Sprint 36: Tactical Items + Ability System
- **Sprint:** S36 | **Type:** feature | **Status:** Planned (6 tasks, T36.1-T36.6)

### S36 Tasks

| Task | Title | Cx | Depends On | Status |
|------|-------|----|------------|--------|
| T36.1 | Tactical item execution engine | 30 | — | pending |
| T36.2 | power_up callback + use_ability action | 35 | T36.1 | pending |
| T36.3 | evolve callback — mid-match adaptation | 20 | T36.2 | pending |
| T36.4 | Feed + overlay — tactical and ability FX | 15 | T36.1, T36.2 | pending |
| T36.5 | Ability-using example bot + balance sim | 20 | T36.2, T36.3 | pending |
| T36.6 | GATE: Tactical + ability integration test | 20 | all | pending |

## Current Focus

T35.2 done. T35.4 (state dict + docs) still pending before T35.6 gate.

## What Was Just Done

**T35.2: Combat hooks -- weapon + armor bonuses** -- Wired equipment bonuses into the combat pipeline. Added `equipment_bonuses` field to Bot class. Modified `_compute_ac()` with `equipment_dr` and `armor_pierce` params. Extended `roll_attack()` and `roll_ranged_attack()` with equipment_to_hit, equipment_min_dmg, equipment_max_dmg, equipment_crit_mult, equipment_dr, armor_pierce params. Updated `_roll_melee()` and `_roll_ranged()` to read from `bot.equipment_bonuses`. Modified `apply_action_cost()` to apply equipment action_cost_mods. Implemented weapon specials: finesse (speed-based to-hit), armor_piercing (reduces defender AC), reach (attack at 2+ tiles). 18 tests in `tests/test_equipment_combat.py`, all passing. Refactored `_compute_ac` helper and extracted `_d20_chance` + `_equipment_dicts` to keep functions under 50 lines.

## What's Next

T35.4 (state dict + docs) still pending, then T35.6 (integration gate).

## Completed Sprints

| Sprint | Focus | PR | Status |
|--------|-------|-----|--------|
| S1-S18 | Core through Polish | #1-#18 | Done |
| S20-S26 | Experience → King of the Hill | #21 | Done |
| S27 | Stat Budget System | #22 | Done |
| S28 | Roll-Based Combat | #23 | Done |
| S29 | Dodge, Modifiers, Initiative | #24 | Done |
| S30 | Visual Identity | #25 | Done |
| S31 | Balance Tuning + Phase 1 Gate | #27 | Done |
| S32 | XP and Leveling System | #27 | Done |
| S33 | Callback Infrastructure + Trap Action | #28 | Done |
| S34 | Trap Polish & Balance | #29 | Done |
