# Current State

> Last updated: 2026-03-16 S16 done

## Active Plan

**Plan:** NPC Wars v2 — Spectacle, Human Play & The Cringe
**Status:** S12–S16 done. Next: S17 (Server Layer)

## Current Focus

S16 (Diff View) complete. Ready for S17 (Server Layer).

## What Was Just Done

**S16: The Diff View** (7 tasks) -- Stat diff computation module (`data/stat_diff.py`), per-player lifetime stats API (`data/lifetime_stats.py`), GitHub-style diff overlay in viewer with color-coded improved/regressed rows sorted by delta magnitude, diff data injected into match JSON via `inject_diff_data()` wired into play.py and cmd_battle.py, first-match handling with "FIRST MATCH!" banner showing current stats, E2E integration tests running 2 real matches. 1946 tests passing.

**S15: Viewer Polish** (8 tasks) -- Fixed audio stinger paths, added 7 spectacle effects (shatter, glitch, dark entrance, skull flash, pulse wave, multiball, split screen), maximized battlefield layout to 70%+ viewport, added smooth movement interpolation via requestAnimationFrame, wired player profiles into play.py. 1849 tests passing.

**S14: Distribution & Packaging** (10 tasks) -- Built-in bots package, TOML config reader, CLI dispatcher with init/wizard/validate/battle subcommands, package metadata & LICENSE, community scaffolding, E2E integration gate. pip-installable via `npcwars` entry point.

**S13: Vibe Wizard & Helpers** (10 tasks) -- Me/Enemies/Storm helper classes for bot DSL, preset strategies with tuning sliders, wizard CLI for interactive bot generation, package wiring & re-exports, scanner compatibility, example vibes bot + docs, E2E integration gate.

**S12: The Cringe** (14 tasks) -- Adaptive Watcher boss bot with pattern recognition, counter-action engine, rubber-banding difficulty, spawn conditions, memory persistence, learning decay, stats tracking, spectacle events, integration tests.

## What's Next

S17 (Server Layer), S18 (Polish & Production).

## Completed Sprints

| Sprint | Focus | Tasks | Tests After | PR | Status |
|--------|-------|-------|-------------|-----|--------|
| S1 | Engine Test Coverage | T1.1–T1.12 (12) | 233 | #1 | Done |
| S2 | Data Layer + CI | T2.1–T2.8 (8) | 304 | #2 | Done |
| S3 | Discord Bot | T3.1–T3.6 (6) | 370 | #3 | Done |
| S4 | Video Renderer | T4.1–T4.6 (6) | 435 | #4 | Done |
| S5 | YouTube Upload | T5.1–T5.3 (3) | 471 | #4 | Done |
| S6 | Production Hardening | T6.1–T6.9 (9) | 530 | #5 | Done |
| S7 | Security Hardening | T7.1–T7.5 (5) | 585 | #5 | Done |
| S8 | Balance & Physics | T8.1–T8.11 (11) | 720 | #6 | Done |
| S9 | Progression System | T9.1–T9.11 (11) | 870 | #6 | Done |
| S10 | Spectacle & Audio | T10.1–T10.10 (10) | 1103 | #7 | Done |
| S11 | Human Play & Bounty | T11.1–T11.11 (11) | 1212 | #8 | Done |
| S12 | The Cringe (Watcher) | T12.1–T12.14 (14) | 1380 | — | Done |
| S13 | Vibe Wizard & Helpers | T13.1–T13.10 (10) | 1622 | — | Done |
| S14 | Distribution & Packaging | T14.1–T14.10 (10) | 1737 | — | Done |
| S15 | Viewer Polish | T15.1–T15.8 (8) | 1849 | — | Done |
| S16 | The Diff View | T16.1–T16.7 (7) | 1946 | — | Done |

## Archive

Completed sprint docs archived to `.paircoder/archive/`:
- **Tasks:** S1–S15 task files (archived; S16–S18 remain in `.paircoder/tasks/`)
- **Plans:** S1–S15 plan files (archived; S16–S18 remain in `.paircoder/plans/`)
- **Research:** `RESEARCH-spectacle-and-human-play.md` (shipped, archived)
