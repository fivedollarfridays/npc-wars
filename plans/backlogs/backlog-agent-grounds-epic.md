# Agent Grounds Epic — Open Source Platform + TV Layer

> All free. All client-side. Net-zero. Pure cred.
> 8-week rollout across npc-wars, npc-race, and agentgrounds-web.

**Plan type:** feature
**Estimated sprints:** 16 (S58–S73)
**Tracks:** Kill Switch TV, Code Circuit TV, Platform Extraction, Discord Queue, OSS Packaging

---

## Phase 1: Kill Switch TV Core (Weeks 1–2)

Goal: `agentgrounds killswitch play` outputs commentary + highlights alongside match JSON.

### T58.1 — Kill Switch rivalry tracker | Cx: 20 | P0

**Description:** Build `engine/rivalry.py` and `data/rivalry_db.py` to track head-to-head history between bot pairs across matches. Iterate `data/match_history` and `data/matchup_stats` to aggregate wins, losses, kill counts, streaks, and rounds of dominance per bot pair. Output a rivalry score (0-100), trending direction, and notable stats as JSON. This becomes the data source for commentary callouts and episode cold opens.

**AC:**
- [ ] `compute_rivalry(emoji_a, emoji_b, results_dir)` returns rivalry dict with wins, losses, streak, score
- [ ] Rivalry score 0-100 reflects historical dominance (50 = even, 100 = total dominance)
- [ ] Handles edge cases: no history, single match, same bot
- [ ] All functions are pure (no I/O in core logic; I/O wrapper separate)
- [ ] Tests cover 0, 1, 5+ match histories
- [ ] File under 200 LOC, ruff clean

**Depends on:** —

---

### T58.2 — Kill Switch personality profiler | Cx: 25 | P0

**Description:** Build `engine/personality.py` to analyze bot behavior across matches and generate personality profiles. Consume stat_diff history, action frequency from pattern tables, equipment choices, and callback usage. Output a trait list (e.g., "aggressive opener", "trap-obsessed", "storm dodger"), archetype variant name, and flavor bio. Used by commentary, episode intros, and viewer overlays.

**AC:**
- [ ] `profile_bot(emoji, results_dir, patterns_dir)` returns profile dict with traits, archetype_variant, bio
- [ ] At least 10 distinct traits detected from behavior patterns
- [ ] Bio is a 1-2 sentence generated description (template-based, no LLM)
- [ ] Graceful on first match (returns "Unknown" archetype, generic bio)
- [ ] Tests cover varied bot behaviors (aggressive, defensive, balanced, trap-heavy)
- [ ] File under 200 LOC, ruff clean

**Depends on:** —

---

### T58.3 — Kill Switch commentary engine | Cx: 30 | P0

**Description:** Build `engine/commentary.py` — template-based commentary generator that consumes round-by-round match data, spectacle data, personality profiles, and rivalry data. Generate play-by-play (factual: "Tank moves to high ground") and color commentary (analytical: "Smart positioning — that's how they beat Kiter last match"). Drama tier modulates tone: calm=observational, heating=building, hype=excited, chaos=screaming. Output per-round commentary strings with timing and tone markers.

**AC:**
- [ ] `generate_commentary(match_data, profiles, rivalries)` returns list of CommentaryLine(round, text, tone, type)
- [ ] Play-by-play covers: kills, movement, defend, trap placement, ability use, storm damage
- [ ] Color commentary references: personality traits, rivalry history, equipment choices, Watcher events
- [ ] Tone scales with drama tier (5 tiers = 5 tone levels)
- [ ] At least 50 unique commentary templates
- [ ] Produces commentary for a full match with zero crashes on any builtin_bot matchup
- [ ] Tests cover all drama tiers and major event types
- [ ] File under 400 LOC (may split into commentary.py + commentary_templates.py), ruff clean

**Depends on:** T58.1, T58.2

---

### T59.1 — Highlight extractor | Cx: 20 | P0

**Description:** Build `engine/highlights.py` to scan match rounds for high-drama moments (drama_score >= "hype" tier threshold). Extract highlight clips: 2 rounds before trigger → trigger round → 1 round after. Tag each highlight with type (kill, near_death, chain_bump, watcher_event), participants, and drama score. Output a highlight manifest JSON with round ranges, tags, and associated commentary snippets.

