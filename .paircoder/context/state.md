# Current State

> Last updated: 2026-03-19 T28.8 done

## Active Plans

**Plan:** Sprint 28: Roll-Based Combat Overhaul
- **Sprint:** S28 | **Type:** feature | **Status:** Complete (8/8 tasks done)
- **Part of:** Phase 1 — Agent Wars v2 Foundation (S27-S31, 35 tasks, 810 Cx)

### S28 Tasks

| Task | Title | Cx | Depends On | Status |
|------|-------|----|------------|--------|
| T28.1 | Combat roll engine + CombatResult | 30 | — | done |
| T28.2 | Critical hit system | 20 | T28.1 | done |
| T28.3 | Thread RNG through game loop | 25 | T28.1 | done |
| T28.4 | Wire roll combat into resolve_attacks | 25 | T28.1-3 | done |
| T28.5 | Ranged attacks use roll system | 20 | T28.4 | done |
| T28.6 | Combat events carry roll/crit data | 15 | T28.4-5 | done |
| T28.7 | Feed formatters for crit/miss events | 20 | T28.6 | done |
| T28.8 | GATE: Statistical validation | 25 | all | done |

### S28 Wave Plan

```
Wave 1 (parallel): T28.1, T28.2              (50 Cx)
Wave 2:            T28.3                       (25 Cx)
Wave 3:            T28.4                       (25 Cx)
Wave 4 (parallel): T28.5, T28.6              (35 Cx)
Wave 5:            T28.7                       (20 Cx)
Wave 6:            T28.8 — INTEGRATION GATE    (25 Cx)
```

## Current Focus

Sprint 28 complete. All 8 tasks done. Ready for next sprint.

## What Was Just Done

T28.8: GATE — Statistical validation for roll-based combat. Created `tests/test_s28_integration.py` with 12 integration tests across 6 test classes. Ran 20 seeded matches to validate: avg damage ~32.5 (within [20,40]), miss rate ~24.6% (within [5%,30%]), crit rate within [30%,70%], match length within [15,60] rounds. Verified all hit/miss events carry roll/modifier/ac/is_crit fields. Confirmed high-power bots deal more damage, high-armor bots take fewer hits, feed shows CRIT and dodged text, builtin bots complete matches, and deterministic bots with same seed produce identical results. Fixed S27 `test_default_bots_damage_is_25` to accept roll-based range instead of exact value. All 2618 tracked tests pass, ruff clean.

## What's Next

Sprint 28 complete. Ready for next sprint (S29+).

## Completed Sprints

| Sprint | Focus | PR | Status |
|--------|-------|-----|--------|
| S1-S18 | Core through Polish | #1-#18 | Done |
| S20-S24 | Experience, Memory, Tournament, Restructure, FX | — | Done |
| S25-S26 | Momentum, King of the Hill | #21 | Done |
| S27 | Stat Budget System | #22 | Done |
| S28 | Roll-Based Combat Overhaul | — | Done |
