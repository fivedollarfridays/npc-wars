# Current State

> Last updated: 2026-03-14 T11.11 done

## Active Plan

**Plan:** NPC Wars v2 — Spectacle, Human Play & The Watcher
**Status:** All 6 sprints planned, 70 tasks created with full AC
**Current Sprint:** S11 (Human Play & Bounty) — **Done ✓**
**Research Doc:** docs/RESEARCH-spectacle-and-human-play.md

## Current Focus

S11 complete. T11.1, T11.2, T11.3, T11.4, T11.5, T11.6, T11.7, T11.8, T11.9, T11.10, T11.11 done.

## What Was Just Done

**T11.11: Integration Tests -- Human Play** -- Created `tests/test_integration_human.py` with 13 integration tests covering: mock human match completion (async with adapter attached), human_override event emission in sync path (appear when adapter overrides, absent on timeout, absent when same action), async/sync parity with 0 humans, AFK detection through full threshold lifecycle (afk at 3, kicked at 10, reset on input, kicked permanent), and bounty placement (single/multiple humans, no humans). All 1208 tests pass. Integration issue noted: async path (`_execute_round_async`) does not emit `human_override` events unlike the sync path -- overrides are applied silently. Sprint S11 complete.

## What's Next

S11 complete. Ready for next sprint.

## v1 Completed Plans

| Sprint | Plan ID | Focus | Tasks | Status |
|--------|---------|-------|-------|--------|
| S1 | plan-2026-03-s1-engine-tests | Engine Test Coverage | T1.1–T1.12 | Done ✓ |
| S2 | plan-2026-03-s2-data-ci | Data Layer + CI | T2.1–T2.8 | Done ✓ |
| S3 | plan-2026-03-s3-discord-bot | Discord Bot | T3.1–T3.6 | Done ✓ |
| S4 | plan-2026-03-s4-video-renderer | Video Renderer | T4.1–T4.6 | Done ✓ |
| S5 | plan-2026-03-s5-youtube-upload | YouTube Upload | T5.1–T5.3 | Done ✓ |
| S6 | plan-2026-03-s6-prod-hardening | Production Hardening | T6.1–T6.9 | Done ✓ |

## v2 Roadmap

| Sprint | Plan ID | Focus | Tasks | Cx | Status |
|--------|---------|-------|-------|----|--------|
| S8 | plan-2026-03-s8-balance-physics | Balance & Physics | T8.1–T8.11 | 320 | Done ✓ |
| S9 | plan-2026-03-s9-progression | Progression System | T9.1–T9.11 | 325 | Done |
| S10 | plan-2026-03-s10-spectacle | Spectacle & Audio | T10.1–T10.10 | 335 | Done ✓ |
| S11 | plan-2026-03-s11-human-play | Human Play & Bounty | T11.1–T11.11 | 375 | In Progress |
| S12 | plan-2026-03-s12-watcher | The Watcher (🍆) | T12.1–T12.14 | 380 | Planned |
| S13 | plan-2026-03-s13-modes-community | Match Modes & Community | T13.1–T13.13 | 375 | Planned |

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

- **T11.10 done** -- Human Override Events in Match JSON. Extracted `_apply_human_override()` helper from `resolve_decisions()` in engine/rounds.py to handle copilot override + event emission. Changed `resolve_decisions()` return signature from `(actions, forced_rest)` to `(actions, forced_rest, override_events)`. When a human adapter provides a valid action that differs from the bot's original action, appends a `human_override` event with `type`, `player` (emoji), `original` (bot action string), and `override` (human action string). No event when human returns None (timeout), invalid action, or same action as bot. Updated `_execute_round()` in engine/game.py to prepend override_events to round_events. Updated all callers: tests/test_copilot.py (9 tests), tests/test_rounds.py (5 tests). 5 new tests in tests/test_human_events.py. All 1163 tests pass, ruff clean, arch clean (no new violations).

- **T11.4 done** -- Async Tick Loop (Human Input Window). Added `run_match_async()` and `_execute_round_async()` to engine/game.py, plus `_collect_human_override()` helper. Async match delegates to sync `_execute_round` when no humans present; uses async path with `asyncio.gather` + `asyncio.wait_for` for concurrent human input collection when humans attached. Added `get_action_async()` default method to `HumanInputAdapter` ABC (delegates to sync, subclasses override for WebSocket). Fixed pre-existing `resolve_decisions` 3-value unpack in `_execute_round`. 8 tests in tests/test_async_match.py. All 1163 tests pass, ruff clean.

