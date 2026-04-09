# Epic Brief: Agent Grounds — Open Source Platform + TV Layer

> All free. All client-side. Net-zero. Pure cred.

## The Idea

Ship the entire Agent Grounds platform as open source over 8 weeks. Three repos (Kill Switch, Code Circuit, agentgrounds-web) converge into a single coherent offering: a platform where anyone can write Python bots, run matches locally, and get a procedural sports broadcast out the other end — commentary, highlights, personality profiles, rivalry arcs, and full episodic packaging. No SaaS. No server required. No cloud bills. The Discord bot runs on Nathan (Mac Mini), video renders locally, and the website is static on Vercel free tier. The only cost is a domain you already own.

The rollout is staged: each week ships something usable and shareable. By week 8, the community has everything — engine, TV layer, viewer, Discord bot, and the tools to build new games on the same foundation.

---

## What Exists Across All Three Repos

### Kill Switch (npc-wars) — 228 source files, 704 tests, 57 sprints shipped
- Full battle royale engine with d20 combat, equipment, terrain, traps, abilities
- Spectacle engine (`engine/spectacle.py`) — drama scoring with tier classification
- Watcher AI boss — pattern memory, sync tracking, adaptive difficulty
- Rival system — 5-tier training with pattern persistence and debrief
- Video pipeline — Pillow + ffmpeg MP4 rendering with effects
- Audio — procedural WAV generation, drama-tier hype tracks
- Viewer — canvas replay with 10+ visual effects, sidebar, controls
- Server — FastAPI with lobby, matchmaking, tournaments, leaderboard
- Discord bot — announcements, challenges, human copilot, community commands
- Data layer — profiles, match history, matchup stats, stat diffs, leaderboards, bot memory

### Code Circuit (npc-race) — 145 source files, 535 tests, 48 sprints shipped
- Full F1 racing engine with tire/fuel/weather/DRS/ERS physics
- **Already has commentary** (`engine/commentary.py`) — template-based event→text
- **Already has narrative events** (`engine/narrative.py`) — overtakes, battles, spins, pit stops, safety cars, fastest laps
- **Already has ghost system** (`engine/ghost.py`) — adversarial teaching with calibrated flaws
- **Already has championship** (`engine/championship.py`) — F1 points, standings, tiebreakers
- **Already has seasons** (`engine/season.py`) — preset calendars (short/full/classic)
- Drama system in `engine/drama.py` — collisions, spins, safety cars, weather
- Viewer — canvas replay with telemetry panels, timing tower, car renderer
- Server — FastAPI with lobby, car submission, leaderboard

### Agent Grounds Web (agentgrounds-web) — 133 source files, 146 tests
- Astro + Three.js + Rapier physics
- 3D voxel arena: robot builds logo, game actors destroy it, logo reforms
- API proxy routes for both Kill Switch and Code Circuit
- CRT monitor aesthetic, bedroom scene, game selection UI
- Deployed on Vercel free tier

---

## The Discovery: Code Circuit Is Ahead

Code Circuit already has game-specific versions of 3 of the 6 TV features:

| TV Feature | Kill Switch | Code Circuit |
|------------|-------------|--------------|
| Commentary | Needs building | **Already exists** (`engine/commentary.py`) |
| Narrative Events | Spectacle engine (drama scoring) | **Already exists** (`engine/narrative.py` — RaceEvent class) |
| Ghost/What-If | Needs building | **Already exists** (`engine/ghost.py` — ghost car system) |
| Championships/Seasons | Tournament system (bracket-based) | **Already exists** (`engine/championship.py` + `engine/season.py`) |
| Rivalry Tracking | `data/matchup_stats.py` (partial) | Not yet |
| Personality Profiles | Not yet | Not yet |

This means the platform-level abstraction isn't speculative — we have **two concrete implementations** to extract from. The god doc principle ("copy first, extract after two working implementations") is satisfied for commentary, events, and seasons.

---

## Architecture: Fully Client-Side, Net-Zero

