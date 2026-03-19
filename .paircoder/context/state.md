# Current State

> Last updated: 2026-03-19 Phase 1 planned

## Active Plans

**Plan:** Sprint 27: Stat Budget System
- **Sprint:** S27 | **Type:** feature | **Status:** Planned (7 tasks, T27.1-T27.7)
- **Part of:** Phase 1 — Agent Wars v2 Foundation (S27-S31, 35 tasks, 810 Cx)

### S27 Tasks

| Task | Title | Cx | Depends On | Status |
|------|-------|----|------------|--------|
| T27.1 | Stat allocation dataclass + validation | 20 | — | done ✓ |
| T27.2 | Derived stats calculator | 25 | T27.1 | done ✓ |
| T27.3 | Bot class accepts stat allocation | 20 | T27.2 | done ✓ |
| T27.4 | Loader reads stat constants from bot files | 20 | T27.3 | done ✓ |
| T27.5 | State dict exposes stats + enemy hints | 15 | T27.3 | done ✓ |
| T27.6 | Derived stats wired into game loop | 25 | T27.2, T27.3 | done ✓ |
| T27.7 | GATE: 25/25/25/25 matches pre-overhaul | 30 | all | done ✓ |

### S27 Wave Plan

```
Wave 1: T27.1                           (20 Cx)
Wave 2: T27.2                           (25 Cx)
Wave 3: T27.3, T27.4                    (40 Cx)
Wave 4: T27.5, T27.6                    (40 Cx)
Wave 5: T27.7 — INTEGRATION GATE        (30 Cx)
```

## Current Focus

S27: Stat Budget System complete. All 7 tasks done.

## What Was Just Done

- **T27.7 done**: S27 integration gate passed. Created `tests/test_s27_integration.py` with 13 tests across 4 categories: backward compatibility (default 25/25/25/25 bots start at hp=100, energy=100, deal 25 damage, match lasts 15-50 rounds), stat system wiring (custom stat bots get different HP, state dicts expose power/speed/armor/mind and max_hp/speed_class, high-mind bots get energy regen), loader (all builtin bots load, all have DEFAULT_ALLOCATION), and no dead code (all engine.stats.__all__ entries importable and referenced in engine source). All 13 tests pass, 188 S27-related tests pass, ruff clean, arch check clean.

- **T27.6 done**: Wired derived stats into all game loop references. Replaced hardcoded `MAX_HP`/`MAX_ENERGY` caps with `bot.derived.max_hp`/`bot.derived.max_energy` in `engine/rounds.py` (rest healing, kill bounty energy), `engine/bounty.py` (bounty reward restore), `engine/watcher_spawn.py` (HP ratio check), and `engine/watcher_controller.py` (HP ratio calculation). Added MIND energy regen bonus (`bot.derived.energy_regen`) to rest energy restore in `apply_energy_and_rest()`. Updated `FakeBot` in `tests/test_watcher_spawn.py` to include `derived.max_hp`. 10 new tests in `tests/test_derived_wiring.py`, all 106 related tests passing. Ruff clean.

- **T27.5 done**: Updated `Bot.to_self_dict()` to expose stat fields (power, speed, armor, mind) and derived fields (max_hp, max_energy, min_damage, max_damage, dodge_chance, damage_reduction). Updated `Bot.to_enemy_dict()` to include `max_hp` and `speed_class` (qualitative hint). Added `_speed_class()` helper method to Bot. Updated `build_round_record()` in `engine/rounds.py` to include `max_hp` in position data. 10 new/updated tests in `tests/test_combat_serialization.py`, all 18 tests passing. Ruff clean.

- **T27.4 done**: Extended `engine/loader.py` to read `BOT_POWER`, `BOT_SPEED`, `BOT_ARMOR`, `BOT_MIND` from bot modules via `getattr` (defaults to 25). Validates with `validate_allocation()`; on `ValueError`, logs warning and falls back to `DEFAULT_ALLOCATION`. Adds `stat_allocation` key to config dict. Updated `_create_bots()` in `engine/game.py` to pass `stat_allocation` through to `Bot()`. 6 new tests in `tests/test_loader_stats.py`, all passing. Ruff clean.

- **T27.3 done**: Modified `Bot.__init__()` in `engine/combat.py` to accept optional `stat_allocation` parameter. Stores `self.stats` (StatAllocation) and `self.derived` (DerivedStats), wires `self.hp` and `self.energy` from derived stats. Updated `make_bot()` in `tests/conftest.py` to pass through `stat_allocation` and default hp/energy to None (uses derived values). 8 new tests in `tests/test_combat.py` (TestBotStatAllocation class), all passing. Ruff clean, arch check clean (warning only: combat.py at 219 lines).

- **T27.2 done**: Added `DerivedStats` frozen dataclass and `calculate_derived()` function to `engine/stats.py`. Maps raw stat allocation to gameplay values. Default 25/25/25/25 produces exactly current game values (max_hp=100, max_energy=100, avg damage=25, dodge=10%, dr=0, regen=0). 15 new tests (27 total) in `tests/test_stats.py`, all passing, ruff clean.

- **T27.1 done**: Created `engine/stats.py` with `StatAllocation` frozen dataclass (power/speed/armor/mind), constants (STAT_BUDGET=100, STAT_MIN=5, STAT_MAX=80), `DEFAULT_ALLOCATION`, and `validate_allocation()`. 12 tests in `tests/test_stats.py`, all passing, ruff clean, arch check clean.

Planned Phase 1 of Agent Wars v2 one-year overhaul. 5 sprints (S27-S31), 35 tasks, 810 Cx covering stat allocation, roll-based combat, identity system, and balance tuning. Created proposal doc at `docs/proposal-wars-v2-one-year.md`. Created S27 task files (T27.1-T27.7).

## What's Next

S27 complete. Ready for S28 (roll-based combat) or PR/merge.

## Completed Sprints

| Sprint | Focus | PR | Status |
|--------|-------|-----|--------|
| S1-S11 | Core Engine → Human Play | #1-#8 | Done |
| S12-S15 | Watcher, Wizard, Packaging, Viewer | #12 | Done |
| S16 | The Diff View | #13 | Done |
| S17 | Server Layer | #14 | Done |
| S18 | Polish & Production | #18 | Done |
| S20 | Experience Layer | — | Done |
| S21-S24 | Memory, Tournament, Restructure, Combat FX | — | Done |
| S25 | Momentum & Scoring | #21 | Done |
| S26 | King of the Hill | #21 | Done |