- **T11.6 done** -- Bounty Scaling for Co-op. Added BOUNTY_SCALING dict constant to engine/bounty.py mapping human counts to scaling params (1: full HP/3 rounds, 2: full HP/2 rounds, 3+: no HP/1 round). Added hp_restore field to BountyInfo dataclass (default "full"). Updated place_bounties to auto-scale based on len(human_emojis) using BOUNTY_SCALING (4+ falls back to key 3). Updated claim_bounty to read hp_restore/bonus_damage_rounds from BountyInfo instead of hardcoded values. Updated apply_bounty_reward to skip HP restore when hp_restore="none". 9 new tests added to tests/test_bounty_system.py (16 total). Backward compatible: 1-human matches produce identical results to T11.5. All 1163 tests pass, ruff clean.

- **T11.5 done** -- Bounty Placement & Reward System. Created engine/bounty.py (70 lines) with BountyInfo dataclass (target_emoji, reward="full_restore", bonus_damage_rounds=3), place_bounties(bots, human_emojis) returning BountyInfo list for human-controlled bots (empty list for pure bot matches), claim_bounty(target_emoji, bounties) returning reward dict on match (hp_restore, energy_restore, damage_bonus, bonus_rounds) or None, and apply_bounty_reward(bot, reward) setting HP/energy to max and damage_bonus dict with multiplier/rounds_remaining. Added damage_bonus attribute to Bot class in engine/combat.py. 7 tests in tests/test_bounty_system.py. All 1141 tests pass, ruff clean.

- **T11.3 done** -- Copilot Override Logic in Engine. Added `human_adapter: HumanInputAdapter | None = None` field to `Bot` class in engine/combat.py (with TYPE_CHECKING import to avoid circular deps). Modified `resolve_decisions()` in engine/rounds.py: after bot's `decide()` runs and is validated, checks `bot.human_adapter`; if present, calls `adapter.get_action(state, timeout_s=2.0)` with the same state dict the bot received; if adapter returns a valid action (passes same `validate_action` with unlock gating), replaces bot's decision; if adapter returns None (timeout) or invalid/locked action, keeps bot's original decision. 9 tests in tests/test_copilot.py: human override replaces bot decision (1), override doesn't affect other bots (1), None timeout uses bot fallback (1), no adapter uses bot normally (1), same state dict passed to human (1), invalid action falls back (1), invalid direction falls back (1), locked action falls back (1), unlocked action accepted (1). All tests pass, ruff clean, arch clean.

- **T10.10 done** -- Integration Tests for Spectacle. Created tests/test_integration_spectacle.py (157 lines) with 16 tests covering the full spectacle pipeline end-to-end: spectacle metadata presence in all rounds (2 tests), tier validity and calm-on-zero-events (2 tests), drama score non-negativity (1 test), trigger-effect consistency for kill/shatter, kill_streak/fire_border, near_death/slow_mo, chain_bump/multiball (4 tests), zero-score calm baseline (1 test), build_audio_timeline returns list of (timestamp_ms, path) tuples (2 tests), build_hype_volume_curve returns one entry per round with volumes in [0.0, 1.0] (2 tests), render_match_video accepts audio param defaulting to True (2 tests). Uses seeded run_match with 6 bots (mix of chase_and_attack and always_rest). All 1013 tests pass, ruff clean.

- **T10.5 done** -- Three-Layer Audio Mixer for Video. Created audio/mixer.py (56 lines) with TIER_VOLUMES dict (calm=0.1, heating=0.3, intense=0.5, hype=0.8, chaos=1.0), build_audio_timeline(match_data, round_duration_ms) returning sorted (timestamp_ms, audio_file_path) tuples from round events via get_stinger_path, and build_hype_volume_curve(match_data, round_duration_ms) returning (timestamp_ms, volume) keyframes from spectacle tier per round. Created audio/renderer.py (47 lines) with mux_audio_into_video (ffmpeg silent stereo AAC mux via anullsrc) and has_audio_stream (ffprobe check). Updated audio/__init__.py to export mixer symbols. Wired into video/video_render.py: render_match_video gained audio=True param, encodes to temp file then mux_audio_into_video. Updated scripts/render_video.py with --no-audio flag. 15 tests in tests/test_audio_mixer.py across 3 classes (TestBuildAudioTimeline, TestBuildHypeVolumeCurve, TestTierVolumes). All 997 tests pass, ruff clean.

- **T10.9 done** -- Hype Track Escalation System. Created audio/hype.py (149 lines) with HYPE_TRACKS dict (3 intensities: ambient, mid, peak), INTENSITY_VOLUMES, _TIER_TO_INTENSITY mapping, select_hype_track(tier) returning {track, volume, intensity}, and build_hype_timeline(match_data) producing crossfade events on tier transitions (CROSSFADE_MS=500, no event when consecutive rounds share intensity). 3 hype WAV generators: _gen_hype_ambient (gentle sine harmonics at 55/110/165Hz), _gen_hype_mid (sine+square mix at 110/220Hz), _gen_hype_peak (rapid modulated square at 330Hz). Auto-generates 3 WAV assets (~40KB each, 5s at 8kHz) on import if missing. 14 tests in tests/test_hype.py across 3 classes (TestSelectHypeTrack, TestHypeTracks, TestBuildHypeTimeline). All 71 audio tests pass, ruff clean.