```
┌─ Anyone's Machine ──────────────────────────────────┐
│                                                       │
│  pip install agent-grounds                            │
│                                                       │
│  agentgrounds killswitch play                         │
│  → match.json + commentary + highlights + episode     │
│  → opens viewer in browser (local HTML file)          │
│  → optionally renders MP4 via ffmpeg                  │
│                                                       │
│  agentgrounds circuit race                            │
│  → race_replay.json + commentary + highlights         │
│  → opens viewer in browser                            │
│                                                       │
└──────────────────────┬────────────────────────────────┘
                       │ share JSON / MP4
                       ▼
┌─ Nathan (Mac Mini, already owned) ───────────────────┐
│                                                       │
│  Discord bot watches #submissions                     │
│  Renders full TV treatment (video + commentary)       │
│  Posts to #kill-switch-tv / #code-circuit-tv          │
│  Tracks seasons/rankings in local SQLite              │
│  Runs tournament brackets on schedule                 │
│                                                       │
└──────────────────────┬────────────────────────────────┘
                       │
                       ▼
┌─ Free Infrastructure (all $0) ───────────────────────┐
│                                                       │
│  agentgrounds.ai → Vercel free tier (static Astro)    │
│  github.com/agentgrounds → public repos               │
│  PyPI → agent-grounds package                         │
│  Discord → community server                           │
│  YouTube → auto-uploaded episodes (optional)           │
│                                                       │
│  Total recurring cost: $0 (domain already paid)       │
│                                                       │
└───────────────────────────────────────────────────────┘
```

### What Runs Where

| Component | Runs On | Cost |
|-----------|---------|------|
| Game engines | Player's machine | $0 |
| Commentary generation | Player's machine (part of `play` command) | $0 |
| Episode packaging | Player's machine | $0 |
| Video rendering | Player's machine or Nathan | $0 |
| HTML viewer | Player's browser (local file) | $0 |
| Discord bot | Nathan (Mac Mini) | $0 (already owned) |
| Season/league tracking | Nathan (SQLite) | $0 |
| Website | Vercel free tier | $0 |
| Package hosting | PyPI | $0 |
| Source hosting | GitHub | $0 |

**There is no server.** The FastAPI code in both repos becomes optional self-hosting scaffolding for anyone who wants to run a community server. Nathan runs the Discord bot and renders videos. Everything else is local.

---

## What Needs to Be Built

### Track A: Platform TV Layer (the extraction)

**A1. Platform Commentary Interface** — extract from two existing implementations
- Kill Switch: needs new `engine/commentary.py` (template-based, drama-tier-aware)
- Code Circuit: already has `engine/commentary.py` (event→text templates)
- Platform contract: `generate_commentary(events, drama_data, context) → list[CommentaryLine]`
- Each game provides: event types, drama scoring, context data
- Platform provides: tone scaling, highlight detection, episode structure

**A2. Platform Event/Narrative Interface** — extract from two implementations
- Kill Switch: `engine/spectacle.py` produces `SpectacleData` per round
- Code Circuit: `engine/narrative.py` produces `RaceEvent` per tick
- Platform contract: `GameEvent(type, timestamp, participants, data, drama_weight)`
- Each game maps its events to this format
- Platform consumes these for commentary, highlights, episodes

**A3. Platform Highlight Extractor** — new, game-agnostic
- Consumes `GameEvent` stream, identifies sequences where drama exceeds threshold
- Extracts clip ranges (N events before/after trigger)
- Tags highlights by type, participants, drama score
- Output: highlight manifest JSON

**A4. Platform Episode Generator** — new, game-agnostic
- Orchestrates: cold open → pre-match → match → post-match
- Cold open: rivalry data + meta narrative (game-specific data, platform template)
- Pre-match: participant profiles + equipment/setup reveals
- Match: commentary track + highlights
- Post-match: stat diffs + highlight reel + season standings
- Output: episode manifest JSON that any viewer can consume

**A5. Platform Personality Profiler** — new, game-agnostic
- Consumes: stat history, behavior patterns, loadout/setup choices
- Produces: trait list, archetype variant, flavor bio
- Each game provides: what stats matter, what patterns to detect
- Platform provides: profiling framework, trait vocabulary, bio templates

**A6. Platform Rivalry Tracker** — new, game-agnostic
- Consumes: match history between participant pairs
- Produces: rivalry score (0-100), trend, notable stats, narrative hooks
- Kill Switch: bot-vs-bot combat stats
- Code Circuit: car-vs-car position battles, overtake history

**A7. Platform Season Manager** — extract from two implementations
- Kill Switch: tournament brackets (server/tournament_*.py)
- Code Circuit: championship points + season calendars (engine/championship.py, engine/season.py)
- Platform contract: season config → round scheduling → standings → finale
- Each game provides: scoring rules, tiebreakers
- Platform provides: tier system, promotion/relegation, history

### Track B: Kill Switch TV Features (game-specific)

