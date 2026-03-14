# Current State

> Last updated: 2026-03-14 T13.10 done

## Active Plan

**Plan:** NPC Wars v2 — Spectacle, Human Play & The Cringe
**Status:** 6 sprints planned, 70 tasks total. 5 sprints done, 1 remaining.
**Current Sprint:** S12 (The Cringe) — **Done**

## Current Focus

S13 in progress. T13.1, T13.2, T13.3, T13.4, T13.5, T13.6, T13.7, T13.8, T13.9, T13.10 done. Working through helpers DSL and match modes.

## What Was Just Done

**T13.10: E2E Integration Gate -- wizard bot in a full match** -- Created `tests/test_integration_wizard.py` with 7 test functions (10 test cases with parametrization) proving the complete Vibe Wizard pipeline works end-to-end. Tests cover: wizard-generated bot completes a match, all 5 presets complete matches (parametrized), example_vibes.py works in a match, helpers-based bot makes non-trivial decisions (moves/attacks, not just rest), wizard bot coexists with existing bots, and full pipeline smoke test (generate -> write -> validate_bot -> load_bots -> run_match -> check stats). All tests use tmp_path isolation with a dummy "always rest" opponent. 1622 total tests passing. Ruff clean. Arch clean.

**T13.9: Example vibes bot + user docs** -- Created `bots/example_vibes.py` (50 lines) porting the Cognify strategy to the helpers DSL. Six-priority decision tree: storm escape, energy crisis rest, finish kills on adjacent low-HP enemies, defend/counter when adjacent, rest when safe, chase wounded, drift center. Imports `Me`, `Enemies`, `Storm` inside `decide()`. Bot passes `validate_bot.py`. Created `docs/vibe-wizard.md` covering all 3 levels of bot creation (zero-code wizard, vibes DSL, full control) with complete API reference for Me, Enemies, Storm classes and valid actions table with energy costs. 16 tests in `tests/test_example_vibes.py` covering attributes, all 6 priority levels, and validate_bot integration. 1612 total tests passing. Ruff clean. Arch clean.

**T13.8: Scanner & loader compatibility tests** -- Created `tests/test_bot_scanner_helpers.py` with 8 test functions (12 test cases with parametrization) proving npcwars helpers are scanner-safe. Tests cover: helpers import passes scan, helpers.py source has no violations, preset-generated bot passes scan, all 5 presets pass scan (parametrized), wizard-generated bot loads via load_bots(), npcwars not in BLOCKED_MODULES, helpers.py AST has no blocked imports, loaded bot returns valid action tuple. 1612 total tests passing. Ruff clean.

**T13.6: Wizard CLI -- interactive bot generator** -- Created top-level `wizard.py` (251 lines) with argparse-based CLI for generating bot files. Non-interactive mode (`--non-interactive --name X --emoji Y --style Z`) and interactive mode with prompted inputs. Generates complete bot files with BOT_NAME, BOT_EMOJI, BOT_BIO, BOT_AUTHOR constants and `decide()` function using preset body from `npcwars/presets.py`. Input validation (name format, style, slider ranges), name/emoji uniqueness checking against existing bots. Fixed 3 bugs in `npcwars/presets.py`: `enemies.in_range(1)` -> `enemies.adjacent()`, `wounded` list used directly as target -> `wounded[0]` in kiter and opportunist presets. 25 tests in `tests/test_wizard.py`. 1582 total tests passing. Ruff clean.

**T13.7: Package wiring & re-exports** -- Wired `npcwars/__init__.py` with re-exports of `Me`, `Enemies`, `Storm` from `npcwars.helpers`. Added `npcwars*` to `pyproject.toml` packages include list. Created `tests/test_helpers_import.py` with 14 import smoke tests covering direct imports, top-level re-exports, identity checks, preset imports, and callability with mock state. All 1557 tests passing. Ruff clean.

**T13.5: Preset strategies with tuning sliders** -- Created `npcwars/presets.py` (198 lines) with `generate_preset(style, aggression, risk_tolerance)` that produces Python source code for bot `decide()` function bodies. Five playstyles: aggro (chase weakest, attack), tank (defend, counterattack adjacent), kiter (maintain range, flee when approached), opportunist (rest safe, strike wounded), chaos (random weighted actions). Sliders (1-10) adjust thresholds via linear interpolation. All generated code passes `ast.parse()`, contains `from npcwars.helpers import Me, Enemies, Storm`, and has no blocked imports. 53 tests in `tests/test_presets.py`. 1543 total tests passing. Ruff clean. Arch clean.

**T13.3: Helpers -- Enemies class** -- Added `Enemies` class to `npcwars/helpers.py` with `_manhattan()` helper. Methods: `.closest()` (smallest manhattan distance, None if empty), `.weakest()` (lowest hp, None if empty), `.wounded(threshold=50)` (list with hp < threshold), `.adjacent()` (distance exactly 1), `.nearby(radius=2)` (distance <= radius), `.count` property. All return None or [] for empty lists. Added `"Enemies"` to `__all__`. 19 new tests in `tests/test_helpers_enemies.py`. Ruff clean. File at 265 lines.

**T13.2: Helpers -- Me class combat awareness methods** -- Added 7 combat awareness methods to `Me` class in `npcwars/helpers.py`: `dist_to(target)` (manhattan distance, accepts dict or tuple), `attack(enemy)` (returns attack action toward enemy), `adjacent_enemies()` (filters to distance==1), `nearby_enemies(radius=2)` (filters to distance<=radius), `can_kill_adjacent()` (True if any adjacent enemy hp <= attack_power), `weakest_adjacent()` (lowest-hp adjacent or None), `threatened()` (True if adjacent enemies AND hp<40 or outnumbered). Added `_enemies` to `__slots__`, stored in `__init__`. 21 new tests appended to `tests/test_helpers_me.py` (45 total). Ruff clean. File at 265 lines.

## What's Next

Remaining S13 tasks (T13.11-T13.13).

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

## S12 Tasks: The Cringe

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
