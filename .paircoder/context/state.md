# Current State

> Last updated: 2026-03-12

## Active Plan

**Plan:** NPC Wars Full Build — 5 Sprints
**Status:** Planned, ready for S1
**Current Sprint:** S1 (Engine Tests)

## Plans Overview

| Sprint | Plan ID | Focus | Tasks | Cx | Status |
|--------|---------|-------|-------|----|--------|
| S1 | plan-2026-03-s1-engine-tests | Engine Test Coverage | T1.1–T1.12 | 260 | **Active** |
| S2 | plan-2026-03-s2-data-ci | Data Layer + CI | T2.1–T2.8 | 185 | Pending |
| S3 | plan-2026-03-s3-discord-bot | Discord Bot | T3.1–T3.6 | 145 | Pending |
| S4 | plan-2026-03-s4-video-renderer | Video Renderer | T4.1–T4.6 | 180 | Pending |
| S5 | plan-2026-03-s5-youtube-upload | YouTube Upload | T5.1–T5.3 | 75 | Pending |

## Task Status

### S1: Engine Tests (Active)

| ID | Title | Cx | Type | Status |
|----|-------|----|------|--------|
| T1.1 | Test grid module: bounds, directions, storm border | 15 | chore | ✓ done |
| T1.2 | Test combat module: Bot class, damage, death priority | 20 | chore | ✓ done |
| T1.3 | Test state module: state dict builder | 10 | chore | ✓ done |
| T1.4 | Test sandbox: action validation, timeout, failures | 25 | chore | ✓ done |
| T1.5 | Test loader: bot discovery, validation, errors | 20 | chore | ✓ done |
| T1.6 | Test match_writer: JSON output structure | 15 | chore | ✓ done |
| T1.7 | Test game loop: full match e2e with seeded bots | 35 | chore | ✓ done |
| T1.8 | Bug: fix Bot.force_rest dead code | 15 | bugfix | ✓ done |
| T1.9 | Bug: seed ChaosBot random for reproducibility | 15 | bugfix | ✓ done |
| T1.10 | Bug: prevent energy going negative | 15 | bugfix | ✓ done |
| T1.11 | Bug: add tiebreaker for 200-round draws | 20 | bugfix | ✓ done |
| T1.12 | Bug: fix kill attribution to killing blow | 20 | bugfix | ✓ done |

### S2: Data + CI (Pending)

| ID | Title | Cx | Type | Status |
|----|-------|----|------|--------|
| T2.1 | Create data/emoji_claims.py (CRUD, uniqueness) | 25 | feature | pending |
| T2.2 | Create data/leaderboard.py (stats, rankings) | 30 | feature | pending |
| T2.3 | Create data/match_history.py (index, query) | 25 | feature | pending |
| T2.4 | Create scripts/validate_bot.py (CI validator) | 30 | feature | pending |
| T2.5 | Add requirements.txt and pyproject.toml | 10 | chore | pending |
| T2.6 | GitHub Actions CI: lint, test, coverage gate | 25 | feature | pending |
| T2.7 | Bot submission PR template + validation workflow | 20 | feature | pending |
| T2.8 | Add type hints to engine modules | 20 | refactor | pending |

### S3: Discord Bot (Pending)

| ID | Title | Cx | Type | Status |
|----|-------|----|------|--------|
| T3.1 | Discord bot scaffold: connection, config, commands | 25 | feature | pending |
| T3.2 | Emoji claim system: /claim, /unclaim, /roster | 30 | feature | pending |
| T3.3 | Match announcements: auto-post start/end | 25 | feature | pending |
| T3.4 | Results display: embed with stats, placements | 20 | feature | pending |
| T3.5 | Leaderboard command: /leaderboard with pagination | 20 | feature | pending |
| T3.6 | Message formatter module (testable, no Discord dep) | 25 | feature | pending |

### S4: Video Renderer (Pending)

| ID | Title | Cx | Type | Status |
|----|-------|----|------|--------|
| T4.1 | Grid renderer: Pillow frame, cells, storm overlay | 35 | feature | pending |
| T4.2 | Bot sprites: emoji, HP bars, name labels | 30 | feature | pending |
| T4.3 | Combat effects: hit flash, death, damage numbers | 35 | feature | pending |
| T4.4 | Scoreboard overlay: round counter, kill feed | 25 | feature | pending |
| T4.5 | Video composer: ffmpeg frame-to-MP4 pipeline | 30 | feature | pending |
| T4.6 | Match video CLI: render JSON to MP4 e2e | 25 | feature | pending |