**B1. Kill Switch Commentary** — implement `engine/commentary.py`
- Template-based, consumes spectacle data + personality + rivalry
- Drama tier modulates tone (calm→chaos)
- Kill Switch-specific: Watcher events, equipment references, terrain callouts

**B2. Watcher Dossier** — `engine/watcher_dossier.py`
- Surface PatternTable as human-readable predictions
- Sync score as "How well does the Watcher know you?"
- Pattern change rate between matches

**B3. Watcher Monologues** — `engine/watcher_dialogue.py`
- Template taunts from pattern data
- Injected into match events at spawn/kill/sync milestones

**B4. Decision Tracer** — `engine/decision_trace.py`
- Instrument `decide()` to capture branch execution
- Added to match JSON per-round
- Viewer overlay shows which condition fired

**B5. Kill Switch Meta Analyzer** — `data/meta_analysis.py`
- Equipment loadout win rates
- Dominant strategy detection
- Counter-pick suggestions

### Track C: Code Circuit TV Features (game-specific)

**C1. Code Circuit Commentary Enhancement** — extend existing `engine/commentary.py`
- Add drama-tier tone scaling (currently flat)
- Add personality references, rivalry callouts
- Add weather/strategy narrative ("switching to wets was the right call")

**C2. Code Circuit Personality Profiler** — game-specific traits
- "Conservative tire manager", "late braker", "rain specialist", "one-stop hero"
- Derived from pit strategy, tire wear patterns, weather performance

**C3. Code Circuit Rivalry Tracker** — game-specific
- Position battle history between car pairs
- Overtake/defend success rates
- Championship points head-to-head

### Track D: Open Source Packaging

**D1. Mono-package Release** — `pip install agent-grounds`
- Single PyPI package containing Kill Switch + Code Circuit
- CLI: `agentgrounds killswitch play`, `agentgrounds circuit play`
- TV features included: commentary, highlights, episodes auto-generated on play

**D2. Viewer Unification**
- Both games share viewer chrome (controls, sidebar, commentary ticker)
- Game-specific: canvas rendering, effects, overlays
- Single `viewer/` directory in package, game-selected at load time

**D3. Discord Bot Unification**
- Single bot serving both games
- Commands: `/killswitch play`, `/circuit race`, `/tv highlights`, `/season standings`
- Video queue: matches → render → post to game-specific channels

**D4. Website Integration** — agentgrounds.ai (agentgrounds-web)
- Static pages: game descriptions, getting started, viewer embed
- Episode browser: loads episode JSON from Discord/GitHub, renders in viewer
- Season standings: static JSON generated by Nathan, displayed on site
- No server required — all static assets on Vercel free tier

**D5. Documentation & On-Ramp**
- PROMPT.md per game (already exists) — paste into Claude/Gemini, get a bot
- Getting started guide: pip install → init → play → watch episode
- "Build Your Own Game" SDK guide: implement the platform contracts
- Contributing guide: how to add commentary templates, effects, viewer features

### Track E: Discord Video Queue (the glue)

**E1. Match Ingestion**
- Discord bot watches #submissions for match JSON uploads
- Or: bot runs matches on Nathan from submitted bot files
- Validates JSON schema, rejects malformed

**E2. TV Pipeline**
- Match JSON → commentary generation → highlight extraction → episode packaging
- Episode → video render (MP4 via existing Pillow+ffmpeg pipeline)
- Commentary overlay burned into video

**E3. Channel Posting**
- Rendered video + episode summary posted to game-specific channels
- #kill-switch-tv, #code-circuit-tv
- Includes: winner, key highlights, season standings update
- Threaded replies with full stats, diffs, Watcher dossier (Kill Switch)

**E4. Season Automation**
- Nathan runs scheduled matches (cron or Discord command)
- Season standings updated in SQLite after each match
- Weekly power rankings posted to #standings
- Season finale auto-scheduled when enough matches complete

---

## Integration Points

| Platform Component | Kill Switch Source | Code Circuit Source | Platform Contract |
|---|---|---|---|
| Commentary | New `engine/commentary.py` | Existing `engine/commentary.py` | `generate_commentary(events, drama, ctx) → [Line]` |
| Events | `engine/spectacle.py` SpectacleData | `engine/narrative.py` RaceEvent | `GameEvent(type, ts, participants, data, weight)` |
| Highlights | New | New | `extract_highlights(events, threshold) → [Clip]` |
| Episodes | New | New | `build_episode(match, commentary, highlights, profile, rivalry) → Episode` |
| Personality | New | New | `profile_participant(history, patterns) → Profile` |
| Rivalry | `data/matchup_stats.py` | New | `compute_rivalry(pair, history) → Rivalry` |
| Seasons | `server/tournament_*.py` | `engine/championship.py` + `engine/season.py` | `Season(config, scoring, standings)` |
| Ghost/What-If | New `engine/ghost_replay.py` | Existing `engine/ghost.py` | Game-specific (different mechanics) |

