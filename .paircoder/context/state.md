# Current State

> Last updated: 2026-03-17 S20 plan created

## Active Plans

**Plan 1:** NPC Wars -- Get Sellable (Public Release)
- **Sprint:** S19 | **Type:** chore | **Status:** Planned (5 tasks, T1-T5)

**Plan 2:** Sprint 20: The Experience Layer
- **Sprint:** S20 | **Type:** feature | **Status:** Planned (8 tasks, T20.1-T20.8)

### S20 Tasks

| Task | Title | Cx | Depends On | Status |
|------|-------|----|------------|--------|
| T20.1 | ANSI terminal renderer module | 40 | — | done |
| T20.2 | `npcwars watch` — CLI match playback | 30 | T20.1 | done |
| T20.3 | `npcwars play` — one-command experience | 25 | T20.2 | done |
| T20.4 | Agent Arena prompt doc (PROMPT.md) | 20 | — | done |
| T20.5 | Starter bot template with guided TODOs | 15 | — | done |
| T20.6 | `npcwars generate` — AI-assisted bot creation | 25 | T20.4 | done |
| T20.7 | Integration wiring + CLI polish | 20 | T20.3, T20.5 | done |
| T20.8 | S20 integration test | 20 | all | done |

**Total: 195 Cx**

### S20 Wave Plan

```
Wave 1 (no deps):     T20.1, T20.4, T20.5              (75 Cx)
Wave 2 (viewer):      T20.2, T20.6                      (55 Cx)
Wave 3 (experience):  T20.3                              (25 Cx)
Wave 4 (polish):      T20.7                              (20 Cx)
Wave 5 (gate):        T20.8 — INTEGRATION GATE           (20 Cx)
```

## Current Focus

S26 complete. All tasks T26.1-T26.5 done.

## What Was Just Done

T26.5: S26 integration test + balance verification (INTEGRATION GATE). Created `tests/test_s26_integration.py` with 14 tests covering: one-leader-per-round rule, non-leader tier cap at 2, leader reaching tier 3+, is_leader in position data, energy drain events, drain field validation, leader bounty constant, REGICIDE in feed output, crown in rendered roster, drain rate in roster, PROMPT.md leader/bounty/king-of-the-hill/is_leader content, and public API importability. Updated `PROMPT.md` with King of the Hill section, is_leader in state dict example, and leader strategy tips. All 14 S26 tests pass, all S25 and renderer tests pass, ruff clean.

## What's Next

S26 sprint complete. Ready for branch merge/PR.

## Completed Sprints

| Sprint | Focus | Tasks | Tests After | PR | Status |
|--------|-------|-------|-------------|-----|--------|
| S1-S11 | Core Engine → Human Play | 97 | 1212 | #1-#8 | Done |
| S12-S15 | Watcher, Wizard, Packaging, Viewer | 42 | 1849 | #12 | Done |
| S16 | The Diff View | 7 | 1946 | #13 | Done |
| S17 | Server Layer | 10 | 2056 | #14 | Done |
| S18 | Polish & Production | 8 | 2170 | — | Done |
