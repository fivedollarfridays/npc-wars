# Current State

> Last updated: 2026-03-16 S17 done

## Active Plan

**Plan:** NPC Wars v2 — Spectacle, Human Play & The Cringe
**Status:** S12–S17 done. Next: S18 (Polish & Production)

## Current Focus

S17 complete. Ready for /reviewing-and-fixing then S18.

## What Was Just Done

**S17: Server Layer** (10 tasks) -- FastAPI app with CORS + /health, POST /api/submit-bot with AST validation + rate limiting, Redis-backed match queue + worker process, GET /api/match/{id} with path traversal protection, GET /api/stats + /api/leaderboard, time-limited 30s lobby with AI fill, adaptive fill bots using preset strategies calibrated to skill level, Monaco in-browser code editor, SQLite player registry. 2056 tests passing.

**S16: The Diff View** (7 tasks) -- Stat diff computation, lifetime stats API, diff overlay with color-coded rows sorted by delta, diff data injected into match JSON, first-match handling. 1946 tests.

**S15: Viewer Polish** (8 tasks) -- 7 spectacle effects, battlefield layout 70%+, movement interpolation, audio path fix, player profiles. 1849 tests.

**S14: Distribution & Packaging** (10 tasks) -- pip install npc-wars, CLI dispatcher, built-in bots, community scaffolding. 1737 tests.

**S13: Vibe Wizard & Helpers** (10 tasks) -- Me/Enemies/Storm DSL, presets, wizard CLI. 1622 tests.

**S12: The Cringe** (14 tasks) -- Adaptive Watcher boss bot. 1380 tests.

## What's Next

S18 (Polish & Production) — final sprint.

## Completed Sprints

| Sprint | Focus | Tasks | Tests After | PR | Status |
|--------|-------|-------|-------------|-----|--------|
| S1 | Engine Test Coverage | 12 | 233 | #1 | Done |
| S2 | Data Layer + CI | 8 | 304 | #2 | Done |
| S3 | Discord Bot | 6 | 370 | #3 | Done |
| S4 | Video Renderer | 6 | 435 | #4 | Done |
| S5 | YouTube Upload | 3 | 471 | #4 | Done |
| S6 | Production Hardening | 9 | 530 | #5 | Done |
| S7 | Security Hardening | 5 | 585 | #5 | Done |
| S8 | Balance & Physics | 11 | 720 | #6 | Done |
| S9 | Progression System | 11 | 870 | #6 | Done |
| S10 | Spectacle & Audio | 10 | 1103 | #7 | Done |
| S11 | Human Play & Bounty | 11 | 1212 | #8 | Done |
| S12 | The Cringe (Watcher) | 14 | 1380 | #12 | Done |
| S13 | Vibe Wizard & Helpers | 10 | 1622 | #12 | Done |
| S14 | Distribution & Packaging | 10 | 1737 | #12 | Done |
| S15 | Viewer Polish | 8 | 1849 | #12 | Done |
| S16 | The Diff View | 7 | 1946 | #13 | Done |
| S17 | Server Layer | 10 | 2056 | — | Done |

## Archive

Completed sprint docs archived to `.paircoder/archive/`:
- **Tasks:** S1–S15 (archived; S16–S18 remain in `.paircoder/tasks/`)
- **Plans:** S1–S15 (archived; S16–S18 remain in `.paircoder/plans/`)
