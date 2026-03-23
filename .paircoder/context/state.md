# Current State

> Last updated: 2026-03-23 S42 planned

## Active Plans

**Plan:** Sprint 42: Server Layer (Vertical Slice)
- **Sprint:** S42 | **Type:** feature | **Status:** Planned (4 tasks, T42.1-T42.4)
- **Part of:** Phase 3A — Playable Product (S40-S43)
- **Plan ID:** plan-2026-03-s42-server

### S42 Tasks

| Task | Title | Cx | Depends On | Status |
|------|-------|----|------------|--------|
| T42.1 | Player auth + bot persistence | 25 | — | done |
| T42.2 | Lobby HTTP endpoints + matchmaking pipeline | 30 | T42.1 | done |
| T42.3 | CLI upload command | 20 | T42.1 | done |
| T42.4 | GATE: Server E2E — two players fight online | 20 | all | pending |

### S42 Wave Plan

```
Wave 1:             T42.1 — player auth + bot storage              (25 Cx)
Wave 2 (parallel):  T42.2 (lobby/matchmaking) + T42.3 (CLI upload) (50 Cx)
Wave 3:             T42.4 — SERVER E2E GATE                        (20 Cx)
```

## Current Focus

Wave 2 complete (T42.2 + T42.3). T42.4 (Server E2E gate) unblocked.

## What Was Just Done

**T42.3: CLI upload command** — `agentgrounds wars upload my_bot.py` with local bot_scanner validation, POST /api/submit-bot, auto lobby join + match polling, --no-join/--server/--api-key flags, ~/.agentgrounds/config.json for API key persistence. 15 new tests (all mocked, no server needed).

**T42.2: Lobby HTTP endpoints + matchmaking pipeline** — POST /api/lobby/join, GET /api/lobby/status, GET /api/lobby/history endpoints. match_players table for tracking. Lobby fills trigger enqueue_match pipeline. 11 new tests (3 DB + 8 HTTP).

**T42.1: Player auth + bot persistence** — API key auth, bot storage in SQLite, submit-bot now persists bots, GET /api/bots routes added. 20 new tests (12 DB + 8 HTTP).

## What's Next

T42.4 (GATE: Server E2E -- two players fight online). All dependencies met.

## Completed Sprints

| Sprint | Focus | PR | Status |
|--------|-------|-----|--------|
| S1-S18 | Core through Polish | #1-#18 | Done |
| S20-S26 | Experience → King of the Hill | #21 | Done |
| S27-S31 | Phase 1: Foundation | #22-#27 | Done |
| S32-S39 | Phase 2: Depth | #27-#34 | Done |
| S40 | PyPI Release + Install Flow | #35 | Done |
| S41 | Browser Viewer Overhaul | #36 | Done |
