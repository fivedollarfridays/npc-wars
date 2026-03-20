# Current State

> Last updated: 2026-03-20 S31 complete

## Active Plans

**Plan:** Sprint 32: XP and Leveling System
- **Sprint:** S32 | **Type:** feature | **Status:** Planned (7 tasks, T32.1-T32.7)
- **Part of:** Phase 2 — Depth (S32-S39)
- **Plan ID:** plan-2026-03-s32-xp-leveling

### S32 Tasks

| Task | Title | Cx | Depends On | Status |
|------|-------|----|------------|--------|
| T32.1 | XP calculation engine | 25 | — | done |
| T32.2 | Level progression table | 20 | — | done |
| T32.3 | SQLite player profile persistence | 30 | — | done |
| T32.4 | XP integration into match runner | 25 | T32.1, T32.2, T32.3 | done |
| T32.5 | CLI profile command | 20 | T32.3 | done ✓ |
| T32.6 | Post-match XP summary | 15 | T32.4 | done |
| T32.7 | GATE: XP flow integration test | 20 | all | done |

### S32 Wave Plan

```
Wave 1 (parallel):  T32.1 + T32.2 + T32.3          (75 Cx)
Wave 2:             T32.4 — XP into match runner     (25 Cx)
Wave 3 (parallel):  T32.5 + T32.6                   (35 Cx)
Wave 4:             T32.7 — INTEGRATION GATE          (20 Cx)
```

## Current Focus

S32 complete (7/7 tasks done). All waves finished including integration gate.

## What Was Just Done

**T32.7: GATE -- XP flow integration test** -- Created `tests/test_s32_integration.py` with 25 tests across 8 test classes covering all 7 required scenarios: (1) fresh player flow with real seeded matches, (2) level-up detection from seeded profiles near boundaries, (3) multi-match XP accumulation across 3 matches, (4) exact XP formula verification against hand-crafted match results, (5) profile persistence across DB close/reopen cycles, (6) no-XP flag producing zero side effects, (7) leaderboard ordering by level DESC then XP DESC. Bonus gate checks verify xp_awards key in real match flow, run_match.py imports xp_runner, and engine.xp __all__ exports are non-empty. All tests use in-memory SQLite (or tmp_path for persistence tests). No mocking of core logic. Ruff clean, arch check clean (warning only: 427 lines, under 600 error threshold).

**T32.5: CLI profile command** -- Created `engine/profile_display.py` with `render_progress_bar()` (block-char progress bar with clamping), `format_profile()` (boxed single-player view with name, level, XP bar, match/win/kill stats, cumulative unlocks, next unlock preview), and `format_leaderboard()` (tabular ranked listing). Created `agentgrounds/wars/cli/cmd_profile.py` with `register()`/`run()` pattern: `profile [name]` shows single profile, `profile` (no args) shows top-10 leaderboard, unknown name shows friendly error. Refactored `cli/__init__.py` to extract `_register_subcommands()` helper to stay within 50-line function limit. 19 tests in `tests/test_cli_profile.py`. Ruff clean, arch check clean.

**T32.6: Post-match XP summary** -- Created `engine/xp_display.py` with `format_xp_summary(xp_awards, players)` that produces formatted console output sorted by total XP descending. Shows per-bot XP breakdown (base + kills + survival + win/place + bonus), level-up lines with old/new level and newly unlocked actions/callbacks via `unlocks_at_level()` diffing. Accepts optional players list for emoji-to-name mapping. 15 tests in `tests/test_xp_display.py` across 4 test classes. Ruff clean, arch check clean.

**T32.4: XP integration into match runner** -- Created `engine/xp_runner.py` with `apply_xp_awards()` (calculates XP, persists to profile DB, detects level-ups) and `inject_xp_into_match()` (attaches `xp_awards` field to match result dict, supports `no_xp` flag, auto-creates DB at `data/profiles.db`). Wired into `run_match.py` (with `--no-xp` and `--db-path` flags via argparse) and `agentgrounds/wars/cli/cmd_battle.py` (with `--no-xp` flag). 15 tests in `tests/test_xp_integration.py` covering structure, persistence, level-up detection, no-xp skip, and auto-DB-creation. Ruff clean, arch check clean.

**T32.1: XP calculation engine** -- Created `engine/xp.py` with `XpBreakdown` dataclass (base/kills/survival/placement/bonuses + total property), `calculate_match_xp()` returning per-bot XP breakdown from match result dict, `_placement_xp()` (1st=50, 2nd=25, 3rd=15), `_bonus_xp()` (first blood=20, leader bounty=25). Handles edge cases: no winner, tie placements (same round = shared rank), storm kills excluded from first blood, zero kills/rounds. 26 tests in `tests/test_xp.py`. Pure functions, stdlib only, ruff clean, arch check clean.

**T32.3: SQLite player profile persistence** -- Created `engine/profile_db.py` with 7 public functions: `init_profile_db`, `get_or_create_profile`, `update_profile` (upsert with XP accumulation and level recalc via `level_from_xp`), `get_profile`, `list_profiles`, `get_leaderboard`. Schema uses `CREATE TABLE IF NOT EXISTS` for idempotent init. All writes commit immediately. 22 tests in `tests/test_profile_db.py` using `:memory:` SQLite. Ruff clean, arch check clean.

**T32.2: Level progression table** -- Created `engine/levels.py` with LEVEL_TABLE (levels 1-30 with linear interpolation for gaps), `level_from_xp()`, `xp_for_next_level()`, `xp_to_next_level()`, `LevelUnlocks` dataclass, and `unlocks_at_level()` (cumulative). 15 tests in `tests/test_levels.py`. All pure functions, no I/O.

**Sprint 31 completed (7/7 tasks):**
- T31.3: Tuned stat scaling curves — nerfed dodge (0.3/pt, 20% cap), buffed armor DR (0.25/pt), buffed mind regen (0.6/pt), buffed high-power damage (0.8), added versatility damage bonus (+20 flat), increased versatility HP to 75. Balance: Balanced 49.5%, no archetype >55%.
- T31.4: All builtin bots updated with thematic stat allocations and BOT_GLYPH. 29 new tests.
- T31.5: PROMPT.md rewritten with full v2 docs — stats, combat, archetypes, glyphs, state dict.
- T31.6: Balance regression tests — 16 tests verifying balanced builds produce 145 HP, matches complete in 8-80 rounds, damage/miss/crit rates in expected ranges.
- T31.7: Phase 1 integration gate — 24 tests across 7 classes verifying stat round-trip, combat events, visual identity, balance targets, builtin bots, PROMPT.md, no dead functions.

## What's Next

S32 complete. Ready for S33 planning or PR creation.

## Completed Sprints

| Sprint | Focus | PR | Status |
|--------|-------|-----|--------|
| S1-S18 | Core through Polish | #1-#18 | Done |
| S20-S26 | Experience → King of the Hill | #21 | Done |
| S27 | Stat Budget System | #22 | Done |
| S28 | Roll-Based Combat | #23 | Done |
| S29 | Dodge, Modifiers, Initiative | #24 | Done |
| S30 | Visual Identity | #25 | Done |
| S31 | Balance Tuning + Phase 1 Gate | — | Done |
| S32 | XP and Leveling System | — | Done |
