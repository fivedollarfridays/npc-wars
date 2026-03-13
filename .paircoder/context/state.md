# Current State

> Last updated: 2026-03-12

## Active Plan

**Plan:** NPC Wars Full Build — 5 Sprints
**Status:** S5 in progress
**Current Sprint:** S5 (YouTube Upload)

## Current Focus

Sprint 5 complete — all T5.1–T5.3 done.

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
| T2.1 | Create data/emoji_claims.py (CRUD, uniqueness) | 25 | feature | done ✓ |
| T2.2 | Create data/leaderboard.py (stats, rankings) | 30 | feature | done ✓ |
| T2.3 | Create data/match_history.py (index, query) | 25 | feature | done ✓ |
| T2.4 | Create scripts/validate_bot.py (CI validator) | 30 | feature | done ✓ |
| T2.5 | Add requirements.txt and pyproject.toml | 10 | chore | done ✓ |
| T2.6 | GitHub Actions CI: lint, test, coverage gate | 25 | feature | done ✓ |
| T2.7 | Bot submission PR template + validation workflow | 20 | feature | done ✓ |
| T2.8 | Add type hints to engine modules | 20 | refactor | done |

### S3: Discord Bot (Active)

| ID | Title | Cx | Type | Status |
|----|-------|----|------|--------|
| T3.1 | Discord bot scaffold: connection, config, commands | 25 | feature | done ✓ |
| T3.2 | Emoji claim system: /claim, /unclaim, /roster | 30 | feature | done ✓ |
| T3.3 | Match announcements: auto-post start/end | 25 | feature | done ✓ |
| T3.4 | Results display: embed with stats, placements | 20 | feature | done ✓ |
| T3.5 | Leaderboard command: /leaderboard with pagination | 20 | feature | done ✓ |
| T3.6 | Message formatter module (testable, no Discord dep) | 25 | feature | done ✓ |

### S4: Video Renderer (Pending)

| ID | Title | Cx | Type | Status |
|----|-------|----|------|--------|
| T4.1 | Grid renderer: Pillow frame, cells, storm overlay | 35 | feature | done ✓ |
| T4.2 | Bot sprites: emoji, HP bars, name labels | 30 | feature | done ✓ |
| T4.3 | Combat effects: hit flash, death, damage numbers | 35 | feature | done ✓ |
| T4.4 | Scoreboard overlay: round counter, kill feed | 25 | feature | done ✓ |
| T4.5 | Video composer: ffmpeg frame-to-MP4 pipeline | 30 | feature | done ✓ |
| T4.6 | Match video CLI: render JSON to MP4 e2e | 25 | feature | done ✓ |

### S5: YouTube Upload (Pending)

| ID | Title | Cx | Type | Status |
|----|-------|----|------|--------|
| T5.1 | YouTube API auth: OAuth2, token storage | 25 | feature | done ✓ |
| T5.2 | Upload pipeline: metadata, thumbnail, tags | 30 | feature | done ✓ |
| T5.3 | Auto-publish CLI: render + upload in one command | 20 | feature | done ✓ |

## What Was Just Done

- **T5.3 done** (auto-updated by hook)

- **T5.3 done** — scripts/publish_match.py: full render→upload pipeline CLI. 19 tests pass, ruff + arch clean. Sprint 5 complete.

- **T5.2 done** (auto-updated by hook)

- **T5.2 done** — youtube/upload.py: build_metadata(), extract_thumbnail() (ffmpeg), upload_video() (MediaFileUpload resumable). 17 tests pass, arch check clean.

- **T5.1 done** (auto-updated by hook)

### Session: 2026-03-13 -- T5.1 YouTube API Auth

- Created youtube/__init__.py and youtube/auth.py
- authenticate(): loads token, refreshes if expired, runs OAuth2 flow on first use
- get_youtube_service(): builds YouTube Data API v3 resource
- refresh_token(): refreshes expired creds and persists to disk
- _load_token(), _save_token(), _run_oauth_flow() helpers
- token.json and client_secrets.json added to .gitignore
- Added google-api-python-client>=2.0, google-auth-oauthlib>=1.0 to dev extras
- tests/test_youtube_auth.py: 10 tests, all mocked (no real API calls)
- 419 tests passing, ruff clean, arch check clean

