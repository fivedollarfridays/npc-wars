# Current State

> Last updated: 2026-03-14 T14.10 done

## Active Plan

**Plan:** NPC Wars v2 — Spectacle, Human Play & The Cringe
**Status:** 6 sprints planned, 70 tasks total. 5 sprints done, 1 remaining.
**Current Sprint:** S12 (The Cringe) — **Done**

## Current Focus

S13 in progress. T13.1, T13.2, T13.3, T13.4, T13.5, T13.6, T13.7, T13.8, T13.9, T13.10 done. Working through helpers DSL and match modes.

## What Was Just Done

**T14.10: E2E integration gate for full CLI pipeline** -- Created `tests/test_cli_e2e.py` (203 lines) with 13 subprocess-based end-to-end tests proving the complete `npcwars` CLI pipeline works: init -> wizard -> validate -> battle. Tests organized in 7 classes: TestInitCreatesValidStructure (4 tests: bots dir, replays dir, config, bot files), TestValidateRejectsBadBot (2 tests: bad syntax, missing decide), TestWizardBotPassesValidate (2 tests: file creation, validation), TestPipelineWithCustomBot (2 tests: validate, battle), TestFullPipelineInitToBattle (1 test: full 5-step pipeline with replay verification), TestBattleWithSeedDeterministic (1 test: same seed same winner), TestBattleReplayHasExpectedKeys (1 test: winner, duration_rounds, players, eliminations keys and types). All tests use subprocess to invoke `python -m npcwars.cli` in tmp_path isolation. 1737 total tests passing (2 pre-existing failures in test_bot_submission.py unrelated). Ruff clean. Arch clean.

**T14.8: Package metadata & LICENSE** -- Added PyPI metadata to `pyproject.toml`: license (MIT), readme, keywords, 7 classifiers (Beta, Developers, Education, MIT, Python 3/3.13, Games), and project URLs (Homepage, Repository, Issues). Created `LICENSE` file with MIT license text (2026, Kevin Masterson). 8 tests in `tests/test_package.py` covering all metadata fields, entry point, LICENSE existence, and MIT content. 1737 total tests passing (2 pre-existing failures in test_bot_submission.py unrelated). Ruff clean. Arch clean.

**T14.9: Community scaffolding + docs** -- Created `suggestions/TEMPLATE.md` (suggestion form with category checkboxes and priority guess), `showcase/README.md` (bot gallery submission guide with rules), rewrote `CONTRIBUTING.md` (three contribution paths: bot showcase, suggestions, bug reports; engine-maintained-by-one-person policy; bot rules table; state dict reference; energy costs), rewrote `README.md` (pip install flow, quick start with npcwars init/wizard/battle, raw bot example, helpers DSL example, game rules, battle options, built-in bots table, MIT license). 13 tests in `tests/test_community_scaffolding.py` covering file existence, content assertions for all four files. Ruff clean. Arch clean.

**T14.7: `npcwars battle` command** -- Created `npcwars/cli/cmd_battle.py` (80 lines) with `register()`, `_resolve_config()`, `_print_summary()`, and `run()` functions. Runs a bot match using existing engine modules (load_bots, run_match, write_match). Supports `--bots-dir` (override bots directory), `--seed` (deterministic matches), and `--replay` (save match JSON). Prints bot roster, winner, round count, and kill feed. Error handling for missing bots dir and fewer than 2 bots. Wired into `npcwars/cli/__init__.py` dispatcher replacing the battle stub. 13 tests in `tests/test_cli_battle.py` covering help output, help shows options, battle exits zero, prints winner, prints rounds, seed determinism, replay JSON creation, replay parseability, replay filepath output, custom bots-dir, missing dir error, fewer-than-2 error, empty dir error. All 10 dispatch tests still pass. Ruff clean. Arch clean.

**T14.4: `npcwars init` command** -- Created `npcwars/cli/cmd_init.py` (57 lines) with `register()` and `run()` functions. Scaffolds a project directory with `bots/`, `replays/`, and `npcwars.toml`. Copies all 6 built-in bots via `npcwars.builtin_bots`. Supports `--dir` flag for target directory (default: cwd) and `--force` flag to overwrite existing files. Idempotent: second run without --force prints skip message and exits cleanly. Wired into CLI dispatcher replacing init stub. 14 tests in `tests/test_cli_init.py` covering directory creation, config validity, bot copying, idempotency, --force overwrite, --dir flag, default cwd, and dispatcher integration. All dispatch tests still pass. Ruff clean. Arch clean.

