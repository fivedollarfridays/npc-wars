# Current State

> Last updated: 2026-03-23 S43 planned

## Active Plans

**Plan:** Sprint 43: Leaderboard + Discord (Phase 3A Final)
- **Sprint:** S43 | **Type:** feature | **Status:** Planned (4 tasks, T43.1-T43.4)
- **Part of:** Phase 3A — Playable Product (S40-S43) — FINAL SPRINT
- **Plan ID:** plan-2026-03-s43-leaderboard

### S43 Tasks

| Task | Title | Cx | Depends On | Status |
|------|-------|----|------------|--------|
| T43.1 | Web leaderboard + player profile pages | 30 | — | done |
| T43.2 | Discord match announcements + challenge | 25 | — | done |
| T43.3 | CLI leaderboard command | 15 | T43.1 | pending |
| T43.4 | GATE: Phase 3A completion — full product loop | 15 | all | pending |

### S43 Wave Plan

```
Wave 1 (parallel):  T43.1 (web pages) + T43.2 (Discord)           (55 Cx)
Wave 2:             T43.3 — CLI leaderboard                        (15 Cx)
Wave 3:             T43.4 — PHASE 3A GATE                          (15 Cx)
```

## Current Focus

T43.1 done. T43.3 (CLI leaderboard) unblocked.

## What Was Just Done

**T43.1 done** — Web leaderboard + player profile pages. Created `server/routes/pages.py` (GET /leaderboard, GET /profile/{id}), `server/static/leaderboard.html` (sortable table), `server/static/profile.html` (stats + match history). Added GET /api/matches/{player_id} to stats.py. 5 tests, all passing.

## What's Next

T43.3 (CLI leaderboard command, depends on T43.1 which is now done).

## Completed Sprints

| Sprint | Focus | PR | Status |
|--------|-------|-----|--------|
| S1-S18 | Core through Polish | #1-#18 | Done |
| S20-S26 | Experience → King of the Hill | #21 | Done |
| S27-S31 | Phase 1: Foundation | #22-#27 | Done |
| S32-S39 | Phase 2: Depth | #27-#34 | Done |
| S40 | PyPI Release + Install Flow | #35 | Done |
| S41 | Browser Viewer Overhaul | #36 | Done |
| S42 | Server Layer (Multiplayer) | #38 | Done |