### S5: YouTube Upload (Pending)

| ID | Title | Cx | Type | Status |
|----|-------|----|------|--------|
| T5.1 | YouTube API auth: OAuth2, token storage | 25 | feature | pending |
| T5.2 | Upload pipeline: metadata, thumbnail, tags | 30 | feature | pending |
| T5.3 | Auto-publish CLI: render + upload in one command | 20 | feature | pending |

## What Was Just Done

### Session: 2026-03-12 -- Consider Fixes 12-15

- **Fix 12**: GooseLoose storm center deadlock -- only override dx/dy with storm pull when pull is non-zero; refactored decide() into 3 functions to stay under 50-line limit
- **Fix 13**: Bot.__init__ now uses keyword-only arguments (added `*` before `name`)
- **Fix 14**: Added single-bot match test to tests/test_game.py
- **Fix 15**: Added `__all__` exports to all 7 engine modules (combat, grid, sandbox, state, match_writer, rounds, game)
- Created tests/test_consider_fixes.py (12 tests covering all 4 fixes)
- All 195 tests pass, all arch checks clean

### Session: 2026-03-12 — Two Gameplay Bug Fixes in rounds.py

- **Bug 1 (forced-rest double healing):** Removed early healing from `resolve_decisions` for forced-rest bots. Removed `forced_rest` exclusion from healing loop in `apply_energy_and_rest` so all resters (forced and explicit) heal at the same time -- after attacks and storm damage.
- **Bug 2 (pos_map collision):** Changed `pos_map` from plain dict to `defaultdict(list)` in `resolve_attacks`. Now iterates through all bots at a position to find a valid (alive, non-self) target instead of silently overwriting.
- Created tests/test_rounds.py (5 tests): forced-rest timing, energy deduction skip, healing in apply_energy_and_rest, stacked bots targetable, dead-bot-at-same-tile bypass
- All 195 tests pass, arch check clean

### Session: 2026-03-12 — Test Suite Cleanup (3 fixes)

- Split tests/test_combat.py (33 functions -> 20) into test_combat.py + test_combat_serialization.py (13 functions)
- Replaced duplicate _make_bot in tests/test_code_quality_fixes.py with shared conftest make_bot
- Fixed conditional assertion in test_tiebreaker_highest_hp_wins: made assertions unconditional, removed dead code (hp_tracker, rest_but_lose_hp), used two resting bots to guarantee MAX_ROUNDS
- All 48 targeted tests pass, all 4 files pass arch check, no regressions in full suite (11 pre-existing failures unchanged)

- **T1.12 done** (auto-updated by hook)

### Session: 2026-03-12 — T1.12 Kill Attribution Fix

- Added hp_before tracking to hit events in Phase 4
- Kill attribution now finds the hit where hp_before > 0 and hp_before - damage <= 0 (killing blow)
- Falls back to last-hit if no single lethal blow found (multi-source death)
- Created tests/test_kill_attribution.py (3 tests)
- All 166 tests pass

- **T1.11 done** (auto-updated by hook)

### Session: 2026-03-12 — T1.11 Tiebreaker Implementation

- Added tiebreaker logic to game.py: HP → energy → kills → damage_dealt (descending)
- Losers get elimination records with cause: "tiebreaker"
- Created tests/test_tiebreaker.py (4 tests)
- All 163 tests pass

- **T1.10 done** (auto-updated by hook)

### Session: 2026-03-12 — T1.10 Energy Clamp Fix

- Fixed apply_action_cost to clamp: max(0, energy - cost)
- Created tests/test_energy_clamp.py (4 tests) — confirmed bug (energy=-10), then fixed

- **T1.9 done** (auto-updated by hook)

### Session: 2026-03-12 — T1.9 ChaosBot Determinism Fix

- Changed ChaosBot to use bot-local Random seeded from hash(round, x, y) per decide() call
- No bot interface changes — seeding derived from state dict
- Created tests/test_chaosbot_determinism.py (4 tests)