**T14.6: `npcwars validate` command** -- Created `npcwars/cli/cmd_validate.py` (33 lines) wrapping `scripts.validate_bot.validate_bot()`. Accepts one or more bot file paths, prints PASS/FAIL per file with error details, exits 1 if any fail. Wired into `npcwars/cli/__init__.py` dispatcher replacing the stub handler. 8 tests in `tests/test_cli_validate.py` covering help output, valid bot passes, invalid syntax fails, missing file fails, PASS/FAIL output indicators, multiple valid bots pass, and one-invalid-among-valid fails. All 10 dispatch tests still pass. Ruff clean. Arch clean.

**T14.5: `npcwars wizard` command** -- Created `npcwars/cli/cmd_wizard.py` (44 lines) as a thin wrapper that registers the wizard subcommand with all argparse flags (--non-interactive, --name, --emoji, --style, --aggression, --risk, --bio, --author, --output-dir) and delegates to `wizard.main(argv)`. Wired into `npcwars/cli/__init__.py` dispatcher replacing the stub handler. 8 tests in `tests/test_cli_wizard.py` covering help output, non-interactive bot creation, bot file contents (BOT_NAME, def decide), nested output dir creation, and error cases (invalid style, missing name). All 10 dispatch tests still pass. Ruff clean. Arch clean.

**T14.3: CLI dispatcher skeleton** -- Created `npcwars/cli/__init__.py` (57 lines) as the unified CLI entry point with argparse subcommands (init, wizard, validate, battle), --help, --version. Added `npcwars/cli/__main__.py` for `python -m npcwars.cli` invocation. All subcommands wired to stub handlers that exit non-zero with "Not implemented yet". Added `[project.scripts] npcwars = "npcwars.cli:main"` entry point to `pyproject.toml`. 10 tests in `tests/test_cli_dispatch.py` covering help output, version, all 4 subcommand --help calls, no-args exit, and nonexistent subcommand exit. 1662 total tests passing. Ruff clean. Arch clean.

**T14.1: Built-in bots package** -- Created `npcwars/builtin_bots/` package with `__init__.py` (31 lines) exposing `BUILTIN_NAMES`, `list_builtin_bots()`, and `get_bot_source()`. Copied 5 example bots + template from `bots/` into the package (excludes goose_loose). Uses `importlib.resources` to read bot source at runtime. 19 tests in `tests/test_builtin_bots.py` covering list length, expected names, source content checks, AST parsing of all bots, ValueError on unknown name, and goose_loose exclusion. 1662 total tests passing. Ruff clean. Arch clean.

**T14.2: TOML config reader** -- Created `npcwars/config.py` (48 lines) with three public functions: `default_config()` returns dict with bots_dir, replays_dir, seed defaults; `load_config(path)` reads TOML file and merges with defaults (missing file returns defaults); `write_default_config(path)` writes commented template. Uses stdlib `tomllib`. 11 tests in `tests/test_npcwars_config.py` covering defaults, load from missing file, load with values, merge with defaults, write creates file, write output parseable by tomllib, and round-trip. 1662 total tests passing. Ruff clean. Arch clean.

**T13.10: E2E Integration Gate -- wizard bot in a full match** -- Created `tests/test_integration_wizard.py` with 7 test functions (10 test cases with parametrization) proving the complete Vibe Wizard pipeline works end-to-end. Tests cover: wizard-generated bot completes a match, all 5 presets complete matches (parametrized), example_vibes.py works in a match, helpers-based bot makes non-trivial decisions (moves/attacks, not just rest), wizard bot coexists with existing bots, and full pipeline smoke test (generate -> write -> validate_bot -> load_bots -> run_match -> check stats). All tests use tmp_path isolation with a dummy "always rest" opponent. 1622 total tests passing. Ruff clean. Arch clean.

**T13.9: Example vibes bot + user docs** -- Created `bots/example_vibes.py` (50 lines) porting the Cognify strategy to the helpers DSL. Six-priority decision tree: storm escape, energy crisis rest, finish kills on adjacent low-HP enemies, defend/counter when adjacent, rest when safe, chase wounded, drift center. Imports `Me`, `Enemies`, `Storm` inside `decide()`. Bot passes `validate_bot.py`. Created `docs/vibe-wizard.md` covering all 3 levels of bot creation (zero-code wizard, vibes DSL, full control) with complete API reference for Me, Enemies, Storm classes and valid actions table with energy costs. 16 tests in `tests/test_example_vibes.py` covering attributes, all 6 priority levels, and validate_bot integration. 1612 total tests passing. Ruff clean. Arch clean.