### Session: 2026-03-12 -- Sprint 4 /reviewing-code fixes

- video/colors.py: added _FONT (shared cached font), HP threshold comment noting divergence from viewer/match.html
- video_sprites/overlay/effects: now import _FONT from colors — single source
- video_effects: removed dead constants (HIT_FLASH_COLOR was RGBA/mismatched, STORM_FLASH_COLOR/MISS_COLOR unused); added HIT_FLASH_OUTLINE (correct RGB); extracted _handle_flash_and_damage to eliminate _handle_attack/_handle_storm copy-paste
- video_grid: replaced _is_storm_tile with engine.grid.is_in_storm; collapsed two draw calls per storm cell into one (fill+outline)
- video_render.encode_frames: now streams frames one-at-a-time to ffmpeg stdin (no bytearray buffer, no O(n²) copies); added schema comment on bots/positions dual-key
- 409 tests passing, ruff clean, arch check clean

### Session: 2026-03-12 -- Sprint 4 /simplify cleanup

- Created video/colors.py: shared HP_HIGH/HP_MID/HP_LOW constants + hp_color() helper
- video_sprites.py: imported hp_color from colors.py, removed duplicate constants + _hp_color(), cached font as module-level _FONT
- video_overlay.py: same — removed duplicated HP constants/_hp_color(), cached _FONT at module level, inline font= locals eliminated
- video_effects.py: cached ImageFont.load_default() as module-level _FONT (was called per-frame)
- video_render.py encode_frames(): replaced proc.wait()+late-stderr-read deadlock pattern with communicate(input=all_bytes) — safe even if stderr fills pipe buffer
- scripts/render_video.py: removed fake progress loop that ran and completed before render_match_video() was called
- All 409 tests still pass, ruff clean, arch check clean

- **T4.6 done** (auto-updated by hook)

### Session: 2026-03-12 -- T4.6 Match Video CLI

- Created scripts/render_video.py: argparse CLI with _parse_args(), _default_output(), _main()
- Accepts match JSON path, optional --output and --fps flags
- Default output: replaces .json with .mp4 (e.g. match_001.json -> match_001.mp4)
- Error handling: missing file -> exit 1, invalid JSON -> exit 1, render failure -> exit 1
- Created tests/test_render_video_cli.py: 6 tests via subprocess (produces mp4, default path, custom path, custom fps, missing input, invalid JSON)
- All 409 tests pass, ruff clean, arch check clean
- Sprint 4 (Video Renderer) plan now complete

- **T4.5 done** (auto-updated by hook)

### Session: 2026-03-12 -- T4.5 Video Composer

- Created video/video_render.py: frames_from_match(), encode_frames(), render_match_video() pipeline
- render_frame() composes grid + sprites + effects + overlay per round
- encode_frames() pipes raw RGB frames to ffmpeg stdin (no temp files), outputs H.264 MP4
- Handles both "bots" and "positions" keys in round data (real match JSON uses "positions")
- H.264 even-dimension padding via _pad_even() helper
- Created tests/test_video_render.py: 6 tests (frames list, count matches rounds, dimensions, creates file, nonzero file, e2e)
- All 403 tests pass, ruff clean, arch check clean

- **T4.4 done** (auto-updated by hook)

- **T4.3 done** (auto-updated by hook)

### Session: 2026-03-12 -- T4.3 Combat Effects

- Created video/video_effects.py: render_effects() with _draw_hit_flash(), _draw_death_marker(), _draw_damage_number() helpers
- Event handlers: _handle_attack (flash + damage number), _handle_death (red X), _handle_storm (flash + damage number)
- Bot positions passed as dict mapping emoji -> (col, row) for cell lookup
- Colors: pale yellow flash outline, red X for death, yellow damage text
- Created tests/test_video_effects.py: 8 tests (returns image, hit flash, death marker, damage number, no events unchanged, multiple events same cell, storm damage, modifies in place)
- All 389 tests pass, ruff clean, arch check clean

