# Current State

> Last updated: 2026-04-09 T66.3 done

## Active Plans

**Plan:** Sprint 58: Engage — Agent Grounds backlog
- **Sprint:** S58 | **Type:** feature | **Status:** in_progress

### S58 Tasks

| Task | Title | Cx | Depends On | Status |
|------|-------|----|------------|--------|
| T58.1 | Kill Switch rivalry tracker | 20 | — | done |
| T58.2 | Kill Switch personality profiler | 25 | — | done |
| T58.3 | Kill Switch commentary engine | 30 | T58.1, T58.2 | done |
| T59.1 | Highlight extractor | 20 | T58.3 | done ✓ |
| T59.2 | Watcher dossier | 20 | — | done ✓ |
| T59.3 | Watcher monologues | 15 | T59.2 | done ✓ |
| T59.4 | Wire TV into play command | 15 | T58.3, T59.1, T59.2 | done ✓ |
| T60.1 | Code Circuit commentary enhancement | 20 | T58.3 | done ✓ |
| T60.2 | Code Circuit personality profiler | 20 | — | done ✓ |
| T60.3 | Code Circuit rivalry tracker | 15 | — | done ✓ |
| T61.1 | Platform event contract + adapters | 25 | T59.4, T60.1 | done ✓ |
| T61.2 | Platform commentary contract | 15 | T59.4, T60.1 | done ✓ |
| T62.1 | Episode generator | 30 | T61.1, T61.2 | done ✓ |
| T62.2 | Commentary video overlay | 20 | T58.3 | done ✓ |
| T62.3 | Viewer commentary ticker | 20 | T59.4 | done ✓ |
| T63.1 | Season manager | 25 | — | done ✓ |
| T64.1 | Discord match ingestion | 20 | — | done ✓ |
| T64.2 | TV rendering pipeline | 25 | T62.1, T62.2, T64.1 | done ✓ |
| T64.3 | Discord channel posting | 20 | T64.2 | done ✓ |
| T64.4 | Season automation | 20 | T63.1, T64.3 | done ✓ |
| T65.1 | Kill Switch meta analyzer | 20 | — | done ✓ |
| T65.2 | Decision tracer | 25 | — | done ✓ |
| T65.3 | Code overlay in viewer | 20 | T65.2 | done ✓ |
| T65.4 | Ghost replay for Kill Switch | 25 | — | done ✓ |
| T66.1 | Mono-package structure | 25 | T59.4, T60.1 | done ✓ |
| T66.2 | Viewer unification | 20 | T62.3 | done ✓ |
| T66.3 | Documentation + on-ramp | 15 | T66.1 | done ✓ |

## Current Focus

T66.3 complete. Open-source documentation ready.

## What Was Just Done

- **T66.3 done**

**T66.3: Documentation + on-ramp** — Rewrote README.md with 3-command demo (pip install, init, play), both games (Kill Switch + Code Circuit), feature list, architecture overview with directory tree, and all CLI commands. Created docs/getting-started.md with full on-ramp: install → init → play → watch replay → build a bot (AI/tweak/scratch) → episodes → batch sim. Expanded CONTRIBUTING.md with 6 contribution paths: bot showcase, commentary templates (with examples for both games), spectacle effects (drama tier table), adding new games (platform contracts, dispatcher registration, full checklist), suggestions, and bug reports. Verified LICENSE (MIT, Cognify Labs). Reviewed PROMPT.md — already polished (466 LOC), packaged copy in sync. 29 new tests covering: README (demo, features, architecture, both games, links, no broken markdown links), Getting Started (exists, pip install, init, play, episode), PROMPT.md (exists, format, equipment, packaged), CONTRIBUTING (commentary, effects, new games, bots), LICENSE (exists, MIT, copyright), rendering (no script tags, headings). All pass. Ruff clean, arch clean.

- **T66.2 done** (auto-updated by hook)

- **T66.2 done**

