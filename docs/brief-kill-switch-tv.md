# Feature Brief: Kill Switch TV — Procedural Esports Broadcast

## Idea

Transform Kill Switch from a game-you-play into a **show-you-watch** by layering six interconnected systems on top of the existing match engine. Every match already generates structured drama (spectacle scoring, Watcher patterns, momentum arcs, elimination order). The missing piece is a presentation layer that turns that data into narrative — commentary, dossiers, personality profiles, meta reports, prediction games, and full episodic packaging. The culmination is "Kill Switch TV": matches presented as episodes with cold opens, AI commentary, villain arcs, audience participation, and post-match analysis.

## Codebase Context

- **Stack:** Python 3.x (engine, data, server, CLI), vanilla JS (viewer), FastAPI (server), SQLite + JSON (persistence), Pillow + ffmpeg (video), procedural WAV (audio), Discord.py (bot)
- **Size:** ~228 source files, ~704 test files. 54 engine files, 24 CLI files, 21 server files, 10 viewer JS files, 7 video files, 7 audio files
- **Current sprint:** S47 (Tournaments, Phase 3B final). S1–S46 shipped. S48–S49 planned (browser flow, security hardening). S50–S57 completed (assessment, launch readiness, rival training, mirror graduation, rival polish, tech debt, queue resilience)
- **Oversized files (>200 LOC):** 34 source files, heaviest in viewer/js (effects 511, events 417), engine (combat 365, rounds 350, watcher_controller 255), server (rival_debrief 357, rival_factory 348)

## What Exists That This Touches

### Spectacle Engine — `engine/spectacle.py` (207 LOC)
- `SpectacleEngine.score_round()` already scores every round for drama (kill=4, near_death=4, multi_kill=6, etc.)
- `TIER_RANGES` classifies into calm/heating/intense/hype/chaos
- `TRIGGER_EFFECT_MAP` maps triggers → visual effects (shatter, fire_border, slow_mo, etc.)
- **Integration:** Commentary voice/tone scales with drama tier. Highlight reel clips where tier >= "hype"

### Match Writer — `engine/match_writer.py` (48 LOC)
- `build_match_data()` produces the complete match JSON: players, rounds (with positions, events, spectacle), eliminations, stats, carryover
- **Integration:** This is the source-of-truth for all commentary, highlight extraction, and episode packaging

### Watcher System — `engine/watcher_*.py` (7 files, ~31K LOC total)
- `watcher_memory.py`: `PatternTable` with context→action frequency tracking, cross-session decay (30-70%)
- `watcher_brain.py`: Counter-action selection from predicted player behavior
- `watcher_controller.py`: Spawn logic, sync tracking (0-100%), accuracy caps with rubber-banding
- `watcher_stats.py`: Encounter history, sync milestones
- `watcher_spectacle.py`: Emits watcher_spawn, watcher_kill, sync_milestone events
- **Integration:** Dossier reads from PatternTable. Monologues generated from pattern predictions. Sync score becomes rivalry meter

### Rival System — `server/rival_*.py` (4 files)
- `rival_patterns.py`: Already wraps `PatternTable` for per-player persistence, has `get_pattern_summary()` and `compact_for_embed()`
- `rival_debrief.py`: Post-match analysis with pedagogical lessons per tier
- `rival_factory.py`: Tier 1-5 rival bot generation
- `rival_db.py`: Player rival state persistence
- **Integration:** Pattern summary is the data source for Watcher Dossier. Debrief structure extends to episode post-match analysis

### Data Layer — `data/*.py` (9 files)
- `player_profiles.py`: Persistent win/loss/streak/career stats per player
- `match_history.py`: `get_all_matches()`, per-player history, match-by-ID lookup
- `matchup_stats.py`: Per-archetype win/loss records (already tracks head-to-head)
- `stat_diff.py`: Per-match stats vs lifetime averages (improved/regressed/neutral)
- `leaderboard.py`: Rankings by wins, win rate, kills
- `bot_memory.py`: Persistent dict per bot (max 10KB) for cross-match learning
- **Integration:** Rivalry arcs built from matchup_stats + match_history. Meta reports from leaderboard + equipment data. Personality profiles from stat_diff patterns over time