- **T4.2 done** (auto-updated by hook)

### Session: 2026-03-12 -- T4.2 Bot Sprite Renderer

- Created video/video_sprites.py: render_bots() with _draw_hp_bar(), _draw_label(), _draw_dead() helpers
- HP bar colors: green (hp>=60), yellow (hp 30-59), red (hp<30), grey background
- Dead bots: grey fill + X cross lines, no HP bar or label
- Labels: emoji or first 2 chars of name, centered in upper cell area
- Created tests/test_video_sprites.py: 8 tests (2 basic, 1 position, 3 HP bar colors, 1 dead, 1 multiple)
- All tests pass, ruff clean, arch check clean

- **T4.1 done** (auto-updated by hook)

### Session: 2026-03-12 -- T4.1 Grid Renderer

- Created video/__init__.py (empty package marker)
- Created video/video_grid.py: render_grid() with _is_storm_tile() and _draw_cells() helpers
- Dark theme palette: safe=blue-grey (30,35,40), storm=dark-red (80,20,20), grid lines, outer border
- Storm tiles determined by distance from nearest edge <= storm_border
- Created tests/test_video_grid.py: 8 tests (4 basics, 4 storm overlay)
- Added Pillow>=10.0 to pyproject.toml dev extras + video extras and requirements.txt
- All 357 tests pass, ruff clean, arch check clean

- **T3.6 done** (auto-updated by hook)

### Session: 2026-03-12 -- T3.6 Pure Formatter Module

- Created discord_bot/formatters.py: format_match_start, format_match_end, format_results, format_leaderboard, format_claim_response, format_unclaim_response
- All functions return plain dicts with keys: title, description, color (hex int), fields, optional footer
- Zero discord.py dependency -- verified by test_no_discord_import (blocks discord in sys.modules)
- Created tests/test_formatters.py: 15 tests across 6 test classes
- All 349 tests pass, ruff clean, arch check clean
- Sprint 3 (Discord Bot) plan now complete

- **T3.5 done** (auto-updated by hook)

### Session: 2026-03-12 -- T3.5 /leaderboard Command

- Created discord_bot/commands/leaderboard.py: build_leaderboard_embed, leaderboard_callback, register_commands
- PAGE_SIZE=10 pagination with page clamping (out-of-range pages clamp to valid range)
- Sort options: wins, kills, win_rate, avg_placement (as app_commands.Choice)
- Callback accepts optional match_data_list for testability (no filesystem in tests)
- Empty data path returns ephemeral "No match data available" message
- Created tests/test_leaderboard_command.py: 8 tests (5 embed, 3 callback)
- All tests pass, ruff clean, arch check clean

- **T3.4 done** (auto-updated by hook)

- **T3.3 done** (auto-updated by hook)

### Session: 2026-03-12 -- T3.3 Match Announcements

- Created discord_bot/announcements.py: build_match_start_embed, build_match_end_embed (sync), announce_match_start, announce_match_end (async)
- Start embed: title with match_id, player emoji roster, competitor count, optional seed field
- End embed: winner in description, duration rounds, last 3 eliminations as "Final Kills"
- Pure formatting functions -- no Discord API calls needed for embed tests
- Created tests/test_announcements.py: 9 tests (4 start embed, 2 end embed, 1 seed omission, 2 async send)
- All 334 tests pass, ruff clean, arch check clean

- **T3.2 done** (auto-updated by hook)

### Session: 2026-03-12 -- T3.2 /claim /unclaim /roster Commands

- Created discord_bot/commands/claims.py: claim_callback, unclaim_callback, roster_callback, register_commands
- Callbacks accept injected state dict for testability (no file I/O in tests)
- unclaim_callback syncs state dict in-place (deletes removed keys)
- roster_callback lists all claims as "emoji -> @user" lines
- register_commands wraps callbacks in @tree.command decorators with guild binding
- Created tests/test_claims_commands.py: 9 tests across 4 test classes
- All tests pass, ruff clean, arch check clean

- **T3.1 done** (auto-updated by hook)