**T66.2: Viewer unification** — Created unified `viewer/viewer.html` entry point that detects game type from loaded JSON and dispatches to the correct renderer. Created `viewer/js/game_detect.js` (17 LOC) with `detectGame(data)` returning "circuit" or "killswitch" based on `data.game` field. Created `viewer/js/circuit_renderer.js` (109 LOC) with `renderCircuitCanvas(round)` drawing an oval track with car positions, lap indicators, start/finish line, and car color coding; `renderCircuitRound(idx)` orchestrates canvas + sidebar + commentary updates. Created `viewer/js/circuit_sidebar.js` (101 LOC) with `buildCircuitCarList()` for car roster, `updateCircuitSidebar(round)` showing positions and lap_time, and `updateCircuitEvents(round, idx)` for race event feed (overtakes, spins, fastest laps with icons). Updated `viewer/js/app.js` with game-aware `initViewer()` dispatching to `_initKillSwitchViewer()` or `_initCircuitViewer()`. Updated `viewer/js/renderer.js` `renderRound()` to dispatch to `renderCircuitRound()` for circuit matches. Shared controls (play/pause/speed/scrub), commentary ticker, zoom, and audio work for both games. KS-specific effects (spectacle, kill cam, terrain, storm) preserved. CC-specific telemetry (position standings, lap times, race events) in new modules. 41 new tests. All 338 viewer tests pass. Arch clean.

- **T66.1 done** (auto-updated by hook)

- **T66.1 done**

**T66.1: Mono-package structure** — Restructured for `pip install agent-grounds` as a single PyPI package containing both Kill Switch and Code Circuit. Created `engine/circuit.py` (132 LOC) with `run_race(car_configs, laps, seed)` — lap-based race simulation with overtakes, spins, fastest laps, deterministic seeding, and platform-compatible output (results, events, rounds, players). Created `engine/circuit_tv.py` (47 LOC) with `enrich_circuit_tv(race_data)` — adds commentary and highlights to race data via `circuit_commentary.py`. Created `agentgrounds/circuit/` package with CLI: `cli/__init__.py` (parser + dispatch), `cli/cmd_race.py` (race subcommand with --laps, --seed, --no-tv flags, builtin car fallback). Updated `agentgrounds/__main__.py` dispatcher: `killswitch` → wars CLI, `circuit` → circuit CLI, `wars` kept as backward-compat alias. Updated `pyproject.toml` to include `tv*` in package discovery. Help text updated with both games + examples. Package builds cleanly (`python -m build`). Both games run: `agentgrounds killswitch play` and `agentgrounds circuit race`. 28 new tests across 3 files (test_mono_package.py, test_circuit_engine.py, test_cli_circuit.py). All arch checks clean.

- **T65.4 done** (auto-updated by hook)

- **T65.4 done**

**T65.4: Ghost replay for Kill Switch** — Built `engine/ghost_replay.py` (143 LOC) with `ghost_replay(match_data, round_num, bot_emoji, alt_action, seed)` returning ghost match JSON. Forks match state at any round by reconstructing Bot objects from round position data, substitutes one bot's action at the divergence point, and re-simulates remainder using the engine's `resolve_combat_phases` and `apply_momentum_phase`. Post-fork rounds replay original recorded actions against diverged state. Output marks `divergence_point: True` on fork round, `ghost: True` and `divergence_round` at top level, includes `original_winner` for comparison. Original match data never modified (deep copy). Deterministic via seeded RNG. 12 tests covering: ghost JSON shape, divergence marking, original unmodified, deterministic replay, pre-fork rounds unchanged, attack→defend substitution, defend→attack substitution, early divergence (round 1), late divergence, simulation to completion, invalid round validation, file LOC limit. Ruff clean, arch clean.

- **T65.3 done** (auto-updated by hook)

- **T65.3 done**

**T65.3: Code overlay in viewer** — Built `viewer/js/code_overlay.js` (131 LOC) with `initCodeOverlay()`, `updateCodeOverlay(roundIdx)`, `renderDecisionTrace(emoji, trace)`, `toggleCodeOverlay()`, and `toggleBotTrace(emoji)`. Collapsible panel in sidebar shows decision traces per round from `round.decision_traces`. Active branch highlighted with accent color (`trace-active`), inactive dimmed (`trace-inactive`). Per-bot toggle buttons auto-built from match data — only bots with trace data get toggles. Panel hidden when no trace data in match JSON. State snapshot (HP, energy, enemies) shown below traces. Wired into `renderRound()` via `updateCodeOverlay(idx)` call and `initViewer()` via `initCodeOverlay()`. Added HTML panel + CSS to `index.html`. 11 tests covering: file existence, LOC limit, panel element, collapsible, render function, active/inactive highlighting, per-bot toggle, no-data hiding, update function, renderRound integration. Arch clean.

- **T65.2 done** (auto-updated by hook)

- **T65.2 done**