**AC:**
- [ ] `extract_highlights(match_data, threshold="hype")` returns list of Highlight dicts
- [ ] Each highlight has: round_range, trigger_type, participants, drama_score, commentary
- [ ] Minimum 1 highlight from any match containing a kill
- [ ] Adjacent highlights merge (no overlapping round ranges)
- [ ] Works with existing match JSON format (no schema changes needed)
- [ ] Tests cover: no highlights (calm match), single highlight, multiple overlapping
- [ ] File under 200 LOC, ruff clean

**Depends on:** T58.3

---

### T59.2 — Watcher dossier | Cx: 20 | P0

**Description:** Build `engine/watcher_dossier.py` to surface the Watcher's PatternTable as a human-readable dossier. Read pattern data via existing `server/rival_patterns.py` helpers (`get_pattern_summary`, `compact_for_embed`). Format as "Context: below_30_hp → Predicted action: rest (78%), Expected counter: attack". Include sync score as "How well does the Watcher know you?" percentage and pattern change rate between matches.

**AC:**
- [ ] `build_dossier(player_id, patterns_dir, watcher_stats_path)` returns dossier dict
- [ ] Dossier includes: per-context predictions (top 3 actions with probabilities), sync_score, predictability_change
- [ ] Human-readable text summary generated (template-based)
- [ ] Returns empty/intro dossier for players with no history
- [ ] Tests cover: no data, 1 match, 5+ matches, high/low sync scores
- [ ] File under 200 LOC, ruff clean

**Depends on:** —

---

### T59.3 — Watcher monologues | Cx: 15 | P1

**Description:** Build `engine/watcher_dialogue.py` with template-based taunts generated from pattern data. Context-aware: different taunts for high-sync ("I know what you'll do") vs low-sync ("Interesting... you've changed"). Triggered at: Watcher spawn, kill, sync milestone, player death. Output dialogue strings with timing, injected into match events via the existing watcher_spectacle event system.

**AC:**
- [ ] `generate_monologue(trigger, sync_score, pattern_summary)` returns dialogue string
- [ ] At least 5 templates per trigger type (spawn, kill, sync_milestone, player_death)
- [ ] Tone varies by sync level (low <30%, mid 30-70%, high >70%)
- [ ] Integration point: monologues added to match events alongside existing watcher_spectacle events
- [ ] Tests cover all trigger types at all sync levels
- [ ] File under 150 LOC, ruff clean

**Depends on:** T59.2

---

### T59.4 — Wire TV into play command | Cx: 15 | P0

**Description:** Wire commentary, highlights, personality, rivalry, and Watcher dossier into the match output. After `run_match()` completes, run the TV pipeline: generate commentary, extract highlights, build profiles, compute rivalries, build dossier. Append results to match JSON under new top-level keys: `commentary`, `highlights`, `profiles`, `rivalries`, `watcher_dossier`. Existing viewer and video pipeline ignore unknown keys, so this is additive-only.

**AC:**
- [ ] `agentgrounds killswitch play` outputs match JSON with commentary + highlights + profiles + rivalries
- [ ] TV data appended post-match (no engine changes — wraps match_data after run_match)
- [ ] `--no-tv` flag skips TV generation for speed
- [ ] Existing tests unaffected (TV keys are optional)
- [ ] New test: play command with TV enabled produces valid commentary and highlights
- [ ] No new dependencies

**Depends on:** T58.3, T59.1, T59.2

---

## Phase 2: Code Circuit TV + Platform Extraction (Week 3)

Goal: Both games produce commentary. Platform contracts defined.

### T60.1 — Code Circuit commentary enhancement | Cx: 20 | P0

**Description:** Extend Code Circuit's existing `engine/commentary.py` with drama-tier tone scaling (currently flat), personality references, rivalry callouts, and weather/strategy narrative. The existing `format_event()` produces flat strings — add a `generate_commentary()` function that wraps events with tone, personality context, and rivalry data matching the interface built for Kill Switch.