- **T10.8 done** -- Web Audio Integration in Viewer. Added AudioEngine class to viewer/match.html with Web Audio API: init() creates AudioContext + master gain node, loadStinger() fetches and decodes WAV buffers, play(eventType, tier) plays buffers with tier-based volume scaling (calm=0.3 to chaos=1.0), setMasterVolume/mute/unmute/toggleMute for volume control. Added audio controls UI (mute button + volume slider) in controls bar. Wired into initViewer() (init + load 13 stingers from audio/assets/) and renderRound() (play stingers for each event). Volume persisted to localStorage as 'npc-wars-volume'. 12 structural tests in tests/test_viewer_audio.py verify class definition, methods, UI elements, CSS, global instance, renderRound integration, and localStorage persistence. All tests pass, ruff clean, arch clean.

- **T10.6 done** -- Viewer Spectacle FX (CSS/JS). Added 4 CSS @keyframes animations to viewer/match.html: screen-shake (translate offset), fire-border (inset box-shadow pulse), subtle-pulse (slight scale), slow-mo-flash (brightness/saturation). Added .spectacle-banner class with banner-fade animation for overlay text. Added applySpectacleEffects(tier, triggers, effects) JS function: clears previous effects, applies tier-based animations (heating=subtle-pulse, intense/hype/chaos=screen-shake on kill, hype/chaos=fire-border), slow_mo filter, and trigger-based banners (UNSTOPPABLE, MULTI-BUMP, FINAL SHOWDOWN). Added showBanner(text, color) helper. Wired into renderRound() via round.spectacle metadata. 6 structural tests in tests/test_viewer_spectacle.py verify function definitions, CSS keyframes, banner class, and renderRound integration. All 956 tests pass, ruff clean.

- **T10.7 done** -- Video Renderer Spectacle FX. Added `render_spectacle_effects()` to `video/video_effects.py` with 3 helpers: `_apply_screen_shake` (pixel offset by 2-4px for intense+ tier with kill/kill_streak triggers), `_apply_fire_border` (orange-red gradient rectangles on edges for hype+ tier), `_apply_damage_flash` (red RGBA overlay with tier-scaled opacity: heating=25, intense=50, hype=100, chaos=150). Returns `(image, slow_mo)` tuple; slow_mo=True when near_death in triggers. Wired into `render_frame()` in `video/video_render.py` after overlay step; `frames_from_match()` duplicates slow-mo frames. 8 tests in `tests/test_video_spectacle.py`: calm unchanged, screen shake shifts pixels, fire border changes edges, damage flash increases red avg, intensity scales (chaos > heating), None spectacle unchanged, slow_mo flag on/off. All 22 video tests pass, ruff clean.

- **T10.3 done** -- Spectacle Metadata in Match JSON. Wired SpectacleEngine into run_match() in engine/game.py: imports SpectacleEngine, creates instance before round loop, calls score_round() after each _execute_round() with bot states converted to dict format, adds spectacle dict (drama_score, tier, triggers, effects) to round_data. 4 new tests in tests/test_game.py TestSpectacleMetadata class: every round has spectacle key, required fields have correct types, existing round fields preserved (no regressions), calm rounds have spectacle with drama_score=0/tier="calm". All 15 test_game.py tests pass, ruff clean, arch clean.

- **T10.4 done** -- Stinger Audio Asset Library. Created audio/ package with hub-and-spoke structure: audio/__init__.py (hub exports), audio/stingers.py (STINGER_MAP dict + get_stinger_path helper + auto-generation on import), audio/waveforms.py (4 primitives: sine/square/noise samples + decay envelope), audio/generators.py (13 event-specific generators using waveforms). All 13 WAV stinger files auto-generated as 8-bit mono 8kHz PCM: hit (0.3s square burst), critical_hit (0.5s low square), kill (0.8s noise burst), kill_streak (1.0s rising sine), bump (0.2s high ping), chain_bump (0.5s descending pings), wall_splat (0.4s low noise), storm_damage (0.3s freq sweep), rest_heal (0.3s sine chime), near_death (0.5s low tone), watcher_spawn (1.5s harmonic chord), human_enter (1.0s noise sweep), match_end (2.0s rising chord). Total assets 88KB (well under 5MB cap). 57 tests in tests/test_audio.py across 3 classes (TestStingerMap, TestGetStingerPath, TestAudioAssets): map size, all 13 keys present, WAV filenames, known/unknown path lookup, file existence, nonzero size, total size cap, RIFF header validation. 938 total tests pass, 0 regressions, ruff clean, arch clean.