**T65.2: Decision tracer** — Built `engine/decision_trace.py` (111 LOC) with `trace_decision(bot_module, state)` returning (action, trace_dict). Uses `sys.settrace` to capture line execution within bot module and `ast` to extract if/elif condition strings. Trace dict contains: `conditions_checked` (readable condition strings evaluated), `branch_taken` (condition whose body was entered), `state_snapshot` (hp, energy, x, y, round, enemies_alive, storm_border). Opt-in via `BOT_TRACE = True`. Integrated into `engine/game.py:_execute_round()` via `collect_round_traces()` adding traces to round_data under `decision_traces` key. Also refactored `run_match` by extracting `_run_match_loop` to fix pre-existing arch violation. 24 tests covering: simple bot, complex bot with helpers, opt-in flag, state isolation, all 11 builtin bots. Ruff clean, arch clean.

- **T65.1 done**

**T63.1: Season manager** — Built `data/seasons.py` (168 code LOC) with `create_season(conn, name, config, scoring_rules)`, `record_result(season_id, match_data, conn=conn)`, `get_standings(season_id, conn=conn)`, and `promote_relegate(season_id, conn=conn)`. SQLite-backed with seasons and season_results tables. Game-agnostic scoring: Kill Switch (kills × kill_points + placement_points map) and Code Circuit (F1 position_points map). Tier system (Diamond/Gold/Silver/Bronze) via configurable thresholds with defaults (10%/30%/60%). Promotion/relegation computed per-tier with configurable top-N promote and bottom-N relegate. 14 tests covering: create, store, multiple seasons, KS scoring, CC scoring, 5-result standings, unknown placement, empty season, tier assignments, default tiers, promotion/relegation, single-participant edge case, F1 multi-race accumulation, unscored position. Ruff clean, arch clean.

- **T62.3 done** (auto-updated by hook)

- **T62.3 done**