**AC:**
- [ ] `generate_commentary(replay, events, profiles, rivalries)` returns list of CommentaryLine-compatible dicts
- [ ] Tone scales with race drama (safety car=hype, spin=intense, calm racing=calm)
- [ ] Weather commentary: "switching to wets was the right call", "track drying, slicks coming into play"
- [ ] Strategy commentary: "one-stop gamble paying off", "tire cliff approaching"
- [ ] Personality references in commentary (e.g., "the rain specialist thrives in these conditions")
- [ ] Tests cover: dry race, wet race, safety car, multi-stop strategy, overtake battle
- [ ] File stays under 400 LOC (extend existing, don't rewrite), ruff clean

**Depends on:** T58.3 (for interface alignment)

---

### T60.2 — Code Circuit personality profiler | Cx: 20 | P1

**Description:** Build Code Circuit `engine/personality.py` with game-specific traits: "conservative tire manager", "late braker", "rain specialist", "one-stop hero", "aggressive defender", "slipstream hunter". Derive from pit strategy patterns, tire wear rates, weather performance, overtake/defend ratios, and qualifying vs race pace delta.

**AC:**
- [ ] `profile_car(name, race_history)` returns profile dict with traits, variant_name, bio
- [ ] At least 8 distinct traits detected from racing behavior
- [ ] Bio template-based (no LLM)
- [ ] Graceful for first race
- [ ] Tests cover varied strategies (aggressive, conservative, wet specialist, etc.)
- [ ] File under 200 LOC, ruff clean

**Depends on:** —

---

### T60.3 — Code Circuit rivalry tracker | Cx: 15 | P1

**Description:** Build Code Circuit `engine/rivalry.py` to track position battle history between car pairs. Compute overtake/defend success rates, championship points head-to-head, and laps spent in direct battle. Output rivalry score (0-100) and narrative hooks.

**AC:**
- [ ] `compute_rivalry(car_a, car_b, race_history)` returns rivalry dict
- [ ] Tracks: overtakes between pair, defensive holds, gap statistics, championship points delta
- [ ] Rivalry score reflects historical competitiveness
- [ ] Tests cover: no history, single race, season-long rivalry
- [ ] File under 150 LOC, ruff clean

**Depends on:** —

---

### T61.1 — Platform event contract + adapters | Cx: 25 | P0

**Description:** Define the platform-level `GameEvent` dataclass and build adapters for both games. Kill Switch adapter maps `SpectacleData` + round events → `GameEvent` list. Code Circuit adapter maps `RaceEvent` → `GameEvent` list. This is the seam that makes highlight extraction and episode generation game-agnostic. Place in a shared location importable by both games (initially in npc-wars, extracted later).

**AC:**
- [ ] `GameEvent` dataclass: type, timestamp, participants, data, drama_weight
- [ ] `adapt_killswitch_events(match_data) → list[GameEvent]` maps all KS event types
- [ ] `adapt_circuit_events(replay, race_events) → list[GameEvent]` maps all CC event types
- [ ] Both adapters tested against real match/replay data
- [ ] Event types documented with drama_weight rationale
- [ ] File under 200 LOC, ruff clean

**Depends on:** T59.4, T60.1

---

### T61.2 — Platform commentary contract | Cx: 15 | P0

**Description:** Define the platform-level `CommentaryLine` dataclass and `CommentaryContract` protocol. Both games already have `generate_commentary()` — this task formalizes the shared interface so episode generator and highlight extractor can consume commentary from either game without knowing which game produced it.

**AC:**
- [ ] `CommentaryLine` dataclass: timestamp, text, tone (calm/heating/intense/hype/chaos), line_type (play_by_play/color/analysis)
- [ ] Both Kill Switch and Code Circuit commentary functions return `list[CommentaryLine]`
- [ ] Protocol or ABC defined for type checking
- [ ] No behavioral changes — just interface alignment
- [ ] Tests verify both game outputs conform to contract
- [ ] File under 100 LOC, ruff clean

**Depends on:** T59.4, T60.1

---

## Phase 3: Episode Packaging + Video (Week 4)

Goal: Matches become episodes. Episodes become videos.

### T62.1 — Episode generator | Cx: 30 | P0

**Description:** Build `engine/episode.py` — the game-agnostic episode orchestrator. Consumes match data, commentary, highlights, personality profiles, and rivalry data. Produces an episode manifest JSON with four sections: (1) Cold Open — rivalry recaps, meta narrative; (2) Pre-Match — participant intros with profiles, equipment/setup reveals; (3) Match — commentary track indexed by round/tick; (4) Post-Match — stat diffs, highlight reel manifest, season standings snapshot. Works for both Kill Switch and Code Circuit via platform contracts.

**AC:**
- [ ] `build_episode(match_data, commentary, highlights, profiles, rivalries, season_standings)` returns episode dict
- [ ] Episode has: cold_open, pre_match, match_commentary, post_match sections
- [ ] Cold open generates "Previously on..." text from rivalry data
- [ ] Pre-match generates participant intro cards from profiles
- [ ] Post-match includes stat diffs and highlight manifest
- [ ] Works with both Kill Switch match JSON and Code Circuit replay JSON
- [ ] Tests cover: first episode (no history), mid-season, season finale
- [ ] File under 300 LOC, ruff clean

**Depends on:** T61.1, T61.2

---

### T62.2 — Commentary video overlay | Cx: 20 | P0

**Description:** Build `video/video_commentary.py` to burn commentary text into the existing video pipeline. Add a text ticker at the bottom of rendered frames showing commentary lines synced to round numbers. Integrate into `video/video_render.py`'s `render_frame()` pipeline as an optional layer. Commentary text uses drama-tier color coding (white=calm, yellow=heating, orange=intense, red=hype, magenta=chaos).

**AC:**
- [ ] `render_commentary_overlay(frame, commentary_line)` returns PIL Image with text overlay
- [ ] Text positioned at bottom of frame, readable at video resolution
- [ ] Color-coded by drama tier
- [ ] Integrated into render_frame() pipeline (called when commentary data present, skipped otherwise)
- [ ] Existing video tests still pass
- [ ] New test: frame with commentary overlay renders correctly
- [ ] File under 150 LOC, ruff clean

**Depends on:** T58.3

---

### T62.3 — Viewer commentary ticker | Cx: 20 | P1

**Description:** Build `viewer/js/commentary.js` — a text ticker at the bottom of the browser replay that displays commentary lines, auto-advancing with round playback. Reads from the `commentary` key in match JSON. Shows play-by-play in white, color commentary in gold. Fades in/out with round transitions. Toggleable via controls.

**AC:**
- [ ] Commentary ticker renders below canvas during replay
- [ ] Auto-advances with round playback, manual scrubbing updates commentary
- [ ] Play-by-play and color commentary visually distinct
- [ ] Toggle button in controls panel
- [ ] Graceful when match JSON has no commentary key
- [ ] Works with existing replay controls (play, pause, speed, scrub)
- [ ] File under 200 LOC

**Depends on:** T59.4

---

### T63.1 — Season manager | Cx: 25 | P0

**Description:** Build `data/seasons.py` — game-agnostic season manager extracted from Kill Switch tournaments and Code Circuit championships. Define season config (episodes per season, tier thresholds), round scheduling, standings computation, and promotion/relegation. Store in local SQLite. Tier system: Bronze/Silver/Gold/Diamond. Standings computed from match results using game-provided scoring rules.

**AC:**
- [ ] `create_season(name, config, scoring_rules)` initializes season in SQLite
- [ ] `record_result(season_id, match_data)` updates standings
- [ ] `get_standings(season_id)` returns sorted standings with tier assignments
- [ ] Promotion/relegation computed at season end
- [ ] Supports both Kill Switch scoring (kills + placement) and Code Circuit scoring (F1 points)
- [ ] Tests cover: create, record 5 results, standings correct, tier boundaries, promotion
- [ ] File under 250 LOC, ruff clean

**Depends on:** —

---

## Phase 4: Discord Video Queue (Week 5)

Goal: Nathan accepts match submissions and posts TV-quality videos.

### T64.1 — Discord match ingestion | Cx: 20 | P0

**Description:** Add a Discord bot command and file watcher for match JSON submissions. Bot watches `#submissions` for uploaded JSON files, validates schema (must have `match_id`, `rounds`, `stats` for Kill Switch; or `frames`, `results` for Code Circuit), and queues valid matches for TV processing. Rejects malformed uploads with error message.

**AC:**
- [ ] Bot accepts JSON file uploads in designated channel
- [ ] Schema validation distinguishes Kill Switch vs Code Circuit match data
- [ ] Invalid files get error reaction + DM with reason
- [ ] Valid files queued in local directory for processing
- [ ] Rate limit: 1 submission per user per 5 minutes
- [ ] Tests cover: valid KS match, valid CC race, malformed JSON, missing fields
- [ ] File under 200 LOC, ruff clean

**Depends on:** —

---

### T64.2 — TV rendering pipeline | Cx: 25 | P0

**Description:** Build the Nathan-side TV pipeline that processes queued match JSONs. Flow: load match JSON → run TV enrichment (commentary, highlights, profiles, rivalries) → build episode manifest → render MP4 via existing video pipeline with commentary overlay. Output: MP4 file + episode JSON. Runs as a Discord bot background task, processing queue entries sequentially.

**AC:**
- [ ] Pipeline processes Kill Switch match JSON → MP4 with commentary overlay
- [ ] Pipeline processes Code Circuit replay JSON → MP4 (highlight reel for long races)
- [ ] Output MP4 under 25MB (Discord free upload limit)
- [ ] Episode JSON saved alongside MP4
- [ ] Error handling: corrupt JSON logged, queue continues
- [ ] Processing time logged per match
- [ ] Tests cover: KS match pipeline, CC race pipeline, corrupt input handling

**Depends on:** T62.1, T62.2, T64.1

---

### T64.3 — Discord channel posting | Cx: 20 | P0

**Description:** After TV pipeline renders a match, post the video and episode summary to game-specific Discord channels (`#kill-switch-tv`, `#code-circuit-tv`). Main message: video file + winner + key stats. Threaded reply: full stat diffs, highlight descriptions, Watcher dossier (Kill Switch only), season standings update. Use existing `discord_bot/formatters.py` patterns.

**AC:**
- [ ] Video posted to correct game channel based on match type
- [ ] Main message includes: video attachment, winner, match duration, top highlights
- [ ] Thread reply includes: full stats table, stat diffs, season standings change
- [ ] Kill Switch thread includes Watcher dossier section
- [ ] Handles video >25MB gracefully (posts highlights-only or link)
- [ ] Tests cover: KS posting, CC posting, thread formatting

**Depends on:** T64.2

---

### T64.4 — Season automation | Cx: 20 | P1

**Description:** Wire season manager into Discord bot. Bot commands: `/season create`, `/season standings`, `/season schedule`. Nathan runs scheduled matches via cron or Discord command. After each match, season standings auto-update. Weekly power rankings posted to `#standings`. Season finale triggers when configured match count reached.

**AC:**
- [ ] `/season create <name> <game>` initializes a season
- [ ] `/season standings` shows current standings with tiers
- [ ] Match results auto-update season standings after TV pipeline
- [ ] Weekly standings summary posted (configurable day/time)
- [ ] Season finale detection when all rounds complete
- [ ] Tests cover: create season, add results, standings display, finale trigger

**Depends on:** T63.1, T64.3

---

## Phase 5: Kill Switch Advanced TV (Week 5–6, parallel with Phase 4)

### T65.1 — Kill Switch meta analyzer | Cx: 20 | P1

**Description:** Build `data/meta_analysis.py` to aggregate equipment loadouts and stat allocations across all matches. Compute win rates per weapon, armor, accessory combo. Detect dominant strategies (>60% win rate with ≥5 matches). Output meta report JSON: top builds, counter picks, rising/falling strategies.

**AC:**
- [ ] `generate_meta_report(results_dir)` returns meta report dict
- [ ] Win rate per weapon, per armor, per accessory
- [ ] Dominant strategy detection (win rate + sample size threshold)
- [ ] Stat allocation correlation with win rate
- [ ] Report includes: top 5 builds, top 3 counter picks, meta trend
- [ ] Tests cover: varied equipment distributions, edge cases (single match, all same loadout)
- [ ] File under 200 LOC, ruff clean

**Depends on:** —

---

### T65.2 — Decision tracer | Cx: 25 | P1

**Description:** Build `engine/decision_trace.py` to instrument `decide()` execution and capture which branch fired each round. Run bot's decide() in the existing sandbox with a tracing wrapper that records: conditions evaluated, which branch taken, key state variables that influenced the decision. Output per-round decision trace added to match JSON under `decision_traces` key. Does NOT expose source code — captures execution path only.

**AC:**
- [ ] `trace_decision(bot_module, state)` returns (action, trace_dict)
- [ ] Trace captures: conditions checked (as readable strings), branch taken, key state values
- [ ] Works within existing sandbox security model (no new permissions)
- [ ] Opt-in per bot via `BOT_TRACE = True` flag
- [ ] Traces added to match JSON per-round
- [ ] Works with all builtin_bots
- [ ] Tests cover: simple bot, complex bot with callbacks, bot without trace flag
- [ ] File under 200 LOC, ruff clean

**Depends on:** —

---

### T65.3 — Code overlay in viewer | Cx: 20 | P2

**Description:** Build `viewer/js/code_overlay.js` — a collapsible panel in the browser viewer that displays the decision trace alongside replay. Show "IF enemy_distance == 1 AND hp > 30 → ATTACK" with highlighted active branch. Per-bot toggling. Only shows for bots with trace data in match JSON.

**AC:**
- [ ] Panel renders alongside replay canvas
- [ ] Shows decision trace for selected bot per round
- [ ] Active branch highlighted, inactive dimmed
- [ ] Toggle per bot in sidebar
- [ ] Graceful when no trace data present (panel hidden)
- [ ] Updates on round change (play, scrub, step)
- [ ] File under 200 LOC

**Depends on:** T65.2

---

### T65.4 — Ghost replay for Kill Switch | Cx: 25 | P2

**Description:** Build `engine/ghost_replay.py` to fork match state at any round, substitute one bot's action, and re-simulate the remainder. Show "what would have happened" as an alternate timeline. Output: ghost match JSON with divergence point marked. Engine is deterministic (seeded RNG), so forking is reliable.

**AC:**
- [ ] `ghost_replay(match_data, round_num, bot_emoji, alt_action, seed)` returns ghost match JSON
- [ ] Ghost match diverges from specified round, simulates to completion
- [ ] Divergence point clearly marked in output
- [ ] Uses same seed for deterministic replay
- [ ] Original match data unmodified
- [ ] Tests cover: substitute attack→defend, early divergence, late divergence
- [ ] File under 200 LOC, ruff clean

**Depends on:** —

---

## Phase 6: Open Source — Engines (Week 6)

### T66.1 — Mono-package structure | Cx: 25 | P0

**Description:** Restructure for `pip install agent-grounds` as a single PyPI package containing both Kill Switch and Code Circuit. CLI entry points: `agentgrounds killswitch play`, `agentgrounds circuit race`. Both games' engines, viewers, and TV layers included. pyproject.toml with unified metadata. The existing `agentgrounds` package structure in npc-wars already has the namespace — extend it to include Code Circuit.

**AC:**
- [ ] `pip install agent-grounds` installs both games
- [ ] `agentgrounds killswitch play` runs Kill Switch match
- [ ] `agentgrounds circuit race` runs Code Circuit race
- [ ] Both games produce TV output (commentary, highlights)
- [ ] `agentgrounds --help` lists available games
- [ ] Package builds cleanly (`python -m build`)
- [ ] Test: install from built wheel, run both games, verify output

**Depends on:** T59.4, T60.1

---

### T66.2 — Viewer unification | Cx: 20 | P0

**Description:** Unify viewer chrome across both games. Shared: controls (play/pause/speed/scrub), sidebar layout, commentary ticker, settings. Game-specific: canvas rendering, effects, overlays. Single `viewer/` directory with `viewer.html` that loads the correct game renderer based on match JSON type detection. Kill Switch and Code Circuit viewers both get commentary ticker from T62.3.

**AC:**
- [ ] Single HTML entry point detects game from loaded JSON
- [ ] Shared controls work for both games
- [ ] Commentary ticker works for both games
- [ ] Kill Switch-specific effects preserved
- [ ] Code Circuit-specific telemetry panels preserved
- [ ] No regression in either game's viewer functionality
- [ ] Test: load KS match, load CC replay, verify both render correctly

**Depends on:** T62.3

---

### T66.3 — Documentation + on-ramp | Cx: 15 | P0

**Description:** Write the open-source documentation: README with compelling demo, Getting Started guide (pip install → init → play → watch episode), PROMPT.md per game (already exists — verify and polish), Contributing guide. The README is the first thing anyone sees — it needs to show a match generating a sports broadcast in 3 commands.

**AC:**
- [ ] README: 3-command demo, screenshot/gif, feature list, architecture overview
- [ ] Getting Started: pip install → init → play → episode in under 60 seconds
- [ ] PROMPT.md per game reviewed and polished
- [ ] Contributing guide: how to add commentary templates, effects, new games
- [ ] LICENSE file (choose license)
- [ ] All docs render correctly on GitHub

**Depends on:** T66.1

---

## Phase 7: Open Source — TV + Discord + Website (Week 7)

### T67.1 — Discord bot unification | Cx: 25 | P0

**Description:** Merge Kill Switch and Code Circuit Discord bots into a single bot. Commands: `/killswitch play`, `/circuit race`, `/tv highlights`, `/season standings`. Video queue serves both games. Unified formatters for stats, standings, and episode summaries. Open-source the bot code with setup instructions for community self-hosting.

**AC:**
- [ ] Single bot binary serves both games
- [ ] `/killswitch` and `/circuit` command groups
- [ ] `/tv highlights <game>` shows recent highlights
- [ ] `/season standings <game>` shows current season
- [ ] Self-hosting docs: Discord app setup, env vars, running on any machine
- [ ] Tests cover: command routing, multi-game formatting

**Depends on:** T64.3, T66.1

---

### T67.2 — Website episode browser | Cx: 20 | P1

**Description:** Add episode browser to agentgrounds.ai (agentgrounds-web). Static Astro page that loads episode JSON files and renders them in an embedded viewer. Episode list with thumbnails (generated from first frame), winner, drama tier, date. No server — episodes served as static JSON from a `public/episodes/` directory synced from Nathan.

**AC:**
- [ ] `/tv` page on agentgrounds.ai shows episode list
- [ ] Click episode → embedded viewer with commentary
- [ ] Episodes organized by game and season
- [ ] Static — no API calls, no server
- [ ] Responsive design (desktop + mobile)
- [ ] Test: page loads, episode renders, navigation works

**Depends on:** T62.1, T66.2

---

### T67.3 — Website season standings | Cx: 15 | P1

**Description:** Add season standings page to agentgrounds.ai. Static Astro page consuming standings JSON generated by Nathan. Shows current season standings per game with tier badges (Bronze/Silver/Gold/Diamond), points, wins, streaks. Updated weekly when Nathan syncs standings JSON to the repo.

**AC:**
- [ ] `/seasons` page shows standings for active seasons
- [ ] Tier badges color-coded
- [ ] Per-game tabs (Kill Switch, Code Circuit)
- [ ] Static JSON consumption, no API
- [ ] Standings JSON format documented for contributors
- [ ] Test: page loads with sample data

**Depends on:** T63.1

---

### T67.4 — SDK guide: Build Your Own Game | Cx: 15 | P2

**Description:** Write a guide for community developers to build new Agent Grounds games. Cover: implementing the platform contracts (GameEvent adapter, commentary generator, personality profiler), engine requirements (deterministic, seeded RNG, replay format), viewer integration, and how to register a new game in the CLI. Based on the actual interfaces from Kill Switch and Code Circuit.

**AC:**
- [ ] Guide covers: engine contract, event adapter, commentary, personality, viewer, CLI registration
- [ ] Includes working example of a minimal game (tic-tac-toe scale)
- [ ] References actual code from Kill Switch and Code Circuit as examples
- [ ] Published in docs/ and linked from README
- [ ] Reviewed for accuracy against actual platform contracts

**Depends on:** T61.1, T61.2, T66.3

---

## Phase 8: Polish + Launch (Week 8)

### T68.1 — End-to-end integration test | Cx: 20 | P0

**Description:** Build a comprehensive integration test that exercises the full pipeline: run match → TV enrichment → episode packaging → video render → Discord posting format. For both Kill Switch and Code Circuit. This is the gate that proves everything works together before launch.

**AC:**
- [ ] Test runs Kill Switch match → full episode with video (or frame render)
- [ ] Test runs Code Circuit race → full episode with video
- [ ] Test verifies Discord message format is valid
- [ ] Test verifies episode JSON conforms to schema
- [ ] Test verifies video render completes (or frame render if ffmpeg unavailable)
- [ ] All existing tests still pass
- [ ] CI-runnable (no Discord/Nathan dependency — mock posting)

**Depends on:** T64.3, T66.1

---

### T68.2 — Launch demo episode | Cx: 15 | P0

**Description:** Generate a showcase episode for the launch announcement. Run a curated Kill Switch match (interesting bots, good matchup, high drama potential) and a curated Code Circuit race (varied strategies, weather, pit stops). Render both as full episodes with commentary, highlights, personality, rivalry. These become the demo content in README, website, and announcement.

**AC:**
- [ ] Kill Switch demo episode: ≥3 bots, produces highlights, Watcher appears
- [ ] Code Circuit demo episode: ≥5 cars, safety car event, pit strategy variance
- [ ] Both episodes render as MP4 under 25MB
- [ ] Episode JSONs included in repo as examples
- [ ] Videos linked/embedded in README
- [ ] Demo is reproducible (seeded, documented command)

**Depends on:** T68.1

---

### T68.3 — Launch prep: repos + PyPI + site | Cx: 15 | P0

**Description:** Final launch checklist. GitHub repos set to public. PyPI package published. agentgrounds.ai updated with episode browser, standings, and getting started. Discord invite link in README. All CI green. Version tagged.

**AC:**
- [ ] GitHub repos public with README, LICENSE, CONTRIBUTING
- [ ] `pip install agent-grounds` works from PyPI
- [ ] agentgrounds.ai shows: landing page, game pages, TV browser, getting started
- [ ] Discord invite link functional
- [ ] CI passing on all repos
- [ ] Git tag for v1.0.0
- [ ] Launch announcement draft ready (blog post or GitHub discussion)

**Depends on:** T68.2, T67.1, T67.2

---

## Delivery Summary

| Phase | Sprint | Tasks | Total Cx | Focus |
|-------|--------|-------|----------|-------|
| 1: KS TV Core | S58–S59 | T58.1–T59.4 | 145 | Commentary, profiles, rivalry, highlights, dossier, monologues |
| 2: CC TV + Platform | S60–S61 | T60.1–T61.2 | 95 | Code Circuit TV, platform contracts |
| 3: Episodes + Video | S62–S63 | T62.1–T63.1 | 95 | Episode generator, video overlay, viewer ticker, seasons |
| 4: Discord Queue | S64 | T64.1–T64.4 | 85 | Ingestion, pipeline, posting, automation |
| 5: KS Advanced | S65 | T65.1–T65.4 | 90 | Meta analyzer, decision tracer, code overlay, ghost replay |
| 6: OSS Engines | S66 | T66.1–T66.3 | 60 | Mono-package, viewer unification, docs |
| 7: OSS TV + Site | S67 | T67.1–T67.4 | 75 | Discord unification, website, SDK guide |
| 8: Launch | S68 | T68.1–T68.3 | 50 | Integration test, demo, publish |
| **Total** | **S58–S68** | **27 tasks** | **695 Cx** | |

## Priority Order

**P0 — Must ship (launch blockers):**
1. T58.1 — Rivalry tracker
2. T58.2 — Personality profiler
3. T58.3 — Commentary engine
4. T59.1 — Highlight extractor
5. T59.2 — Watcher dossier
6. T59.4 — Wire TV into play command
7. T60.1 — Code Circuit commentary enhancement
8. T61.1 — Platform event contract
9. T61.2 — Platform commentary contract
10. T62.1 — Episode generator
11. T62.2 — Commentary video overlay
12. T63.1 — Season manager
13. T64.1 — Discord match ingestion
14. T64.2 — TV rendering pipeline
15. T64.3 — Discord channel posting
16. T66.1 — Mono-package structure
17. T66.2 — Viewer unification
18. T66.3 — Documentation
19. T68.1 — Integration test
20. T68.2 — Demo episode
21. T68.3 — Launch prep

**P1 — Should ship (significantly better with):**
22. T59.3 — Watcher monologues
23. T60.2 — Code Circuit personality profiler
24. T60.3 — Code Circuit rivalry tracker
25. T62.3 — Viewer commentary ticker
26. T64.4 — Season automation
27. T65.1 — Meta analyzer
28. T67.2 — Website episode browser
29. T67.3 — Website season standings

**P2 — Nice to have (launch without if needed):**
30. T65.2 — Decision tracer
31. T65.3 — Code overlay in viewer
32. T65.4 — Ghost replay
33. T67.4 — SDK guide