- **T10.1 + T10.2 done** -- SpectacleEngine drama scoring and trigger-to-effect map. Created engine/spectacle.py (159 lines) with SpectacleData dataclass, DRAMA_WEIGHTS/TIER_RANGES/TRIGGER_EFFECT_MAP constants, and SpectacleEngine class (score_round, classify_tier, select_effects). Drama scoring: kill=3, chain_bump=2, near_death=4, kill_streak=5, watcher_sync=3. Tier classification: calm(0-3), heating(4-7), intense(8-12), hype(13-18), chaos(19+). Trigger-to-effect mapping: kill->shatter, kill_streak->fire_border, near_death->slow_mo, chain_bump->multiball, last_2->split_screen, storm_kill->glitch. Near-death detection for bots with 0<hp<5 and alive=True. Kill streak detection via explicit event OR 3+ kills by same attacker. 32 tests in tests/test_spectacle.py (235 lines), ruff clean, arch clean.

- **T9.11 done** (auto-updated by hook)

- **T9.11 done** -- Integration Tests: Progression. Created tests/test_integration_progression.py with 23 tests across 7 test classes: TestProfilePersistence (3 tests: persist after run_match, winner profile updated, multiple matches accumulate), TestLineBudgetProgression (3 tests: default budget 50, budget +10 per win, cap at 200), TestStreakTracking (3 tests: consecutive wins build streak, loss resets current preserves best, streak bonuses applied), TestActionUnlockFlow (4 tests: base-only, unlocked ranged accepted, locked ranged rejected, dash lock/unlock), TestNewActionsInMatch (4 tests: ranged/dash/taunt matches run clean, result keys), TestLineBudgetEnforcement (3 tests: count_decide_lines, validate over budget raises, validate under budget passes), TestStateDictProgression (3 tests: unlocked_actions/line_budget/win_streak in state dict). 849 total tests pass (826+23), arch clean. Sprint 9 complete.

- **T9.10 done** (auto-updated by hook)

- **T9.9 done** (auto-updated by hook)

- **T9.10 done** -- Profile Update on Match End. Added `update_profiles_after_match(profiles_path, players, winner_emoji)` to `data/player_profiles.py`: loads profiles, creates missing ones via get_or_create_profile, updates streaks and wins/budget for all players, saves to disk. Added optional `profiles_path: Path | None = None` parameter to `run_match()` in `engine/game.py` -- when provided, calls update_profiles_after_match after match completes; defaults to None for backward compatibility. 9 tests in `tests/test_profile_match_update.py` (3 winner/loser updates, 1 budget recalc, 1 disk write, 1 new bots created, 1 existing profiles preserved, 2 run_match integration), 0 regressions, 826 total pass, arch clean.

- **T9.9 done** -- State Dict Unlocks & Budget Fields. Added `unlocked_actions: list[str]`, `line_budget: int`, `win_streak: int` progression fields to `Bot.__init__()` in engine/combat.py with defaults (base 4 actions, budget=50, streak=0). Updated `to_self_dict()` to include all three fields (unlocked_actions as a copy). Updated `SelfInfo` TypedDict in engine/types.py with new fields. Wired `bot.unlocked_actions` into `validate_action()` call in engine/rounds.py `resolve_decisions()`. Added optional progression config passthrough in `_create_bots()` in engine/game.py. 13 tests in tests/test_state_progression.py (3 unlocked_actions, 2 line_budget, 2 win_streak, 3 defaults, 3 TypedDict), fixed 1 regression in test_combat_serialization.py, 826 total pass, arch clean.

- **T9.8 done** (auto-updated by hook)

- **T9.3 done** (auto-updated by hook)

- **T9.3 done** -- Line Budget Enforcement in Bot Scanner. Added `count_decide_lines(source)` to engine/bot_scanner.py: AST-parses source, finds first `def decide()`, counts executable lines in body (excludes blanks, comments, docstrings). Added `validate_line_budget(source, budget)` that raises ValueError when count exceeds budget. Added `_check_semicolons()` that detects semicolon statement chaining in decide() body (string-aware via regex stripping), wired into `scan_bot_source()`. Both new public functions added to `__all__`. 13 tests in tests/test_line_budget_enforcement.py (3 basic counting, 4 exclusions, 3 budget validation, 3 semicolon detection), 0 regressions in existing scanner tests, 804 total pass, arch clean.

- **T9.8 done** -- Action Unlock Gating in Sandbox. Added `BASE_ACTIONS` frozenset (move, attack, rest, defend) and `ACTION_UNLOCK_THRESHOLDS` dict (ranged_attack:3, dash:5, taunt:10) to engine/sandbox.py. Extended `validate_action()` with optional `unlocked_actions: set[str] | None` parameter -- when provided, non-base actions must be in the set or they return None (same as invalid). Default None preserves full backward compatibility. Added both constants to `__all__`. 15 tests in tests/test_action_unlock.py (2 constant, 4 base-always-allowed, 3 locked-rejected, 3 unlocked-accepted, 3 backward-compat), 0 regressions in existing sandbox/ranged/taunt/dash tests, arch clean.

- **T9.6 done** (auto-updated by hook)