**T62.3: Viewer commentary ticker** — Built `viewer/js/commentary.js` (78 LOC) with `initCommentary()`, `updateCommentary(roundIdx)`, and `toggleCommentary()`. Reads from `matchData.commentary` array (platform CommentaryLine format: timestamp, text, tone, line_type). Play-by-play lines render in white (#e0e0f0), color commentary in gold (#ffd700, italic). Shows last 3 lines, auto-advances with round playback via renderRound integration. Fades in/out (opacity transition 0.3s) on round changes. CC toggle button in controls panel. Graceful when commentary key missing. Added ticker HTML + CSS to index.html. 10 tests. Ruff clean, arch clean.

- **T62.2 done**

**T62.2: Commentary video overlay** — Built `video/video_commentary.py` (50 LOC) with `render_commentary_overlay(frame, text, tone)` returning PIL Image with bottom ticker banner. Semi-transparent dark banner (28px) at frame bottom. Drama-tier color coding: white=calm, yellow=heating, orange=intense, red=hype, magenta=chaos. Integrated into `video/video_render.py` `render_frame()` — applies overlay when `round_data["commentary"]` dict is present (with `text` and `tone` keys), skipped otherwise. 8 unit tests + 2 integration tests. All 56 video tests pass. Ruff clean, arch clean, 50 LOC.

- **T62.1 done**

**T62.1: Episode generator** — Built `engine/episode.py` (148 LOC) with `build_episode(match_data, commentary, highlights, profiles, rivalries, season_standings)` returning episode manifest dict. Four sections: cold_open (rivalry recaps with "Previously on..." text, graceful empty-history fallback), pre_match (participant intro cards from profiles with default for unknown participants), match_commentary (indexed commentary track passthrough), post_match (stat diffs computed from match stats, highlight manifest, season standings snapshot, winner). Game-agnostic via `game` field in match_data — works with both Kill Switch and Code Circuit JSON. 21 tests covering: episode shape, cold open with/without rivalries, pre-match intros with/without profiles, commentary track, stat diffs, highlights, standings, cross-game (KS + CC), scenarios (first episode, mid-season, season finale). Ruff clean, arch clean.

- **T61.2 done**

**T61.2: Platform commentary contract** — Created `engine/platform_commentary.py` (38 LOC) with frozen `CommentaryLine` dataclass (timestamp, text, tone, line_type) and `CommentaryContract` runtime-checkable protocol. `VALID_TONES` = {calm, heating, intense, hype, chaos}. `VALID_LINE_TYPES` = {play_by_play, color, analysis}. Updated Kill Switch `engine/commentary.py` to import and use platform `CommentaryLine` (renamed `round` → `timestamp`, `type` → `line_type`). Created `engine/circuit_commentary.py` (68 LOC) with `generate_circuit_commentary(replay, race_events)` producing platform `CommentaryLine` from CC race events. Updated existing KS tests for new field names. 32 new+updated tests covering: dataclass shape, frozen, asdict, valid tones/types, protocol conformance, KS conformance, CC conformance. All 56 related tests pass. Ruff clean, arch clean.

- **T61.1 done** (auto-updated by hook)

- **T61.1 done**

**T61.1: Platform event contract + adapters** — Built `engine/platform_events.py` (145 LOC) with `GameEvent` dataclass (type, timestamp, participants, data, drama_weight) and two adapters. `adapt_killswitch_events(match_data)` maps 12 KS event types (kill, hit, ranged_hit, ability_damage, ability_heal, trap_trigger, bump, wall_splat, storm_damage, watcher_spawn/kill/sync) plus synthesised near_death from positions. `adapt_circuit_events(replay, race_events)` maps all 6 CC event types (OVERTAKE→overtake, BATTLE→battle, SPIN→spin, SAFETY_CAR→safety_car, PIT_STOP→pit_stop, FASTEST_LAP→fastest_lap) with tick→seconds conversion. `EVENT_TYPES` dict documents all 19 event types with drama_weight (0-6 scale) and rationale. 24 tests covering: dataclass shape, defaults, KS empty/calm/kill/storm_kill/hit/ability/watcher_spawn/watcher_kill/near_death/trap/multi-round ordering, CC empty/overtake/battle/spin/safety_car/pit/fastest_lap/timestamp conversion, event type documentation. Ruff clean, arch clean.

- **T60.3 done**

**T60.3: Code Circuit rivalry tracker** — Built `engine/circuit_rivalry.py` (117 LOC) with `compute_rivalry(car_a, car_b, race_history)` returning rivalry dict. Tracks overtakes between pair, defensive holds, laps in battle, championship points delta, average finishing gap. Rivalry score (0-100) based on weighted factors: overtake frequency (35%), battle laps (25%), finishing closeness (25%), volume (15%). Narrative hooks generated for commentary (trade paint, wheel-to-wheel, championship battle, etc.). 10 tests covering: no history, cars never met, single race basics, no overtakes, narrative hooks, multi-race accumulation, high/low rivalry scores, race filtering, season narrative hooks. Ruff clean, arch clean.

- **T60.2 done** (auto-updated by hook)

**T60.2: Code Circuit personality profiler** — Built `npc-race/engine/personality.py` (133 LOC) with `profile_car(name, race_history)` returning profile dict with traits, variant_name, bio. 9 distinct traits detected from racing behavior: conservative tire manager, late braker, rain specialist, one-stop hero, aggressive defender, slipstream hunter, qualifying ace, sunday driver, clean racer. Traits derived from tire wear rates, brake temps, wet-condition gains, pit strategy, defend ratios, slipstream usage, grid-vs-finish delta, and incident rates. Template-based bio and variant name generation (no LLM). Graceful empty-history handling returns Rookie profile. 28 tests covering all trait detection (positive + negative), profile shape, first-race graceful, trait count verification, bio determinism, and bio differentiation. Ruff clean, arch clean.

- **T60.1 done** (auto-updated by hook)

**T60.1: Code Circuit commentary enhancement** — Extended `npc-race/engine/commentary.py` (228 LOC) with `generate_commentary(replay, events, profiles, rivalries)` returning CommentaryLine-compatible dicts. Drama-tier tone scaling (calm/heating/intense/hype) mapped to event types (safety car=hype, spin=intense, overtake=heating, pit=calm). Weather commentary detects wet/dry transitions from replay frames and tire compound switches. Strategy commentary covers multi-stop, compound switches. Personality references use trait templates (rain specialist, conservative tire manager, aggressive defender, etc.) with wet-condition awareness. Rivalry callouts on two-car interactions. Templates extracted to `commentary_templates.py` (130 LOC). 19 new tests covering: dict shape, dry race, wet race, safety car, multi-stop strategy, overtake battle, personality references, rivalry callouts. All 28 tests pass. Ruff clean, arch clean.

- **T59.4 done** (auto-updated by hook)

- **T59.4 done** (auto-updated by hook)

**T59.4: Wire TV into play command** — Built `engine/tv_pipeline.py` (75 LOC). `enrich_tv(match_data)` runs the full TV pipeline post-match: builds personality profiles per bot, computes pairwise rivalries, extracts highlights, generates commentary (serialised from dataclass to dict), and builds watcher dossiers per author. Wired into `cmd_play.py._run_match()` — runs after `inject_diff_data()` and before `write_match()`. Added `--no-tv` flag to skip TV generation for speed. 16 new tests covering: flag registration, all 5 TV keys present, correct types (list/dict), emoji-keyed profiles, JSON serialisability, existing keys untouched, `--no-tv` skips keys, default TV-enabled produces keys. Ruff clean, arch clean.

- **T59.3 done** (auto-updated by hook)

- **T59.3 done** (auto-updated by hook)

**T59.3: Watcher monologues** — Built `engine/watcher_dialogue.py` (133 LOC). `generate_monologue(trigger, sync_score, pattern_summary)` returns context-aware dialogue strings. 4 trigger types (spawn, kill, sync_milestone, player_death) × 3 sync tiers (low <30%, mid 30-70%, high >70%). Templates use `{action}` and `{context}` placeholders from pattern summary, with safe fallbacks for missing data. 5+ templates per trigger type. Invalid triggers raise ValueError. 34 tests covering all trigger/tier combos, placeholder injection, template counts, empty summaries, None handling, and determinism. Ruff clean, arch clean.

- **T59.2 done** (auto-updated by hook)

**T59.2: Watcher dossier** — Built `engine/watcher_dossier.py` (140 LOC). `build_dossier(player_id, patterns_dir, watcher_stats_path)` reads pattern data via `server/rival_patterns.py` helpers, returns dossier dict with per-context predictions (top 3 actions + probabilities + counter), sync_score (exponential saturation on observation count), and predictability_change (average max-probability across contexts). `format_dossier_text()` generates human-readable summary with "Context: X → Predicted action: Y (Z%)" format. Returns intro dossier for players with no history. 10 tests covering: no data, empty table, single context, multiple contexts, high/low sync scores, high/low predictability, and text formatting. Ruff clean, arch clean.

**T59.1: Highlight extractor** — Built `engine/highlights.py` (152 LOC). `extract_highlights(match_data, threshold="hype")` scans rounds via SpectacleEngine, extracts highlight clips (2 rounds before trigger → trigger → 1 after), tags with trigger_type (kill/near_death/chain_bump/watcher_event), participants, drama_score, and commentary snippets. Kill guarantee ensures at least 1 highlight for any match with a kill. Overlapping ranges merge automatically. 11 tests covering: calm match (no highlights), kill guarantee, single highlight, boundary clamping, required fields, merge overlapping, separate distant, and threshold levels. Ruff clean, arch clean.

- **T58.2 done** (auto-updated by hook)

- **T58.1 done** (auto-updated by hook)

**T58.1: Kill Switch rivalry tracker** — Built `engine/rivalry.py` (pure functions: `compute_rivalry_stats`, `compute_rivalry_score`, `rivalry_trend`) and `data/rivalry_db.py` (I/O wrapper). Tracks wins, losses, kills, streaks, rivalry score (0-100), and trending direction between bot pairs. 24 tests across 2 test files, all pass. 167 LOC total, arch clean, ruff clean.

- **T58.2 done**

**T58.2: Kill Switch personality profiler** — Built `engine/personality.py` (API + aggregation, 142 LOC) and `engine/personality_traits.py` (trait detection + variants + bios, 128 LOC). `profile_bot(emoji, results_dir, patterns_dir)` returns profile dict with traits, archetype_variant, bio. 15 distinct traits detected from behavior patterns (aggressive, defensive, trap, ranged, mobile, tactical, equipment, pattern-based). Template-based bio generation. Graceful on first match. 16 tests covering aggressive, defensive, balanced, trap-heavy, pattern-based, and equipment bots. Ruff clean, arch clean.

## What's Next

T66.3 complete. Ready for next sprint task.

## Completed Sprints

| Sprint | Focus | PR | Status |
|--------|-------|-----|--------|
| S1-S31 | Phase 1: Foundation | #1-#27 | Done |
| S32-S39 | Phase 2: Depth | #27-#34 | Done |
| S40-S43 | Phase 3A: Playable Product | #35-#39 | Done |
| S44 | Character System | #40 | Done |
| S45 | Kill Cam + Sound + Preflight | #41 | Done |
| S46 | Cosmetics | #42 | Done |