**T13.8: Scanner & loader compatibility tests** -- Created `tests/test_bot_scanner_helpers.py` with 8 test functions (12 test cases with parametrization) proving npcwars helpers are scanner-safe. Tests cover: helpers import passes scan, helpers.py source has no violations, preset-generated bot passes scan, all 5 presets pass scan (parametrized), wizard-generated bot loads via load_bots(), npcwars not in BLOCKED_MODULES, helpers.py AST has no blocked imports, loaded bot returns valid action tuple. 1612 total tests passing. Ruff clean.

**T13.6: Wizard CLI -- interactive bot generator** -- Created top-level `wizard.py` (251 lines) with argparse-based CLI for generating bot files. Non-interactive mode (`--non-interactive --name X --emoji Y --style Z`) and interactive mode with prompted inputs. Generates complete bot files with BOT_NAME, BOT_EMOJI, BOT_BIO, BOT_AUTHOR constants and `decide()` function using preset body from `npcwars/presets.py`. Input validation (name format, style, slider ranges), name/emoji uniqueness checking against existing bots. Fixed 3 bugs in `npcwars/presets.py`: `enemies.in_range(1)` -> `enemies.adjacent()`, `wounded` list used directly as target -> `wounded[0]` in kiter and opportunist presets. 25 tests in `tests/test_wizard.py`. 1582 total tests passing. Ruff clean.

**T13.7: Package wiring & re-exports** -- Wired `npcwars/__init__.py` with re-exports of `Me`, `Enemies`, `Storm` from `npcwars.helpers`. Added `npcwars*` to `pyproject.toml` packages include list. Created `tests/test_helpers_import.py` with 14 import smoke tests covering direct imports, top-level re-exports, identity checks, preset imports, and callability with mock state. All 1557 tests passing. Ruff clean.

**T13.5: Preset strategies with tuning sliders** -- Created `npcwars/presets.py` (198 lines) with `generate_preset(style, aggression, risk_tolerance)` that produces Python source code for bot `decide()` function bodies. Five playstyles: aggro (chase weakest, attack), tank (defend, counterattack adjacent), kiter (maintain range, flee when approached), opportunist (rest safe, strike wounded), chaos (random weighted actions). Sliders (1-10) adjust thresholds via linear interpolation. All generated code passes `ast.parse()`, contains `from npcwars.helpers import Me, Enemies, Storm`, and has no blocked imports. 53 tests in `tests/test_presets.py`. 1543 total tests passing. Ruff clean. Arch clean.

**T13.3: Helpers -- Enemies class** -- Added `Enemies` class to `npcwars/helpers.py` with `_manhattan()` helper. Methods: `.closest()` (smallest manhattan distance, None if empty), `.weakest()` (lowest hp, None if empty), `.wounded(threshold=50)` (list with hp < threshold), `.adjacent()` (distance exactly 1), `.nearby(radius=2)` (distance <= radius), `.count` property. All return None or [] for empty lists. Added `"Enemies"` to `__all__`. 19 new tests in `tests/test_helpers_enemies.py`. Ruff clean. File at 265 lines.

**T13.2: Helpers -- Me class combat awareness methods** -- Added 7 combat awareness methods to `Me` class in `npcwars/helpers.py`: `dist_to(target)` (manhattan distance, accepts dict or tuple), `attack(enemy)` (returns attack action toward enemy), `adjacent_enemies()` (filters to distance==1), `nearby_enemies(radius=2)` (filters to distance<=radius), `can_kill_adjacent()` (True if any adjacent enemy hp <= attack_power), `weakest_adjacent()` (lowest-hp adjacent or None), `threatened()` (True if adjacent enemies AND hp<40 or outnumbered). Added `_enemies` to `__slots__`, stored in `__init__`. 21 new tests appended to `tests/test_helpers_me.py` (45 total). Ruff clean. File at 265 lines.

## What's Next

Remaining S14 tasks. T14.1, T14.2, T14.3, T14.4, T14.5, T14.6, T14.7, T14.8, T14.9, T14.10 done.

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