### Audio System — `audio/*.py` (7 files)
- `hype.py`: Already maps drama tiers → ambient/mid/peak music intensity with crossfade timeline
- `stingers.py`: Hit/kill/death sound effects
- `waveforms.py`: Procedural WAV generation (sine, square, noise)
- **Integration:** Commentary audio layer sits on top of hype track. Stingers punctuate key commentary moments

### Video System — `video/*.py` (6 files)
- `video_render.py`: Frame rendering pipeline (grid → bots → effects → overlay → spectacle effects)
- `video_effects.py`: Visual FX per event type
- `video_overlay.py`: Kill feed, HP bars, round counter, standings
- **Integration:** Commentary text overlay or TTS audio track added to video pipeline. Highlight clips extracted by time-stamping high-drama rounds

### Viewer — `viewer/js/*.js` (10 files)
- `app.js`: Match JSON loader, replay controller
- `effects.js`: Canvas-based drama FX (shatter, fire_border, slow_mo, glitch, dark_entrance, etc.)
- `live.js`: Live/websocket viewer mode
- `audio.js`: Browser procedural audio synth mapped to drama tiers
- `sidebar.js`: Bot list with HP/energy/kills
- **Integration:** Commentary text overlay in sidebar or bottom ticker. Code replay overlay as new panel. Prediction UI as pre-round overlay during live mode

### Discord Bot — `discord_bot/*.py` (10+ files)
- `announcements.py`: Match start/end notifications
- `human_play.py`: Real-time human input during matches
- `commands/`: Challenge, leaderboard, results, community commands
- **Integration:** Audience voting via Discord reactions/buttons. Prediction market via Discord commands. Episode notifications with "Previously on..." summary

### Server — `server/routes/*.py` (14 files)
- `match.py`: GET match by ID
- `stream.py`: SSE match streaming
- `tournament.py`: Tournament CRUD + runner
- `stats.py`: Player stats API
- `share.py`: Shareable match links
- **Integration:** New routes for commentary, dossiers, predictions, episode packaging, meta reports

### Equipment — `engine/equipment.py` (248 LOC)
- Full loadout system with 40-credit budget, weapons/armor/accessories/tactical items
- **Integration:** Meta reports aggregate equipment choices across matches vs win rates. Signature builds = named loadout+stat combos tracked in profiles

## What Needs to Be Built

### Phase 1: Data Enrichment Layer (foundation for all features)

**1A. Rivalry Tracker** — `engine/rivalry.py` + `data/rivalry_db.py`
- Track head-to-head history between bot pairs across matches
- Store: wins, losses, kill counts, rounds of dominance, streaks
- Source: iterate `match_history` + `matchup_stats`, aggregate by bot-pair
- Output: rivalry score (0-100), trending direction, notable stats

**1B. Personality Profiler** — `engine/personality.py`
- Analyze bot behavior patterns across matches to generate personality profile
- Inputs: stat_diff history, action frequency from pattern tables, equipment choices, callback usage
- Output: trait list (e.g., "aggressive opener", "trap-obsessed", "storm dodger"), archetype variant name, flavor bio
- Used by: commentary, code overlay, episode intros

**1C. Meta Analyzer** — `data/meta_analysis.py`
- Aggregate equipment loadouts + stat allocations across all matches
- Compute win rates per weapon, armor, accessory combo
- Detect dominant strategies (>60% win rate with >5 matches)
- Output: weekly meta report JSON (top builds, counter picks, rising/falling strategies)

### Phase 2: Commentary Engine

**2A. Commentary Generator** — `engine/commentary.py`
- Consume round-by-round match data + spectacle data + personality profiles + rivalry data
- Generate play-by-play (factual: "Tank moves to high ground") and color commentary (analytical: "Smart positioning — that's how they beat Kiter last match")
- Drama tier modulates tone: calm=observational, heating=building tension, hype=excited, chaos=screaming
- Template-based with variable substitution (not LLM-dependent for v1, optional LLM enhancement later)
- Output: per-round commentary strings with timing, tone, and emphasis markers