- **T9.4 done** (auto-updated by hook)

- **T9.2 done** (auto-updated by hook)

- **T9.6 done** -- Dash Action. Added DASH_COST=15 constant to engine/combat.py and ACTION_COSTS dict. Added "dash": 1 to VALID_ACTIONS in engine/sandbox.py. Updated validate_action() direction check to include "dash". Implemented dash handling in resolve_movement() in engine/rounds.py: computes 2-tile destination, clamps to 1 tile if second tile is OOB, skips entirely if first tile is OOB, generates dash events with from/to coordinates, integrates with bumper physics via movers list. 12 tests in tests/test_dash.py (2 validation, 2 cost, 4 movement/edge, 4 bump integration), 776 total pass, arch clean.

- **T9.4 done** -- Win Streak Calculator. Added `update_streak(profile, is_winner)` to `data/player_profiles.py`. Win increments `current_streak` and updates `best_streak` if new record. Loss resets `current_streak` to 0 while preserving `best_streak`. Added to `__all__`. 7 tests in `tests/test_win_streak.py`, no regressions in existing player profile tests, arch clean.

- **T9.2 done** -- Line Budget Tracking. Added BUDGET_BASE=50, BUDGET_CAP=200, BUDGET_PER_WIN=10, BUDGET_STREAK_REWARDS={3:15, 5:25, 10:50}, BUDGET_WATCHER_BONUS=20 constants to data/player_profiles.py. Implemented calculate_line_budget() (base + wins*10 + highest streak bonus + watcher_wins*20, capped at 200) and update_after_match() (increments wins/watcher_wins for winners, recalculates budget; no-op for losers). 15 tests in tests/test_line_budget.py, no regressions in test_player_profiles.py, arch clean.

- **T9.7 done** (auto-updated by hook)

- **T9.5 done** (auto-updated by hook)

- **T9.1 done** (auto-updated by hook)

- **T9.5 done** -- Ranged Attack Action. Added RANGED_ATTACK_COST=20, RANGED_ATTACK_DAMAGE=15 constants to engine/combat.py. Added "ranged_attack": RANGED_ATTACK_COST to ACTION_COSTS, "ranged_attack": 1 to VALID_ACTIONS in sandbox.py. Updated validate_action() direction check to include "ranged_attack". Implemented resolve_ranged_attacks() in engine/rounds.py (targets tile at distance 2 in direction, fixed 15 damage ignoring attack_power, emits ranged_hit/ranged_miss events). Wired into _execute_round() in game.py after regular attacks. 13 tests in tests/test_ranged_attack.py, 724 total pass, arch clean.

- **T9.7 done** -- Taunt Action. Added TAUNT_COST=10, TAUNT_RANGE=2 constants to engine/combat.py. Added "taunt": TAUNT_COST to ACTION_COSTS, "taunt": 0 to VALID_ACTIONS in sandbox.py. Added self.taunt_target: str | None = None to Bot.__init__. Implemented resolve_taunt() in engine/rounds.py (sets taunt_target on bots within Manhattan distance 2 of taunter, returns taunt events). Added _direction_toward() helper and _apply_taunt_override() for redirecting taunted bot attacks toward taunter in resolve_decisions(). Wired resolve_taunt into _execute_round in game.py (after movement, before attack resolution). 18 tests in tests/test_taunt.py, 742 total pass, arch clean.

- **T9.1 done** -- Player Profile Schema & Storage. Created data/player_profiles.py with PlayerProfile dataclass (player_id, bot_name, emoji, line_budget=50, wins, streaks, unlocked_actions, watcher stats). Implemented load_profiles() (JSON deserialize, graceful error handling for missing/corrupt files), save_profiles() (JSON serialize via asdict, creates parent dirs), get_or_create_profile() (returns existing or creates with defaults). Added profiles.json to .gitignore. 10 tests in tests/test_player_profiles.py, arch clean on both files.

- **T8.11 done** (auto-updated by hook)

- **T8.11 done** -- Final integration test sweep for Sprint 8. Created tests/test_integration_v2.py with 20 tests across 7 test classes: TestBalanceConstants (3 tests verifying ATTACK_POWER=25, ATTACK_COST=10, REST_HEAL=5), TestStormTiming (2 tests verifying no storm before R10, border>=1 by R14), TestDamageScaling (3 tests verifying bonus at R15/R25/R35), TestKillBounty (1 test verifying bounty=30), TestBumperConstants (1 test verifying WALL_SPLAT_DAMAGE=10), TestStateDictBumps (2 tests verifying bumps_this_round field in state dict), TestFullMatchIntegration (8 tests: match completion, result keys, storm border growth, bump physics no-crash, late-round scaling, kill events, elimination attribution, determinism). 701 total tests pass (681+20), arch clean on all Sprint 8 files. Sprint 8 complete.