---

## Constraints & Risks

### Cross-Repo Coordination
- Three repos must converge. Risk: interface mismatches between platform contracts and game implementations.
- Mitigation: define contracts in Kill Switch first (largest codebase), validate against Code Circuit, then extract.

### Code Circuit Maturity
- Race has 535 tests and a working engine but hasn't gone through the same polish sprints as Kill Switch (S50-S57).
- Commentary exists but is simple (event→text, no drama scaling, no personality).
- No rival system, no Watcher equivalent, no equipment/loadout system.
- Risk: Code Circuit TV features may be thinner than Kill Switch's.
- Mitigation: this is fine — Kill Switch is the flagship. Circuit is the proof that the platform works with a second game.

### Oversized Files
- Kill Switch: `viewer/js/effects.js` (511), `events.js` (417), `engine/combat.py` (365), `engine/rounds.py` (350)
- Code Circuit: `engine/simulation.py`, `engine/sim_step.py` (likely large, need check)
- All new TV features go in new files — no existing files need to grow.

### Video File Sizes
- Discord free: 25MB limit. Kill Switch matches at 4fps/48px cells ~5-10MB. Fine.
- Code Circuit races are longer (multiple laps). May need lower resolution or shorter highlight clips.
- Mitigation: highlight-only videos for long races, full video for Kill Switch matches.

### The "Two Implementation" Principle
- The god doc says don't extract shared packages until two implementations exist.
- Commentary: two implementations exist (Kill Switch needs building, Code Circuit exists). ✓
- Events: two implementations exist (SpectacleData, RaceEvent). ✓
- Seasons: two implementations exist (tournaments, championship). ✓
- Personality, Rivalry, Highlights, Episodes: new for both — build in Kill Switch first, then port.

### No New Dependencies
- Template-based commentary: stdlib only. ✓
- Episode generator: stdlib only (JSON manipulation). ✓
- Video: Pillow + ffmpeg (already deps). ✓
- Discord: discord.py (already dep). ✓
- No LLM APIs, no TTS, no cloud services.

---

## The 8-Week Open Source Rollout

### Week 1-2: Kill Switch TV Core
**Goal:** `agentgrounds killswitch play` outputs commentary + highlights alongside match JSON.

- Build Kill Switch commentary engine (B1)
- Build highlight extractor (A3, Kill Switch-specific first)
- Build personality profiler (A5, Kill Switch-specific first)
- Build rivalry tracker (A6, Kill Switch-specific first)
- Watcher dossier + monologues (B2, B3)
- **Ship:** Kill Switch with TV features on `main`. Shareable matches with commentary.

### Week 3: Code Circuit TV + Platform Extraction
**Goal:** Both games produce commentary. Platform contracts defined.

- Enhance Code Circuit commentary (C1)
- Build Code Circuit personality + rivalry (C2, C3)
- Extract platform contracts from the two implementations (A1, A2)
- Define `GameEvent`, `CommentaryLine`, `Profile`, `Rivalry` interfaces
- **Ship:** Code Circuit with TV features. Platform interfaces documented.

### Week 4: Episode Packaging + Video Pipeline
**Goal:** Matches become episodes. Episodes become videos.

- Build episode generator (A4) — works for both games
- Wire commentary overlay into video pipeline (existing Pillow+ffmpeg)
- Build season manager (A7) — extract from tournament + championship
- **Ship:** `agentgrounds killswitch play --episode` produces full episode. Video render works.

### Week 5: Discord Video Queue
**Goal:** Nathan accepts match submissions and posts TV-quality videos.

- Build Discord match ingestion (E1)
- Build TV pipeline on Nathan (E2)
- Build channel posting with stats/highlights (E3)
- Season automation (E4)
- **Ship:** Discord community can submit matches, get back broadcast-quality videos.

### Week 6: Open Source — Engines
**Goal:** Public repos. Anyone can `pip install agent-grounds`.

- Mono-package release on PyPI (D1)
- Viewer unification (D2)
- Documentation + PROMPT.md on-ramp (D5)
- Getting started guide
- **Ship:** `pip install agent-grounds` works. README is compelling. First GitHub stars.

