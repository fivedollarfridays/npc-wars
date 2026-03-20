# Current State

> Last updated: 2026-03-20 S31 planned

## Active Plans

**Plan:** Sprint 31: Balance Tuning + Phase 1 Integration
- **Sprint:** S31 | **Type:** chore | **Status:** Planned (7 tasks, T31.1-T31.7)
- **Part of:** Phase 1 — Agent Wars v2 Foundation (S27-S31)

### S31 Tasks

| Task | Title | Cx | Depends On | Status |
|------|-------|----|------------|--------|
| T31.1 | Tune crit threshold + combat constants | 25 | — | done |
| T31.2 | Balance simulation (archetype comparison) | 30 | T31.1 | done |
| T31.3 | Tune stat scaling curves | 25 | T31.2 | pending |
| T31.4 | Update builtin bots with diverse stats | 20 | T31.3 | pending |
| T31.5 | Update PROMPT.md with full v2 docs | 25 | T31.3 | pending |
| T31.6 | Regression: 25/25/25/25 similarity | 20 | T31.3 | pending |
| T31.7 | GATE: Full Phase 1 integration audit | 25 | all | pending |

### S31 Wave Plan

```
Wave 1:             T31.1 — Tune crit threshold              (25 Cx)
Wave 2:             T31.2 — Balance simulation                (30 Cx)
Wave 3:             T31.3 — Tune stat curves                  (25 Cx)
Wave 4 (parallel):  T31.4 + T31.5 + T31.6                   (65 Cx)
Wave 5:             T31.7 — INTEGRATION GATE                  (25 Cx)
```

## Current Focus

S31 Wave 2 complete. Ready for T31.3 (tune stat scaling curves).

## What Was Just Done

T31.2: Created tools/balance_sim.py with 7-archetype round-robin simulation (700 matches, C(7,4)=35 combos x 20 each). Results: Bruiser 50.0%, Duelist 30.5%, Tank 27.5%, Assassin 20.0%, Glass Cannon 18.5%, Mage 10.2%, Balanced 9.0%. Max win rate under 55% target. Balanced archetype underperforms (9% vs 48-52% target) -- needs stat curve tuning in T31.3. 12 tests pass, ruff clean.

## What's Next

T31.3: Tune stat scaling curves -- Balanced at 9% win rate indicates stat differentiation is too rewarding; curves need flattening or Balanced needs inherent advantage.

## Completed Sprints

| Sprint | Focus | PR | Status |
|--------|-------|-----|--------|
| S1-S18 | Core through Polish | #1-#18 | Done |
| S20-S26 | Experience → King of the Hill | #21 | Done |
| S27 | Stat Budget System | #22 | Done |
| S28 | Roll-Based Combat | #23 | Done |
| S29 | Dodge, Modifiers, Initiative | #24 | Done |
| S30 | Visual Identity | #25 | Done |