- **T8.8 done** -- Added `bumps_this_round` to state dict so bots can react to bump events. Added optional `bumps_this_round` param to `build_state()` in engine/state.py (defaults to empty list). Updated `GameState` TypedDict in engine/types.py with `bumps_this_round: list[Event]`. Threaded bump events through: `resolve_decisions()` in rounds.py accepts `bumps_last_round`, `_execute_round()` in game.py accepts and passes it, `run_match()` tracks bump events from previous round via `last_bump_events` accumulator. 3 new tests in tests/test_state.py, 681 total pass, arch clean.

- **T8.10 done** (auto-updated by hook)

- **T8.10 done** -- Viewer bump animations in viewer/match.html. Added 3 CSS keyframe animations (wallSplat, stormBounce, bumpArrow). Added directionArrow() helper mapping direction strings to Unicode arrows (→←↑↓↗↘↙↖). Extended event rendering loop with bump (orange directional arrow on target tile), wall_splat (red flash + damage number), and storm_bounce (purple flash + damage number) cases. Extended updateKillFeed() with bump/wall_splat/storm_bounce descriptions using textContent (no innerHTML injection). 10 new structural tests in tests/test_viewer_bump_events.py, 681 total pass, arch clean.

- **T8.9 done** -- Updated seed bot energy thresholds for ATTACK_COST=10. Changed `energy >= 15` to `energy >= 10` in bots/example_kiter.py (_handle_adjacent) and bots/example_tank.py (counterattack). Verified goose_loose.py rest threshold (energy < 20) and example_aggro.py (energy < 5) are fine as-is. All bots handle bumps_this_round key without crash. 14 new tests in tests/test_seed_bots.py (2 kiter threshold, 2 tank threshold, 5 valid-action parametrized, 5 bumps-key parametrized). 681 total pass, arch clean.

- **T8.4 done** (auto-updated by hook)

- **T8.4 done** -- Gate task: all test regressions from balance changes already fixed. 654 tests pass (exceeds 622 baseline). No tests deleted. All regressions were fixed during T8.1-T8.3 and T8.5-T8.6 implementation.

- **T8.7 done** -- Wired bumper physics into resolve_movement() in engine/rounds.py. Changed signature to return list[_Event] with optional all_bots and storm_border params (backward-compatible defaults). Collects intended moves before updating positions, calls resolve_bumps(), then applies position updates. Updated _execute_round() in engine/game.py to pass all_bots/storm_border and prepend bump events before attack events. 5 new tests in tests/test_bumper_integration.py (bump event return, empty tile no bumps, wall splat HP damage, bump events in round record, position regression guard). 654 total pass, arch clean.

- **T8.6 done** (auto-updated by hook)

- **T8.5 done** (auto-updated by hook)

- **T8.3 done** (auto-updated by hook)

- **T8.5 done** -- Kill bounty: +30 energy on combat kill. Added KILL_BOUNTY_ENERGY=30 constant to engine/combat.py and __all__. Wired into attribute_kills() in engine/rounds.py: killer gets min(energy + 30, MAX_ENERGY) after b.kills += 1. Storm and unknown kills do not award bounty. 5 new tests in tests/test_kill_bounty.py, 649 total pass, arch clean.

- **T8.6 done** -- Bumper physics core in engine/bumpers.py. resolve_bumps() handles collision detection, knockback in movement direction, chain resolution (max depth 5), wall splat damage (WALL_SPLAT_DAMAGE=10), storm bounce damage, cycle prevention via visited set, dead bot skipping. Added WALL_SPLAT_DAMAGE constant to engine/combat.py __all__. 7 helper functions across 6 test classes (9 tests), 649 total pass, arch clean.

- **T8.1 done** -- Balance constants update to fix passive meta. STARTING_ATTACK_POWER 15->25, ATTACK_COST 15->10, REST_HEAL 10->5. ACTION_COSTS["attack"] auto-updated via variable reference. Updated literal assertion in test_combat.py (==15 to ==25). Added TestBalanceConstants class with 4 tests verifying new values. Fixed 4 regression tests in test_game.py and test_tiebreaker.py that assumed resting bots survive to 200 rounds (patched storm to 0 since those tests exercise tiebreaker logic, not storm). 627 tests pass, arch clean.

- **T8.2 done** (auto-updated by hook)

- **T8.3 done** -- Damage scaling: added `get_round_bonus_attack()` to engine/combat.py (+2 attack per 10 rounds after R15). Wired into `_execute_round()` in engine/game.py to apply scaling to all alive bots before decisions. 8 new tests (7 unit + 1 integration) in tests/test_damage_scaling.py. 638 tests pass (2 pre-existing kill_bounty failures unrelated), arch clean.

- **T8.2 done** -- Storm timing rework in engine/grid.py: `get_storm_border()` now starts storm at round 10 instead of 21. New schedule: rounds 1-9 no storm, rounds 10-29 closing phase (1 tile per 5 rounds), rounds 30+ endgame (1 tile per 2 rounds from border=4). Updated all 12 tests in TestGetStormBorder to match new schedule. 27 storm/spawn tests pass, 23 grid tests pass, arch clean.