### Week 7: Open Source — TV Layer + Discord Bot
**Goal:** Full platform is public. Community can self-host everything.

- Discord bot unification and open source (D3)
- "Build Your Own Game" SDK guide
- Contributing guide
- Episode browser on agentgrounds.ai (D4)
- **Ship:** Anyone can fork, run their own league, render their own episodes.

### Week 8: Polish + Launch
**Goal:** The announcement. Everything works end-to-end.

- Kill Switch meta analyzer (B5)
- Decision tracer + code overlay (B4) — the "wow" feature for launch demos
- Ghost replay for Kill Switch (A3/platform, extends Code Circuit's ghost concept)
- Website polish — episode browser, season standings, game pages
- Write the launch post / Make the demo video
- **Ship:** Launch announcement with demo episode, GitHub repos, PyPI package, Discord invite.

### Parallel Tracks

```
Week:  1    2    3    4    5    6    7    8
       ├────┤────┤────┤────┤────┤────┤────┤
KS TV: ████████░░░░░░░░░░░░░░░░░░░░░░████  (core → polish)
CC TV: ░░░░░░░░████░░░░░░░░░░░░░░░░░░░░░░  (enhance)
Platf: ░░░░░░░░████████░░░░░░░░░░░░░░░░░░  (extract → episodes)
Queue: ░░░░░░░░░░░░░░░░████░░░░░░░░░░░░░░  (Discord pipeline)
OSS:   ░░░░░░░░░░░░░░░░░░░░████████░░░░░░  (package → docs)
Site:  ░░░░░░░░░░░░░░░░░░░░░░░░████████░░  (integrate → launch)
```

---

## Impact on Existing Code

### Kill Switch (npc-wars)
- New files only — no existing engine files modified
- `engine/commentary.py` (new), `engine/highlights.py` (new), `engine/personality.py` (new), `engine/rivalry.py` (new), `engine/watcher_dossier.py` (new), `engine/watcher_dialogue.py` (new), `engine/decision_trace.py` (new), `engine/episode.py` (new)
- `data/meta_analysis.py` (new), `data/rivalry_db.py` (new), `data/seasons.py` (new)
- Viewer: new JS modules (commentary.js, code_overlay.js). Existing app.js gets import hooks only.
- Video: `video/video_commentary.py` (new overlay layer in existing pipeline)

### Code Circuit (npc-race)
- Extend existing `engine/commentary.py` — add drama-tier tone scaling, personality refs
- New files: `engine/personality.py`, `engine/rivalry.py`
- Season system already exists — may need minor interface alignment with platform contract

### Agent Grounds Web (agentgrounds-web)
- New pages: `/killswitch/tv`, `/circuit/tv`, `/seasons`
- Episode browser component: loads JSON, renders in embedded viewer
- Season standings component: reads static JSON from Nathan
- No backend — all static Astro pages consuming JSON

---

## Out of Scope

- **SaaS / paid features** — everything is free, everything is client-side
- **LLM-powered commentary** — template-based only. No API keys required.
- **TTS / voice synthesis** — text overlay only
- **Real-time live commentary** — post-match generation from JSON
- **Custom domain purchase** — already owned
- **Server hosting** — Nathan handles Discord bot, everything else is static/local
- **Mobile app** — browser viewer only
- **Bot marketplace / trading** — not a thing
- **Remaining 7 announced games** — Kill Switch + Code Circuit for launch. Others later.
- **NPC-SDK extraction as a separate package** — the platform contracts live in the mono-package for now. Separate SDK is a post-launch concern when game #3 appears.

---

## The Net-Zero Math

| Item | Cost |
|------|------|
| agentgrounds.ai domain | Already paid |
| Vercel hosting | $0 (free tier, static) |
| GitHub repos | $0 (public) |
| PyPI package | $0 |
| Discord server | $0 |
| Nathan (Mac Mini) | $0 (already owned, already running) |
| ffmpeg + Pillow | $0 (open source) |
| YouTube uploads | $0 |
| LLM APIs | $0 (no LLM dependency) |
| **Total** | **$0/year** |

## What You Get

- A portfolio piece that demonstrates full-stack engineering across 3 repos, 1000+ source files, 1300+ tests
- An open-source platform with a genuine second game proving the architecture
- A procedural broadcast engine that turns every match into shareable content
- A Discord community that produces episodes without any human intervention
- The credibility of giving it all away

---

Brief ready. To generate the backlog:

```
/draft-backlog docs/brief-agent-grounds-epic.md
```