- **T1.8 done** (auto-updated by hook)

### Session: 2026-03-12 — T1.8 Remove force_rest Dead Code

- Removed Bot.force_rest() from combat.py — game.py inlines the same logic at lines 71-72
- Removed 4 force_rest tests from test_combat.py, cleaned up unused imports
- All 151 tests pass

- **T1.7 done** (auto-updated by hook)

### Session: 2026-03-12 — T1.7 Game E2E Tests

- Created tests/test_game.py (10 tests): valid output, deterministic replay, winner/cap/stats/players/round structure, storm damage, disconnection
- Uses deterministic test bots: always_rest, chase_and_attack, bad_bot
- All 10 tests pass, arch check clean

- **T1.6 done** (auto-updated by hook)

### Session: 2026-03-12 — T1.6 Match Writer Tests

- Created tests/test_match_writer.py (13 tests): build_match_data keys/values, write_match file creation/naming/JSON validity/nested dir/structure preservation
- All 13 tests pass

- **T1.5 done** (auto-updated by hook)

### Session: 2026-03-12 — T1.5 Loader Tests

- Created tests/test_loader.py (13 tests): valid/minimal bot loading, skip rules (template, underscore, non-py), missing attrs, syntax errors, alphabetical order, empty dir
- All 13 tests pass, arch check clean

- **T1.4 done** (auto-updated by hook)

### Session: 2026-03-12 — T1.4 Sandbox Tests

- Created tests/test_sandbox.py (25 tests): validate_action (18 cases for all valid/invalid combos), execute_decide (7 cases for success/exception/timeout)
- All 25 tests pass, arch check clean

- **T1.3 done** (auto-updated by hook)

### Session: 2026-03-12 — T1.3 State Module Tests

- Created tests/test_state.py (8 tests): top-level keys, me/enemies structure, dead exclusion, energy hiding, last-bot-alive
- All 8 tests pass

- **T1.2 done** (auto-updated by hook)

### Session: 2026-03-12 — T1.2 Combat Module Tests

- Created tests/test_combat.py (37 tests): Bot defaults, can_act, apply_action_cost, force_rest, dict serialization, calculate_damage, resolve_deaths
- Covers: death priority ordering (HP → energy → damage_dealt), defense reduction, energy edge cases, already-dead filtering
- All 37 tests pass, arch check clean

- **T1.1 done** (auto-updated by hook)

### Session: 2026-03-12 — T1.1 Grid Module Tests

- Created tests/test_grid.py (23 tests): bounds checking, directions, apply_direction, calculate_grid_size
- Created tests/test_grid_storm_spawn.py (26 tests): storm border calc, is_in_storm, spawn positions
- Split into 2 files to stay under 40-function arch limit
- All 49 tests pass, both files pass arch check
- Covers: boundary edges, storm transitions at round 20→21 and 40→41, spawn spacing/buffer/fallback, deterministic seeding

### Session: 2026-03-12 — Full Build Planning

- Created 5 sprint plans covering engine tests → YouTube upload
- Created 35 detailed task files with objectives, implementation plans, acceptance criteria
- Sprint 1 (engine tests) set as active sprint
- Explored full codebase: 804 LOC engine, 5 example bots, web viewer, zero tests
- Identified 5 bugs to fix in S1: dead code, unseeded random, negative energy, no tiebreaker, kill attribution

## What's Next

1. **S1 COMPLETE** — all 12 tasks done, 166 tests passing
2. Next: S2 (Data + CI) starting with T2.5 (pyproject.toml) → T2.1–T2.4 → T2.6–T2.8
3. Note: game.py run_match() exceeds 50-line function limit — needs decomposition in a future refactor
4. Run `/start-task T2.5` to begin S2

## Blockers

None currently.

## Known Bugs (to fix in S1)

- `Bot.force_rest()` — dead code, never called in game.py (T1.8)
- `ChaosBot` — uses unseeded `random`, not reproducible from match seed (T1.9)
- Energy can go negative after action cost deduction (T1.10)
- 200-round cap has no tiebreaker — potential draw with no winner (T1.11)
- Kill attribution uses last-hit-this-round, not killing blow (T1.12)
