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

S20 complete. All 8 tasks done.

## What Was Just Done

T20.8: S20 integration test. Wrote `tests/test_s20_integration.py` with 30 tests across 9 test classes verifying: CLI command registration (play/watch/generate in --help), TerminalRenderer output (title, grid, HP bars, combatants, kill feed), PROMPT.md required sections (state dict, actions, decide, strategies, examples), starter bot (validation, 7+ TODOs, helpers DSL, builtin_bots location), npcwars play e2e (subprocess --no-watch --seed 42 exits 0, prints winner), npcwars watch e2e (fixture JSON + --speed 100 --no-clear exits 0), npcwars generate e2e (prints PROMPT.md content), README updated (mentions play, generate, PROMPT.md, starter), no dead public functions (all modules importable and wired in __init__). All 30 tests pass. Ruff clean, arch check clean.

## What's Next

S20 sprint complete. Ready for PR or next sprint.

## Completed Sprints

| Sprint | Focus | Tasks | Tests After | PR | Status |
|--------|-------|-------|-------------|-----|--------|
| S1-S11 | Core Engine → Human Play | 97 | 1212 | #1-#8 | Done |
| S12-S15 | Watcher, Wizard, Packaging, Viewer | 42 | 1849 | #12 | Done |
| S16 | The Diff View | 7 | 1946 | #13 | Done |
| S17 | Server Layer | 10 | 2056 | #14 | Done |
| S18 | Polish & Production | 8 | 2170 | — | Done |