- **T7.4 done** -- youtube/upload.py: added `base_dir` parameter to `extract_thumbnail()` with `_validate_path()` helper. Validates both `video_path` and `output_path` resolve within `base_dir` (blocks `../` traversal and symlink escapes). `base_dir=None` (default) preserves backward compatibility. 5 new tests in TestPathTraversalGuard, 622 total pass, arch clean.

- **T7.1 done** -- Bot scanner security hardening. Added `_BLOCKED_DUNDER_ATTRS` frozenset (8 attrs: `__globals__`, `__builtins__`, `__subclasses__`, `__mro__`, `__bases__`, `__class__`, `__code__`, `__closure__`). New `_check_dunder_attrs()` walks AST for dangerous attribute access chains. Expanded `BLOCKED_MODULES` with 7 new modules (builtins, io, pathlib, pickle, http, urllib, asyncio). 19 new tests in TestDunderAttrBlocking + updated blocklist parametrize. 622 total tests pass, arch clean.

- **T7.5 done** -- youtube/auth.py: added `_warn_if_tracked(path)` helper that runs `git ls-files` to detect git-tracked secret files and emits a `log.warning` if found. Gracefully handles missing git binary and timeouts. Wired into `authenticate()` to check both client_secrets_path and token_path on every call. Added `import logging`, `import subprocess`, `log = logging.getLogger(__name__)`. 4 new tests in TestWarnIfTracked class, 16 total auth tests pass, arch clean.

- **T7.3 done** -- Discord command authorization and rate limiting. Added `@app_commands.default_permissions(manage_guild=True)` to `/run_match` in match_runner.py (restricts to server admins by default). Added `@app_commands.checks.cooldown(1, 5.0)` to both `/claim` and `/unclaim` in claims.py (prevents spam). 4 new AST-based tests verify decorators are present and configured correctly. 33 tests pass across both test files, arch clean.

- **T7.2 done** — Viewer XSS sanitization in viewer/match.html. Added `sanitize(str)` helper (DOM-based textContent/innerHTML escaping) and `validateMatchPath(path)` helper (regex whitelist for `results/match_NNN.json`). Applied sanitize() to innerHTML assignments in `buildBotList()` (p.emoji, p.name) and `updateKillFeed()` (evt.attacker, evt.victim). Applied validateMatchPath() to both fetch calls (`loadDemo()` and window load auto-load) to block arbitrary URL fetches.

- **Refactor: test helper dedup + BotDeps dataclass** -- Extracted `make_mock_interaction()` and `make_bot_config()` to tests/conftest.py, replacing 5 duplicate local `_make_interaction` helpers across test files. Created `BotDeps` dataclass in discord_bot/bot.py to replace 4-parameter sprawl on `NpcWarsBot.__init__()`. Backward-compatible properties maintained. Updated scripts/run_bot.py and all affected test files. 76 targeted tests pass, no regressions.

- **Review fixes: deduplicate bot module loading** -- (1) scripts/run_bot.py: deduplicated _PROJECT_ROOT computation; moved before sys.path.insert. (2) engine/bot_scanner.py: added load_bot_module() shared helper that runs AST pre-scan then importlib load. (3) engine/loader.py: replaced inline scan+importlib with load_bot_module call, removed importlib imports. (4) scripts/validate_bot.py: removed _load_module and separate scan_bot_file call, replaced with load_bot_module. 6 new tests in test_load_bot_module.py, 75 tests pass across 4 test files, arch clean.

- **Review fixes (bot_scanner + leaderboard N+1)** -- (1) bot_scanner.py: reduced false positives on ast.Attribute nodes. Only ast.Name nodes flagged for BLOCKED_CALLS; ast.Attribute nodes only flag `__import__`. Added _BLOCKED_ATTR_CALLS frozenset. 6 new tests in TestAttributeCallFalsePositives. (2) match_history.py: added get_all_matches() for single-pass full match loading. Leaderboard command updated to use it instead of list_matches+get_match N+1 pattern. 6 new tests in TestGetAllMatches. 79 tests pass across 3 files.

- **Review fixes applied** -- 4 items: (1) play.py: replaced hand-rolled get_next_match_id with shared `from data.match_history import next_match_id`. (2) match_history.py: optimized next_match_id to parse filenames via regex instead of reading/parsing all JSON files. (3) match_history.py: added parameterized type hints (`dict[str, Any]`) to all public functions + `from typing import Any`. (4) publish_match.py: removed TOCTOU os.path.exists check, consolidated into try/except FileNotFoundError in the JSON loading block. 6 new next_match_id tests, 50 total tests pass across both files.

- **T6.7 done** (auto-updated by hook)

- **T6.7 done** (auto-updated by hook)