**2B. Highlight Extractor** — `engine/highlights.py`
- Scan match rounds for drama_score >= threshold (default: "hype" tier)
- Extract highlight clips: 2 rounds before trigger → trigger round → 1 round after
- Tag each highlight: type (kill, near_death, chain_bump, watcher_event), participants, drama score
- Output: highlight manifest JSON with round ranges, tags, and commentary snippets

**2C. Commentary Overlay** — `viewer/js/commentary.js` + `video/video_commentary.py`
- Viewer: text ticker at bottom of replay with commentary strings, auto-advancing with rounds
- Video: burned-in text overlay or optional TTS audio track

### Phase 3: Watcher Nemesis System

**3A. Watcher Dossier** — `engine/watcher_dossier.py` + API route
- Read PatternTable for a player, produce human-readable dossier
- Format: "Context: below_30_hp → Predicted action: rest (78%), Expected counter: attack"
- Include sync score as "How well does the Watcher know you?" percentage
- Include pattern change rate: "You've become 23% less predictable since last match"

**3B. Watcher Monologues** — `engine/watcher_dialogue.py`
- Template-based taunts generated from pattern data
- Context-aware: different taunts for high-sync ("I know what you'll do") vs low-sync ("Interesting... you've changed")
- Triggered at: spawn, kill, sync milestone, player death
- Output: dialogue strings with timing, injected into match events

**3C. Dossier UI** — viewer panel + Discord embed + API endpoint
- Viewer: toggleable panel showing live Watcher dossier during replay
- Discord: `/watcher-dossier` command showing pattern summary
- Server: GET `/api/watcher/dossier/{player_id}`

### Phase 4: Code as Content

**4A. Decision Tracer** — `engine/decision_trace.py`
- Instrument `decide()` execution to capture which branch fired
- Record: condition evaluated, result, state variables that influenced decision
- Sandboxed: runs in existing bot sandbox, captures trace without exposing source
- Output: per-round decision trace added to match JSON

**4B. Code Replay Overlay** — `viewer/js/code_overlay.js`
- Display decision trace alongside replay
- Show: "IF enemy_distance == 1 AND hp > 30 → ATTACK" with highlighted active branch
- Collapsible panel, toggleable per bot
- For bots that opt-in to code visibility only

**4C. Bot Breeding** — `engine/breeding.py`
- Combine two bot codebases via AST manipulation
- Inheritance rules: pick `decide()` structure from parent A, combat heuristics from parent B
- Offspring stored with lineage metadata in bot_memory
- Breeding UI: select two bots, preview trait inheritance, generate offspring

### Phase 5: Spectator Games

**5A. Prediction Market** — `server/predictions.py` + `data/prediction_db.py`
- Fake currency (Drama Coins) for spectators
- Pre-round predictions: "Will anyone die?" "Who attacks first?" "Will Watcher spawn?"
- Post-round resolution with payout
- Leaderboard of best predictors
- Discord integration: reaction-based predictions during live matches

**5B. Ghost Replay** — `engine/ghost_replay.py`
- Fork match state at any round, substitute one bot's action, re-simulate
- Show "what would have happened" as alternate timeline overlay
- Viewer: split-screen or toggle between actual and ghost timeline
- Limited to post-match analysis (not real-time)

**5C. Mind-Read Score** — `engine/mind_read.py`
- Track when a bot's `react()` callback correctly predicts opponent's next action
- Score: prediction accuracy percentage over match lifetime
- Surface in stats, commentary, and episode narratives

### Phase 6: Episode Packaging (CULMINATION)

