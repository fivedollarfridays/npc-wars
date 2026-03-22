# Current State

> Last updated: 2026-03-22 S35 merged, S36 ready

## Active Plans

**Plan:** Sprint 36: Tactical Items + Ability System
- **Sprint:** S36 | **Type:** feature | **Status:** Planned (6 tasks, T36.1-T36.6)
- **Part of:** Phase 2 — Depth (S32-S39)
- **Plan ID:** plan-2026-03-s36-tactical-abilities

### S36 Tasks

| Task | Title | Cx | Depends On | Status |
|------|-------|----|------------|--------|
| T36.1 | Tactical item execution engine | 30 | — | done |
| T36.2 | power_up callback + use_ability action | 35 | T36.1 | done |
| T36.3 | evolve callback — mid-match adaptation | 20 | T36.2 | done |
| T36.4 | Feed + overlay — tactical and ability FX | 15 | T36.1, T36.2 | done |
| T36.5 | Ability-using example bot + balance sim | 20 | T36.2, T36.3 | done |
| T36.6 | GATE: Tactical + ability integration test | 20 | all | pending |

### S36 Wave Plan

```
Wave 1:             T36.1 — tactical execution engine            (30 Cx)
Wave 2:             T36.2 — power_up + use_ability               (35 Cx)
Wave 3 (parallel):  T36.3 (evolve) + T36.4 (feed/overlay)       (35 Cx)
Wave 4:             T36.5 — mage bot + balance sim               (20 Cx)
Wave 5:             T36.6 — INTEGRATION GATE                     (20 Cx)
```

## Current Focus

T36.5 complete, ready for T36.6 (integration gate).

## What Was Just Done

**T36.5: Ability-using example bot + balance sim** (done)
- Created `bots/example_mage.py` (101 lines): ability-using bot with power_up (Arcane Bolt damage ability), evolve (ability_boost + stat_shift), setup, react, and smart decide logic
- Stats: 15/20/20/45 (mind-focused), equipment: bow + crystal + pendant_of_mind + amulet_of_crit (30/40 credits)
- Created `tools/ability_balance_sim.py` (140 lines): 200-match balance sim that wires power_up/evolve callbacks onto Bot objects via patched _create_bots; unlocks use_ability for all bots
- Ran 200-match sim: no bot exceeds 65% win rate, Mage at 11.1% with 90 games
- Created `tests/test_mage_bot.py` (205 lines, 17 tests): security scan, required attrs, stats sum, equipment validation, decide behavior, power_up validity, evolve validity, ability usage logic
- Created `tests/test_ability_balance_sim.py` (50 lines, 6 tests): sim infrastructure tests
- Created `tests/test_s36_regression.py` (42 lines, 3 tests): no bot > 65%, all bots >= 20 games, mage participates
- All 26 new tests pass, 156 related tests pass, ruff clean

**T36.3: evolve callback -- mid-match adaptation** (done)
- Added "evolve" to CALLBACK_NAMES and CallbackSet in `engine/callbacks.py`
- Added `has_evolved: bool = False` field to Bot in `engine/combat.py`
- Added `check_evolve_trigger()` and `run_evolve_callbacks()` to `engine/callback_runner.py`
- Trigger fires at 3+ kills OR round >= 20, whichever first; fires once per match
- Validates stat_shift (sum to 0, each abs <= 10) and ability_boost (capped at 15)
- Creates new frozen StatAllocation and AbilityDef on apply
- Wired into game loop in `engine/game.py` and `engine/game_async.py` after momentum phase
- Updated `_get_active_callbacks()` to include evolve
- 21 tests in `tests/test_evolve.py`, all passing
- Updated `tests/test_callbacks.py` for new CALLBACK_NAMES constant

**T36.4: Feed + overlay -- tactical and ability FX** (done)
- Added 6 feed formatters to `agentgrounds/wars/cli/feed.py`: tactical_activate, ability_damage, ability_heal, ability_shield, ability_slow, evolve
- Added 3 overlay FX handlers to `agentgrounds/wars/cli/overlay.py`: tactical (lightning on bot tile), ability_damage (crystal on target tile), evolve (DNA on bot tile)
- 11 tests in `tests/test_tactical_feed.py`, all passing
- 42 related tests pass with no regressions, ruff clean
- Note: feed.py function count (24) exceeds 15-function arch limit but was already over before this task; formatters are data-like 3-5 line functions per task spec guidance

**T36.2: power_up callback + use_ability action** (done)
- Created `engine/abilities.py` (206 lines): AbilityDef dataclass, validate_ability, resolve_ability (4 types: damage/heal/shield/slow), tick_ability_effects, tick_ability_cooldowns, resolve_ability_phase, _find_ability_target
- Added `power_up` to CALLBACK_NAMES and CallbackSet in `engine/callbacks.py`
- Added `run_power_up_callbacks()` to `engine/callback_runner.py`
- Added Bot fields: ability, ability_cooldown, ability_uses, ability_shield, ability_shield_rounds, ability_slow, ability_slow_rounds
- Added `use_ability` action to sandbox VALID_ACTIONS (variable args: 0 for self-target, 1 for directional)
- Wired ability_shield DR into AC computation (added to tactical_dr in rounds_combat.py)
- Wired ability_slow into initiative sort key in rounds_combat.py
- Wired ability phase into _resolve_combat_phases, tick at end of round
- Added power_up callback call in game.py and game_async.py after setup callbacks
- Exposed ability info in to_self_dict() and has_ability in to_enemy_dict()
- 33 tests in tests/test_abilities.py, all passing
- Updated test_callbacks.py for new CALLBACK_NAMES constant

## What's Next

T36.6: GATE -- Tactical + ability integration test (final task in S36).

## Completed Sprints

| Sprint | Focus | PR | Status |
|--------|-------|-----|--------|
| S1-S18 | Core through Polish | #1-#18 | Done |
| S20-S26 | Experience → King of the Hill | #21 | Done |
| S27 | Stat Budget System | #22 | Done |
| S28 | Roll-Based Combat | #23 | Done |
| S29 | Dodge, Modifiers, Initiative | #24 | Done |
| S30 | Visual Identity | #25 | Done |
| S31 | Balance Tuning + Phase 1 Gate | #27 | Done |
| S32 | XP and Leveling System | #27 | Done |
| S33 | Callback Infrastructure + Trap Action | #28 | Done |
| S34 | Trap Polish & Balance | #29 | Done |
| S35 | Equipment System | #30 | Done |