- **T6.7 done** -- discord_bot/commands/match_runner.py: /run_match slash command. Loads bots via load_bots(), runs match in asyncio.to_thread() (non-blocking), saves via write_match(), posts winner announcement via followup. Auto-increments match_id from existing results. Optional seed parameter. 60s cooldown via app_commands.checks.cooldown(). Wired into bot.py setup_hook and scripts/run_bot.py launcher. 11 new tests, 558 total pass, arch clean.

- **T6.5 done** (auto-updated by hook)

- **T6.8 done** (auto-updated by hook)

- **T6.5 done** -- engine/discord_integration.py: thin integration layer with notify_match_start/notify_match_end. Graceful degradation when discord.py missing, BOT_TOKEN unset, or ANNOUNCEMENT_CHANNEL_ID unset. All exceptions swallowed silently. Wired into engine/game.py run_match() before loop and after build_match_data. 13 new tests, 547 total pass, arch clean.

- **T6.9 done** (auto-updated by hook)

- **T6.8 done** -- Type hint completion + sandbox error logging. Parameterized all 7 bare `dict` in emoji_claims.py to `dict[str, str]`. Parameterized dicts in leaderboard.py with `dict[str, Any]`. Added logging to sandbox.py: log.warning on timeout, process death, and bot exceptions. 2 new tests, 547 total pass.

- **T6.9 done** (auto-updated by hook)

- **T6.6 done** (auto-updated by hook)

- **T6.6 done** — Claims state persistence wired end-to-end. claim_callback/unclaim_callback accept optional claims_path; save_claims() called after every successful mutation, skipped on failure. register_commands, NpcWarsBot, and create_bot all thread claims_path through. 6 new tests (5 persistence + 1 roundtrip), 547 total pass, arch clean.

- **T6.9 done** — scripts/render_video.py: added fps bounds validation (1-60), exits 1 on out-of-range. scripts/publish_match.py: canonicalize match_json via pathlib.Path.resolve() before deriving video_path. 7 new tests, 547 total pass.

- **T6.2 done** (auto-updated by hook)

- **T6.4 done** (auto-updated by hook)

- **T6.4 done** — scripts/run_bot.py: Discord bot launcher with full command wiring. NpcWarsBot.__init__() accepts results_dir and claims_state. setup_hook() wires all 4 command modules. Launcher loads config, claims from disk, creates bot, runs it. 14 new tests, 519 total pass.

- **T6.3 done** (auto-updated by hook)

- **T6.3 done** — youtube/auth.py: token file permissions set to 0o600 after save. discord_bot/bot.py: error handler sends generic message, logs full exception server-side. 5 new tests, 33 auth+bot tests pass.

- **T6.1 done** (auto-updated by hook)

- **T6.1 done** — engine/sandbox.py: replaced threading.Thread with multiprocessing.Process + Queue. State deep-copied before passing to bot. Timed-out processes killed via process.kill(). 3 new isolation tests, 28 total sandbox tests pass, 458 total pass.

- **Sprint 6 planned** — 9 tasks (145 Cx) for production hardening. Addresses 2 CRITICAL (sandbox isolation, AST pre-scan), 2 HIGH (OAuth permissions, bot launcher), and 5 MEDIUM findings from readiness audit. Target: 72→90+ production readiness score.

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


### S6: Production Hardening (Planned)

| ID | Title | Cx | Type | Priority | Status |
|----|-------|----|------|----------|--------|
| T6.1 | Sandbox: multiprocessing isolation + state deepcopy | 35 | bugfix | P0 | ✓ done |
| T6.2 | AST pre-scan: block dangerous imports before exec_module | 20 | feature | P0 | ✓ done |
| T6.3 | OAuth token permissions + Discord error hardening | 10 | bugfix | P0 | ✓ done |
| T6.4 | Discord bot launcher: run_bot.py with full command wiring | 15 | feature | P0 | ✓ done |
| T6.5 | Wire announce_match_start/end into match runner | 10 | feature | P1 | done ✓ |
| T6.6 | Claims state persistence: load on startup, save on mutation | 10 | bugfix | P1 | done ✓ |
| T6.7 | Discord /run_match command: trigger match from Discord | 25 | feature | P1 | done ✓ |
| T6.8 | Type hint completion + sandbox error logging | 10 | refactor | P1 | done ✓ |
| T6.9 | CLI input validation: fps bounds, path canonicalization | 10 | bugfix | P2 | done ✓ |

## What's Next

T10.1 and T10.2 done. Continue with T10.3+.


## Blockers

None currently.

## Known Bugs (to fix in S1)

- `Bot.force_rest()` — dead code, never called in game.py (T1.8)
- `ChaosBot` — uses unseeded `random`, not reproducible from match seed (T1.9)
- Energy can go negative after action cost deduction (T1.10)
- 200-round cap has no tiebreaker — potential draw with no winner (T1.11)
- Kill attribution uses last-hit-this-round, not killing blow (T1.12)