**6A. Episode Generator** — `engine/episode.py`
- Orchestrates all prior systems into a single "episode" package
- Structure:
  1. **Cold Open** ("Previously on Kill Switch..."): rivalry recaps from rivalry_db, pattern changes from dossier, meta shifts from meta_analysis
  2. **Pre-Match** : player intros with personality profiles, equipment reveals, audience predictions
  3. **Match**: full commentary track, Watcher monologues, code traces, prediction resolutions
  4. **Post-Match**: stat diffs, highlight reel, prediction payouts, Watcher dossier updates, "Next episode" teaser
- Output: episode manifest JSON referencing all sub-artifacts

**6B. Audience Participation** — Discord voting + server integration
- Pre-episode vote: map selection, match mode, Watcher spawn toggle
- Discord buttons/reactions for voting, results fed to match config
- Vote history tracked for "audience influence" stats

**6C. Season Manager** — `data/seasons.py` + `server/routes/seasons.py`
- Season structure: 10-episode arcs with promotion/relegation tiers (Bronze/Silver/Gold/Diamond)
- Weekly power rankings computed from match results + momentum + meta position
- Season finale: top-4 tournament bracket
- Persistent season history for cross-season narratives

## Integration Points

| New Component | Imports From | Publishes To | API Route | DB/Storage |
|---|---|---|---|---|
| Rivalry Tracker | `data/match_history`, `data/matchup_stats` | Commentary, Episode | `/api/rivalry/{bot_pair}` | `data/rivalry.json` |
| Personality Profiler | `data/stat_diff`, `server/rival_patterns`, `engine/archetype` | Commentary, Episode, Viewer | `/api/personality/{bot}` | `data/personalities.json` |
| Meta Analyzer | `data/match_history`, `engine/equipment` | Commentary, Episode, Discord | `/api/meta/report` | `data/meta_reports/` |
| Commentary Generator | Spectacle, Rivalry, Personality, Dossier | Viewer, Video, Episode | `/api/match/{id}/commentary` | Inline in episode JSON |
| Highlight Extractor | Spectacle, Commentary | Video, Episode, Discord | `/api/match/{id}/highlights` | Inline in episode JSON |
| Watcher Dossier | `engine/watcher_memory`, `server/rival_patterns` | Commentary, Viewer, Discord | `/api/watcher/dossier/{player}` | Reads existing pattern files |
| Watcher Monologues | Watcher Dossier, PatternTable | Match events, Viewer, Video | Injected into match JSON | Template library |
| Decision Tracer | Bot sandbox, `engine/rounds` | Viewer overlay, Commentary | Embedded in match JSON | Per-round trace in match data |
| Prediction Market | Match stream, Discord | Episode, Leaderboard | `/api/predictions/*` | `data/predictions.db` (SQLite) |
| Ghost Replay | `engine/game.run_match`, match JSON | Viewer, Episode | `/api/match/{id}/ghost` | On-demand computation |
| Episode Generator | All above | Viewer, Video, Discord, YouTube | `/api/episodes/*` | `data/episodes/` |
| Season Manager | Episode data, Leaderboard | Discord, Viewer | `/api/seasons/*` | `data/seasons.db` (SQLite) |

## Constraints & Risks

### Oversized Files in the Path
- `viewer/js/effects.js` (511 LOC) — adding commentary overlay increases pressure. Commentary should be a new file.
- `viewer/js/events.js` (417 LOC) — code overlay adds here. Must be a separate module.
- `engine/watcher_controller.py` (255 LOC) — dossier reads from this but doesn't modify it. Safe.
- `server/rival_debrief.py` (357 LOC) — episode post-match analysis extends this pattern. Extract shared helpers.

### Unfinished Work
- S47 T47.3 (tournament bracket page) and T47.4 (Phase 3B gate) still pending
- S48 (browser flow) and S49 (security hardening) planned but not started
- Tournament runner exists but no season/league structure yet

### Missing Tests
- Video pipeline has minimal test coverage
- Audio generation has minimal test coverage
- Discord bot commands have limited test coverage
- These gaps affect Phase 2C (commentary overlay in video) and Phase 5A (Discord predictions)

