# Current State

> Last updated: 2026-03-14 T12.14 done

## Active Plan

**Plan:** NPC Wars v2 — Spectacle, Human Play & The Watcher
**Status:** 6 sprints planned, 70 tasks total. 5 sprints done, 1 remaining.
**Current Sprint:** S12 (The Watcher) — **Done**

## Current Focus

S12 complete. All 14 tasks done (T12.1-T12.14). Ready for S13 (Match Modes & Community).

## What Was Just Done

**T12.14: Integration Tests -- The Watcher** — Created `tests/test_integration_watcher.py` with 17 end-to-end integration tests covering all 8 Watcher subsystems: spawn conditions, pattern recording/prediction pipeline, sync calculation, memory persistence roundtrip, rubber-banding, target rotation, spectacle events, stats tracking, and a full 5-round pipeline test. 1400 total passing. Ruff clean. S12 sprint complete.

## What's Next

S13: Match Modes & Community (T13.1-T13.13).

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

## Upcoming Sprints

| Sprint | Focus | Tasks | Cx | Status |
|--------|-------|-------|----|--------|
| S13 | Match Modes & Community | T13.1–T13.13 (13) | 375 | Planned |

## S12 Tasks: The Watcher

| ID | Title | Cx | Status |
|----|-------|----|--------|
| T12.1 | Watcher Bot Skeleton & Emoji Identity | 15 | done |
| T12.2 | Pattern Table Data Structure | 35 | done |
| T12.3 | Per-Player Frequency Counter | 35 | done |
| T12.4 | Counter-Action Selection Engine | 50 | done |
| T12.5 | Sync Rating Calculation | 25 | done |
| T12.6 | Rubber-Banding Difficulty System | 35 | done |
| T12.7 | Spawn Conditions & Mid-Match Entry | 35 | done |
| T12.8 | Adaptive Target Rotation (Co-op) | 35 | done |
| T12.9 | Watcher Memory Persistence (JSON) | 25 | done |
| T12.10 | Learning Decay (Session & Cross-Session) | 25 | done |
| T12.11 | Full Action Set Access for Watcher | 15 | done |
| T12.12 | Watcher Stats & Kill/Death Tracking | 25 | done |
| T12.13 | Watcher Spectacle Events | 25 | done |
| T12.14 | Integration Tests — The Watcher | 35 | done |

## Archive

Completed sprint docs archived to `.paircoder/archive/`:
- **Tasks:** S1–S10 task files (archived; S11–S13 remain in `.paircoder/tasks/`)
- **Plans:** S1–S10 plan files (archived; S11–S13 remain in `.paircoder/plans/`)
- **Research:** `RESEARCH-spectacle-and-human-play.md` (shipped, archived)
