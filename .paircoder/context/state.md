# Current State

> Last updated: 2026-03-23 S44 planned

## Active Plans

**Plan:** Sprint 44: Code-Built Character System
- **Sprint:** S44 | **Type:** feature | **Status:** Planned (4 tasks, T44.1-T44.4)
- **Part of:** Phase 3B — Spectacle (S44-S47)
- **Plan ID:** plan-2026-03-s44-characters

### S44 Tasks

| Task | Title | Cx | Depends On | Status |
|------|-------|----|------------|--------|
| T44.1 | Character descriptor engine | 20 | — | done |
| T44.2 | Viewer character rendering upgrade | 25 | T44.1 | done |
| T44.3 | Character preview on profile + editor | 15 | T44.2 | pending |
| T44.4 | GATE: Character system validation | 15 | all | pending |

### S44 Wave Plan

```
Wave 1:             T44.1 — character descriptor engine              (20 Cx)
Wave 2:             T44.2 — viewer rendering upgrade                 (25 Cx)
Wave 3:             T44.3 — profile/editor preview                   (15 Cx)
Wave 4:             T44.4 — CHARACTER GATE                           (15 Cx)
```

## Current Focus

S44 in progress. T44.1-T44.2 complete, T44.3 next.

## What Was Just Done

**T44.2: Viewer character rendering upgrade** -- upgraded `viewer/js/shapes.js` (159->238 lines) with `interpolateColor` (HP color gradient toward gray), `drawWeaponIndicator` (6 weapon types: dot/line/long_line/wedge/arc/circle), `drawCharacterPreview` (profile page rendering). Updated `drawBotShape` to accept optional character descriptor for color, border_thickness, shape, and weapon indicator. Updated `viewer/js/renderer.js` to build character lookup from `matchData.players` and pass descriptor to `drawBotShape`. 12 tests in `tests/test_viewer_characters.py`. All 53 viewer tests pass, no regressions.

## What's Next

T44.3 -- Character preview on profile + editor (depends on T44.2).

## Completed Sprints

| Sprint | Focus | PR | Status |
|--------|-------|-----|--------|
| S1-S18 | Core through Polish | #1-#18 | Done |
| S20-S31 | Phase 1: Foundation | #20-#27 | Done |
| S32-S39 | Phase 2: Depth | #27-#34 | Done |
| S40-S43 | Phase 3A: Playable Product | #35-#39 | Done |