### Dependencies Needed
- None for v1 (template-based commentary). Optional later: LLM API for enhanced commentary, TTS library for audio commentary
- SQLite already available via server. No new deps for prediction/season DBs

### Tech Debt
- 26 broad exception handlers across source (non-test)
- `build/` directory contains stale copies of source modules
- Several engine files near 400 LOC limit — new features must go in new files

## Impact on Existing Code

- **Match JSON schema extends**: new keys `commentary`, `decision_trace`, `watcher_dialogue` added to round data. Viewer must gracefully ignore unknown keys (it already does).
- **Spectacle engine**: no modification needed — consumed read-only by commentary and highlights
- **Watcher memory**: no modification — dossier reads PatternTable via existing `to_dict()` / `get_pattern_summary()`
- **Viewer**: new JS modules added (commentary.js, code_overlay.js). Existing app.js gets small hooks to load new panels. No existing JS modified beyond import wiring.
- **Server**: new route files added. `routes/__init__.py` gets new router includes. No existing routes modified.
- **Match writer**: `build_match_data()` may need optional kwargs for commentary/trace injection, or episode generator wraps match data post-hoc (preferred — no engine changes).

## Suggested Phases

### Phase 1: Data Enrichment (2 sprints, parallelizable)
- Sprint A: Rivalry Tracker + Personality Profiler (independent of each other)
- Sprint B: Meta Analyzer + Mind-Read Score
- **Gate:** All four produce valid JSON from existing match data. Tests cover edge cases (no history, single match, etc.)

### Phase 2: Commentary + Highlights (2 sprints, sequential)
- Sprint C: Commentary Generator (template engine + drama-tier tone scaling)
- Sprint D: Highlight Extractor + Commentary Overlay (viewer + video)
- **Gate:** Full match produces commentary track. Highlight reel extracts ≥1 clip from any match with kills.

### Phase 3: Watcher Nemesis (1 sprint)
- Sprint E: Dossier + Monologues + Dossier UI
- **Gate:** Dossier renders for any player with ≥3 matches. Monologues appear in match events at spawn/kill/sync milestones.

### Phase 4: Code as Content (2 sprints)
- Sprint F: Decision Tracer (engine instrumentation)
- Sprint G: Code Replay Overlay + Bot Breeding
- **Gate:** Trace visible in viewer for builtin_bots. Breeding produces valid bot from two parents.

### Phase 5: Spectator Games (2 sprints)
- Sprint H: Prediction Market (server + Discord)
- Sprint I: Ghost Replay
- **Gate:** Predictions resolve correctly. Ghost shows divergent outcome for ≥1 round.

### Phase 6: Episode Packaging — CULMINATION (2 sprints)
- Sprint J: Episode Generator + Audience Participation
- Sprint K: Season Manager + Polish
- **Gate:** Full episode renders with cold open, commentary, predictions, post-match, teaser. Season with ≥3 episodes shows correct rankings.

**Total: ~11 sprints. Phases 1-3 are the highest-value work. Phase 6 is the payoff.**

Parallelization opportunities:
- Phase 1 sprints A and B are independent
- Phase 3 can run parallel with Phase 2D (different codebases: engine vs viewer)
- Phase 4F can start after Phase 2C (needs commentary foundation)
- Phase 5H (predictions) can start after Phase 2C (needs live match infrastructure)

## Out of Scope

- **LLM-powered commentary** — v1 is template-based. LLM enhancement is a future upgrade, not a blocker.
- **TTS / voice synthesis** — text commentary first. Audio narration is a polish feature.
- **Real-time live commentary** — v1 generates commentary post-match from JSON. Live commentary during websocket matches is Phase 2+.
- **Monetization** — no real currency, no paid features. Drama Coins are fake.
- **Mobile app** — viewer is browser-only.
- **YouTube auto-upload** — youtube/ module exists but auto-publishing episodes is a future integration.
- **Bot marketplace / trading** — equipment draft is in-game only, no trading between players.
- **AI-generated visuals** — no image generation for personality portraits or episode thumbnails.
