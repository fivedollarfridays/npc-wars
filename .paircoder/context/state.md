# Current State

> Last updated: 2026-03-14 S11 merged (PR #8)

## Active Plan

**Plan:** NPC Wars v2 — Spectacle, Human Play & The Watcher
**Status:** 6 sprints planned, 70 tasks total. 4 sprints done, 2 remaining.
**Current Sprint:** S12 (The Watcher) — **Ready to Start**

## Current Focus

S11 merged. Ready for S12: The Watcher (adaptive AI boss bot).

## What Was Just Done

**Sprint 11: Human Play & Bounty** — Merged via PR #8. Added copilot mode (human override via pluggable adapters), async match loop with 2s input window, bounty system with co-op scaling, AFK detection, Discord button input, viewer live mode, and WebSocket real-time server. Refactored game.py to eliminate sync/async duplication. 1212 tests, all passing.

## What's Next

Sprint 12: The Watcher — 14 tasks, 380 Cx. Adaptive AI boss that learns player patterns mid-match.

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
| S12 | The Watcher (adaptive boss) | T12.1–T12.14 (14) | 380 | Ready |
| S13 | Match Modes & Community | T13.1–T13.13 (13) | 375 | Planned |

## S12 Tasks: The Watcher

| ID | Title | Cx | Status |
|----|-------|----|--------|
| T12.1 | Watcher Bot Skeleton & Emoji Identity | 15 | pending |
| T12.2 | Pattern Table Data Structure | 35 | pending |
| T12.3 | Per-Player Frequency Counter | 35 | pending |
| T12.4 | Counter-Action Selection Engine | 50 | pending |
| T12.5 | Sync Rating Calculation | 25 | pending |
| T12.6 | Rubber-Banding Difficulty System | 35 | pending |
| T12.7 | Spawn Conditions & Mid-Match Entry | 35 | pending |
| T12.8 | Adaptive Target Rotation (Co-op) | 35 | pending |
| T12.9 | Watcher Memory Persistence (JSON) | 25 | pending |
| T12.10 | Learning Decay (Session & Cross-Session) | 25 | pending |
| T12.11 | Full Action Set Access for Watcher | 15 | pending |
| T12.12 | Watcher Stats & Kill/Death Tracking | 25 | pending |
| T12.13 | Watcher Spectacle Events | 25 | pending |
| T12.14 | Integration Tests — The Watcher | 35 | pending |

## Archive

Completed sprint docs archived to `.paircoder/archive/`:
- **Tasks:** S1–S10 task files (archived; S11–S13 remain in `.paircoder/tasks/`)
- **Plans:** S1–S10 plan files (archived; S11–S13 remain in `.paircoder/plans/`)
- **Research:** `RESEARCH-spectacle-and-human-play.md` (shipped, archived)
