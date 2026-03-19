# Current State

> Last updated: 2026-03-19 T29.7 done

## Active Plans

**Plan:** Sprint 29: Combat Overhaul pt.2 — Dodge, Modifiers, Initiative
- **Sprint:** S29 | **Type:** feature | **Status:** Done (7/7 tasks)
- **Part of:** Phase 1 — Agent Wars v2 Foundation (S27-S31, 35 tasks, 810 Cx)

### S29 Tasks

| Task | Title | Cx | Depends On | Status |
|------|-------|----|------------|--------|
| T29.1 | Extract combat helpers from rounds.py | 20 | — | done |
| T29.2 | Dodge system (SPEED-based) | 25 | T29.1 | done |
| T29.3 | Situational to-hit modifiers | 25 | T29.2 | done |
| T29.4 | Initiative system (SPEED priority) | 20 | T29.1 | done |
| T29.5 | Hit probability calculator | 25 | T29.2, T29.3 | done |
| T29.6 | Incoming threat estimator | 20 | T29.5 | done |
| T29.7 | GATE: Mixed archetypes audit | 25 | all | done |

### S29 Wave Plan

```
Wave 1:             T29.1 — Extract helpers          (20 Cx)
Wave 2 (parallel):  T29.2, T29.4 — Dodge + init      (45 Cx)
Wave 3:             T29.3 — Modifiers                  (25 Cx)
Wave 4 (parallel):  T29.5, T29.6 — Hit calc + threat  (45 Cx)
Wave 5:             T29.7 — INTEGRATION GATE           (25 Cx)
```

## Current Focus

S29 complete. All 7 tasks done.

## What Was Just Done

T29.7 (GATE): Integration gate for S29. Created `tests/test_s29_integration.py` with 13 tests covering: dodge events in real matches, high-speed dodge rate advantage, initiative kill attribution, resting-target hit-rate modifier, state dict `hit_chance_vs` presence and structure, `incoming_threat` sorting, architecture compliance for `rounds.py` and `rounds_combat.py`, builtin bot regression, and feed "(glancing)" rendering for dodged hits. All 13 tests pass. No regressions introduced (pre-existing failures in `test_bot_memory_wiring.py` are unrelated).

## What's Next

S29 sprint complete. Ready for PR or next sprint.

## Completed Sprints

| Sprint | Focus | PR | Status |
|--------|-------|-----|--------|
| S1-S18 | Core through Polish | #1-#18 | Done |
| S20-S24 | Experience, Memory, Tournament, Restructure, FX | — | Done |
| S25-S26 | Momentum, King of the Hill | #21 | Done |
| S27 | Stat Budget System | #22 | Done |
| S28 | Roll-Based Combat | #23 | Done |
