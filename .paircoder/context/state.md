# Current State

> Last updated: 2026-03-22 S37 planned

## Active Plans

**Plan:** Sprint 37: Terrain Engine
- **Sprint:** S37 | **Type:** feature | **Status:** Planned (6 tasks, T37.1-T37.6)
- **Part of:** Phase 2 — Depth (S32-S39)
- **Plan ID:** plan-2026-03-s37-terrain

### S37 Tasks

| Task | Title | Cx | Depends On | Status |
|------|-------|----|------------|--------|
| T37.1 | Terrain map definitions + data model | 30 | — | done |
| T37.2 | Movement + wall collision | 25 | T37.1 | done |
| T37.3 | Combat modifiers from terrain | 30 | T37.1 | done |
| T37.4 | Map selection + state dict + PROMPT.md | 20 | T37.2, T37.3 | pending |
| T37.5 | CLI renderer terrain + balance sim | 20 | T37.4 | done |
| T37.6 | GATE: Terrain system integration test | 20 | all | pending |

### S37 Wave Plan

```
Wave 1:             T37.1 — terrain maps + data model            (30 Cx)
Wave 2 (parallel):  T37.2 (movement) + T37.3 (combat mods)      (55 Cx)
Wave 3:             T37.4 — map selection + state dict + docs    (20 Cx)
Wave 4:             T37.5 — renderer + balance sim               (20 Cx)
Wave 5:             T37.6 — INTEGRATION GATE                     (20 Cx)
```

## Current Focus

T37.5 complete. Wave 4 done. T37.6 (INTEGRATION GATE) is next.

## What Was Just Done

**T37.5: CLI renderer terrain + balance sim** -- Added terrain rendering to `agentgrounds/wars/cli/renderer.py`: `set_terrain()` method and inline terrain cell rendering in `_grid()` using colored ANSI chars (wall=gray #, water=blue ~, high_ground=yellow ^, cover=green %, crystal=magenta *). Added `_TERRAIN_DISPLAY` lookup dict. Wired terrain tiles into match output (`engine/game.py` adds `terrain_tiles` to result dict) and CLI playback commands (`cmd_play.py`, `cmd_watch.py`). Added 4 feed formatters in `agentgrounds/wars/cli/feed.py`: `wall_blocked`, `crystal_pickup`, `terrain_blocked`, `water_penalty`. Created `tools/terrain_balance_sim.py` (200 matches, 40 per map, all 5 maps). Results: no bot exceeds 65% on any map (max was TankBot 60% on highlands). Created regression test `tests/test_s37_regression.py` (3 tests). Total: 5 feed tests + 7 renderer tests + 3 regression tests = 15 new tests.

## What's Next

T37.6 (GATE: Terrain system integration test). Note: `agentgrounds/wars/cli/feed.py` has pre-existing arch error (24 functions, limit 15) -- should be split in a future sprint. `engine/game.py` is at 408+ lines (over 400 limit) -- should be addressed in T37.6 or future sprint.

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
| S35 | Equipment System | #30 | Done |
| S36 | Tactical Items + Ability System | #31 | Done |
