# Current State

> Last updated: 2026-03-24 S46 planned

## Active Plans

**Plan:** Sprint 46: Character Customization (Paid Cosmetics)
- **Sprint:** S46 | **Type:** feature | **Status:** Planned (4 tasks, T46.1-T46.4)
- **Part of:** Phase 3B — Spectacle (S44-S47)

### S46 Tasks

| Task | Title | Cx | Depends On | Status |
|------|-------|----|------------|--------|
| T46.1 | Cosmetic catalog + inventory system | 25 | — | done |
| T46.2 | Cosmetic store API + match coin rewards | 20 | T46.1 | done |
| T46.3 | Viewer cosmetic rendering | 20 | T46.1 | pending |
| T46.4 | GATE: Cosmetic system validation | 10 | all | pending |

### S46 Wave Plan

```
Wave 1:             T46.1 — catalog + inventory                    (25 Cx)
Wave 2 (parallel):  T46.2 (store API) + T46.3 (viewer rendering)  (40 Cx)
Wave 3:             T46.4 — COSMETIC GATE                          (10 Cx)
```

## Current Focus

T46.2 complete. T46.3 (viewer cosmetic rendering) next.

## What Was Just Done

**T46.2: Cosmetic store API + match coin rewards** -- Created `server/routes/cosmetics.py` (6 endpoints: browse store, coin balance, buy, inventory, equip, unequip), `server/coin_rewards.py` (award_match_coins helper), wired into `server/worker.py` for post-match coin distribution. Registered cosmetics router in `server/app.py`. 15 API tests in `tests/test_cosmetic_api.py`, 5 coin reward tests in `tests/test_coin_rewards.py`. All 51 related tests passing, ruff clean.

## What's Next

T46.3 (viewer cosmetic rendering) is unblocked. After that, T46.4 (GATE).

## Completed Sprints

| Sprint | Focus | PR | Status |
|--------|-------|-----|--------|
| S1-S31 | Phase 1: Foundation | #1-#27 | Done |
| S32-S39 | Phase 2: Depth | #27-#34 | Done |
| S40-S43 | Phase 3A: Playable Product | #35-#39 | Done |
| S44 | Character System | #40 | Done |
| S45 | Kill Cam + Sound + Preflight | #41 | Done |