### Session: 2026-03-12 -- T3.1 Discord Bot Scaffold

- Created discord_bot/config.py: load_config() reads BOT_TOKEN, GUILD_ID (required), ANNOUNCEMENT_CHANNEL_ID, RESULTS_CHANNEL_ID (optional) from env vars
- Created discord_bot/bot.py: NpcWarsBot(discord.Client) with CommandTree, setup_hook, on_ready, on_command_error
- Created discord_bot/commands/general.py: ping_callback, help_callback (embed), status_callback, register_commands
- Fixed unused imports in tests/test_discord_bot.py (ruff clean)
- Added discord.py>=2.3 and pytest-asyncio>=0.23 to pyproject.toml and requirements.txt
- 17 tests pass, arch check clean, ruff clean

- **T2.8 done** (auto-updated by hook)

- **T2.8 done**: Added type hints to all 8 engine modules so `mypy engine/ --strict` passes with 0 errors. Created `engine/types.py` with shared TypedDicts. No runtime behavior changes.

- **T2.7 done** (auto-updated by hook)

- **T2.6 done** (auto-updated by hook)

- **T2.5 done** (auto-updated by hook)

- **T2.4 done** (auto-updated by hook)

- **T2.3 done** (auto-updated by hook)

- **T2.2 done** (auto-updated by hook)

- **T2.1 done** (auto-updated by hook)

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
- T2.1: Created data/emoji_claims.py with claim/unclaim/query/persistence CRUD. 21 tests, all passing.
- T2.2: Created data/leaderboard.py with aggregate_stats, get_rankings, get_bot_stats, load_match. 22 tests passing.
- T2.3: Created data/match_history.py with index, pagination, and filtering. 17 tests.
- T2.4: Created scripts/validate_bot.py with syntax/attr/sandbox/timeout validation. CLI exits 0/1. 14 tests.
- T2.5: Added pyproject.toml and requirements.txt. ruff check . passes clean, 269 tests.
- T2.6: Added .github/workflows/ci.yml with lint, test+coverage gate, bot-validate jobs. 11 YAML tests.
- T2.7: PR template, validate-bot.yml workflow, CONTRIBUTING.md. 16 tests.
- T2.8: added type hints to all engine modules (engine/types.py + 8 annotated files), mypy --strict passes with 0 errors, all tests green
- T3.1: Discord bot scaffold complete — NpcWarsBot class, config from env, /ping /help /status commands, error handler, all tests pass
- T3.2: /claim /unclaim /roster commands implemented, 9 tests pass
- T3.3: match start/end announcement embeds, announce_match_start/end async functions, 9 tests pass
- T3.4: /results command with build_results_embed, placements, winner, 7+ tests pass
- T3.5: /leaderboard command with pagination, sort options, 8 tests pass
- T3.6: discord_bot/formatters.py with pure format functions, no discord dep, 15 tests pass
- T4.1: video/video_grid.py render_grid() with storm overlay, 8 tests pass
- T4.2: video/video_sprites.py render_bots() with HP bars, labels, dead overlay, 8 tests pass
- T4.3: video/video_effects.py render_effects() with hit flash, death marker, damage numbers, 8 tests pass
- T4.4: video/video_overlay.py render_overlay() with scoreboard sidebar, round counter, kill feed, 8 tests pass
- T4.5: video/video_render.py render_match_video() frames->MP4 via ffmpeg pipe, 6 tests pass
- T4.6: scripts/render_video.py CLI for match JSON -> MP4, 6 tests pass, Sprint 4 complete


## What's Next

All 5 sprints complete. Ready for /finishing-branches on sprint-5/youtube-upload.


## Blockers

None currently.

## Known Bugs (to fix in S1)

- `Bot.force_rest()` — dead code, never called in game.py (T1.8)
- `ChaosBot` — uses unseeded `random`, not reproducible from match seed (T1.9)
- Energy can go negative after action cost deduction (T1.10)
- 200-round cap has no tiebreaker — potential draw with no winner (T1.11)
- Kill attribution uses last-hit-this-round, not killing blow (T1.12)
