# The NPC Series — Build Spec

**You don't play. You code.**

> This is the canonical technical document for the NPC Series. It captures every architectural decision, the current state of each game, the security model, distribution strategy, and build order. Updated 2026-03-15.

---

## What This Is

The NPC Series is a collection of free, open-source games where you never touch a controller. You write a Python file. Your code plays for you. Every game follows the same pattern:

1. You write a Python file (bot, car, fighter, etc.)
2. You drop it in a folder
3. You run the game
4. You watch what happens

The cheat code for every NPC game is code. Everyone can cheat. Everyone has the same advantage. The skill ceiling is infinite because programming is infinite.

No accounts. No telemetry. No servers required. No dependencies beyond Python itself.

---

## Technical Principles (All Games)

1. **Python stdlib only** — zero `pip install` to run the engine. Players can import `math`, `random`, `collections`, `itertools`, `functools` in their uploaded files. The engine itself has zero runtime dependencies.
2. **Single HTML viewer** — no build step, no node_modules, no React. Vanilla HTML/CSS/JS with canvas rendering. Load `replay.json` and play.
3. **Replay-based** — the engine produces a JSON file. The viewer consumes it. Replays can be shared, archived, analyzed, and rendered on any device with a browser.
4. **Deterministic** — same inputs produce same outputs. Seeded RNG everywhere. A replay is reproducible from player files + seed.
5. **Sandboxed execution** — three-tier security model (see Security section). Player code cannot crash, compromise, or cheat the engine.
6. **No networking** — everything runs locally. Multiplayer is "send me your car file on Discord." Zero server costs.
7. **CLI-first** — every game ships a unified CLI: `npcwars init`, `npcrace init`, etc. Five minutes from `pip install` to watching your first match.
8. **Replay size discipline** — lightweight games (Wars, Race, Fighter) emit full-state JSON per tick. Heavy games (Colony, Fleet) must use **frame-delta compression** — only record what changed per tick, not full state. A Colony match with 400 ants at 30fps for 5000 ticks would produce a 200MB full-state JSON; deltas keep it under 5MB. This is a format decision, not a retrofit — design the replay schema with deltas from day one for any game with >50 entities or >1000 ticks.

---

## Series Identity

| Element | Value |
|---------|-------|
| Name | The NPC Series |
| Tagline | You don't play. You code. |
| Secondary | The cheat code is code. |
| Accent color | #ff6600 (orange) |
| Fonts | JetBrains Mono (code/data), Outfit (UI) |
| Viewer style | Dark theme, minimal, functional |
| Voice | Dry, specific, no marketing speak |
| License | MIT (every game, forever) |
| GitHub org | `fivedollarfridays` |

---

## The Games

### NPC Wars — Battle Royale
| Field | Value |
|-------|-------|
| Status | **Shippable** |
| Repo | `fivedollarfridays/npc-wars` |
| Local path | `~/projects/npc-wars/` |
| You upload | A bot (stats + combat AI) |
| Budget | 100 points across ATTACK, DEFENSE, SPEED, RANGE, HP |
| Strategy function | `decide(state) -> action tuple` |
| State receives | Nearby enemies, own health/energy, position, storm info, round |
| Returns | `("move", "north")`, `("attack", "south")`, `("rest",)`, `("defend",)`, etc. |
| Win condition | Last bot standing (200 round max, tiebreaker: HP > energy > kills > damage) |
| Grid | Auto-sized from bot count, storm shrinks from border |
| Actions | move, attack, rest, defend, ranged_attack (unlock), dash (unlock), taunt (unlock) |
| Action costs | move=5, attack=10, defend=10, rest=0 (restores 15), ranged=20, taunt=10, dash=15 |

**What's built (14 sprints, 1773 tests):**
- Engine: game loop, combat, grid, storm, rounds resolution, state management
- Sandbox: AST scanner (blocklist + module-level code check), builtins restriction, multiprocessing isolation, timeout enforcement
- Progression: line budget grows with wins/streaks/Watcher kills (50 base, 200 cap)
- Spectacle: drama scoring (5 tiers: calm→chaos), event-triggered visual/audio effects
- The Watcher ("The Cringe" 🍆): learning boss bot with pattern memory, counter-action selection, rubber-banding, cross-session persistence
- Audio: procedural waveform synthesis, stinger composition, drama-tier mapping
- Video: PIL frame rendering, grid/sprites/effects/HUD overlay, ffmpeg MP4
- Discord bot: slash commands (claim, results, leaderboard, match run), copilot buttons
- YouTube: OAuth2 flow, upload pipeline with metadata
- Realtime: WebSocket server for human input (copilot mode)
- CLI: `npcwars init/wizard/validate/battle` via argparse
- Distribution: `pip install npc-wars`, `[project.scripts]` entry point, built-in bots package
- Helpers DSL: Me, Enemies, Storm classes for bot authors
- Presets: 5 playstyles (aggro/tank/kiter/opportunist/chaos) with tuning sliders
- Wizard: interactive bot generator (CLI + non-interactive mode)
- CI: GitHub Actions (ruff + pytest + coverage gate + bot validation)

**Remaining tasks (3):**
| ID | Title | Cx | Priority |
|----|-------|----|----------|
| T13.11 | Community Hooks (Bot of Week, Bounty Challenges) | 25 | Nice-to-have (Discord-only) |
| T13.12 | Python Version Drop to 3.11 | 15 | Should-do (3.11 for tomllib; expands user base) |
| T13.13 | Integration Tests — Match Modes | 35 | Should-do (validates all modes) |

**Codebase stats:**
- 100 source files, ~8500 LOC
- 118 test files, ~17500 LOC
- Test:code ratio 2.1:1
- Max file: 393 lines (game.py, under 400 limit)
- 0 TODOs, 11 noqa/type-ignore (all justified)

---

### NPC Race — Racing
| Field | Value |
|-------|-------|
| Status | **Next build** |
| Repo | `fivedollarfridays/npc-race` (to create) |
| Local path | `~/projects/npc-race/` |
| You upload | A car (stats + race strategy AI) |
| Budget | 100 points across POWER, GRIP, WEIGHT, AERO, BRAKES |
| Strategy function | `strategy(state) -> dict` |
| State receives | Speed, position, tire wear, curvature, nearby cars, lap count |
| Returns | `{"throttle": 0.8, "boost": False, "tire_mode": "balanced"}` |
| Win condition | First to finish all laps |

**What makes it interesting:** Same car performs differently on different tracks. Power build dominates Monza but dies at Monaco. Tire strategy creates crossover points. Drafting rewards aero builds. 20 real-world-inspired track layouts.

**Engine status (per bible):** Built. 5 seed cars, viewer built, 20 track presets in progress. Needs sandbox, CLI, packaging, and the security model ported from Wars.

---

### NPC Fighter — 1v1 Fighting
| Field | Value |
|-------|-------|
| Status | **After Race** |
| Repo | `fivedollarfridays/npc-fighter` (to create) |
| Local path | `~/projects/npc-fighter/` |
| You upload | A fighter (stats + combat AI) |
| Budget | 100 points across POWER, SPEED, REACH, STAMINA, DEFENSE |
| Strategy function | `strategy(state) -> dict` |
| State receives | Distance to opponent, own stamina, opponent stance, hit history, round number |
| Returns | `{"action": "jab", "stance": "aggressive"}` |
| Win condition | Best of 5 rounds, KO or points |
| Actions | jab, heavy, block, dodge, advance, retreat |
| Stances | aggressive, neutral, defensive |

**What makes it interesting:** Rock-paper-scissors with continuous state. Heavy beats block on stamina drain. Dodge beats heavy. Jab beats dodge on recovery. Stamina management prevents spam. Reach creates spacing dynamics. Hit history enables adaptive strategies.

**Bracket mode:** 8 or 16 fighters, single elimination tournament.

---

### NPC Kitchen — Cooking Competition
| Status | Concept |
|--------|---------|
| Budget | 100 points: KNIFE_SKILL, PALATE, SPEED, CREATIVITY, COMPOSURE |
| Strategy receives | Available ingredients, time remaining, dishes completed, competitor progress, judge preferences |
| Returns | Action (prep/cook/plate/pivot), technique (sear/braise/roast/raw/ferment) |
| Win condition | Highest score from procedural judges |

---

### NPC Heist — Cooperative Squad Tactics
| Status | Concept |
|--------|---------|
| Roles | Hacker, Muscle, Stealth, Driver (pick one per file) |
| Budget | 100 points across role-specific stats |
| Strategy receives | Floor layout (fog of war), alarm state, guard positions, vault status, teammates, extraction timer |
| Returns | Move direction, action (hack/breach/sneak/grab/signal/drive) |
| Win condition | Highest loot extracted before time expires |

---

### NPC Fleet — Space Fleet Tactics
| Status | Concept |
|--------|---------|
| Budget | 100 fleet points to buy ships (Fighter=1, Corvette=3, Frigate=8, Cruiser=15, Carrier=25) |
| Strategy receives | Fleet positions/health, detected enemies, missile tracks, formation shape, sector control |
| Returns | Formation order, target priority, ship-level commands |
| Win condition | Destroy enemy fleet or control all sectors |

---

### NPC Pitch — Baseball
| Status | Concept |
|--------|---------|
| Roles | Pitcher OR Batter (upload one or both) |
| Pitcher budget | 100 points: VELOCITY, MOVEMENT, CONTROL, STAMINA, DECEPTION |
| Batter budget | 100 points: POWER, CONTACT, EYE, SPEED, CLUTCH |
| Win condition | Most runs after 9 innings |

---

### NPC Dungeon — Tower Defense / Dungeon Builder
| Status | Concept |
|--------|---------|
| Budget | 100 points across rooms + monsters |
| Strategy receives | Hero party position, hero health/mana, room state, monsters remaining, traps triggered |
| Returns | Monster behavior, trap activation timing, boss phase triggers |
| Win condition | Kill the hero party or reduce below escape threshold |

---

## Security Model

Two separate problems, one layered solution.

### Problem 1: Malicious Code (Safety)
Someone shares a car file that runs `os.system("rm -rf /")`. Anyone who runs it executes arbitrary Python on their machine.

### Problem 2: Game-Breaking Code (Fairness)
Strategy function reads engine memory, modifies own stats, takes 10 seconds to compute, allocates 8GB of RAM, or imports the engine module and patches the physics.

### Three-Tier Solution

#### Tier 1 — AST Scanning (before import, zero risk)
Parse the file's AST without executing it. Pure static analysis.

**Import model: ALLOWLIST (not blocklist).**
```python
ALLOWED_IMPORTS = {"math", "random", "collections", "itertools", "functools"}
```
Any import not in this set is rejected. This is the single biggest security decision — a blocklist always has gaps, an allowlist is closed by default.

**Blocked calls:** `eval`, `exec`, `compile`, `__import__`, `open`, `getattr`, `setattr`, `delattr`, `globals`, `locals`, `vars`, `type`, `dir`

**Blocked dunder attrs:** `__globals__`, `__builtins__`, `__subclasses__`, `__mro__`, `__bases__`, `__class__`, `__code__`, `__closure__`

**Module-level code:** Only imports, assignments, definitions, docstrings, `pass`, and `if __name__ == "__main__":` allowed at top level. Bare expressions and function calls are blocked.

**Semicolons:** Blocked inside strategy function body.

**Validator output:**
```
Validating cars/evil_car.py...
  BLOCKED: import os (line 3)
  BLOCKED: open() call (line 14)
  REJECTED — unsafe code detected

Validating cars/gooseloose.py...
  Stats: 100/100 budget ✓
  Strategy function: found ✓
  AST scan: clean ✓
  ACCEPTED
```

#### Tier 2 — Execution Sandbox (runtime restriction)
The strategy function runs in a restricted scope inside a forked subprocess.

**Restricted builtins whitelist:**
- Types: bool, bytes, complex, dict, float, frozenset, int, list, object, set, str, tuple
- Functional: abs, all, any, bin, callable, chr, divmod, enumerate, filter, format, hash, hex, id, isinstance, issubclass, iter, len, map, max, min, next, oct, ord, pow, print, range, repr, reversed, round, slice, sorted, sum, zip
- Exceptions: ArithmeticError, AssertionError, AttributeError, EOFError, Exception, IndexError, KeyError, LookupError, NameError, NotImplementedError, OverflowError, RuntimeError, StopIteration, TypeError, ValueError, ZeroDivisionError
- Constants: True, False, None

**No:** open, compile, exec, eval, __import__, getattr, setattr, delattr, globals, locals, vars, type, dir, breakpoint, input, memoryview, property, staticmethod, classmethod, super

**Frozen state:** Strategy function receives a deep copy of state (pickle across process boundary). Cannot access engine internals.

**Timeout:** Per-game configurable. Wars=1.0s (one subprocess per bot per round). Race=20ms strategy budget per tick for all cars combined (see batch execution below). The engine does NOT need to run in real-time — it simulates at whatever speed the hardware allows and produces a replay JSON. The viewer plays back at 30fps. This means strategy execution can safely take 20ms per tick even though a 30fps tick window is 33ms — the remaining 13ms is physics/state. If strategy is slow on a weak machine, the simulation just takes longer to complete. Only the replay playback is real-time.

**Process isolation:** `multiprocessing.Process` with game-specific execution models:
- **Wars (turn-based, ~200 rounds):** One subprocess per bot per round. Fork overhead is fine at 1s timeout.
- **Race (real-time, ~30 ticks/sec):** **Batch execution** — one subprocess per tick, all car strategy functions called inside it, all decisions returned in one pickle round-trip. Individual process-per-car won't work because fork overhead (10-50ms) exceeds the per-car time budget. Batch keeps process isolation while fitting the tick rate.
- **Fighter (turn-based, fast rounds):** One subprocess per fighter per turn, similar to Wars.

#### Tier 3 — Resource Limits (tournament mode, future)
For server-hosted competitions:
- Memory: 50MB per player file (ulimit)
- CPU: 100ms per tick
- Network: none
- Full isolation: Docker container per race (optional)

**Not needed for local-play launch.** Tier 1 + Tier 2 is sufficient.

### Current Implementation Status

| Component | NPC Wars | NPC Race (planned) |
|-----------|----------|-------------------|
| AST scanner | Blocklist (17 modules) | **Allowlist** (5 modules) |
| Blocked calls | 13 calls | Same |
| Blocked dunders | 8 attrs | Same |
| Module-level check | Done | Copy |
| Builtins restriction | Whitelist in subprocess | Copy |
| Process isolation | 1 subprocess per bot per round | **Batch**: 1 subprocess per tick, all cars inside |
| Timeout | 1.0s per bot | 20ms per tick (all cars combined, batch) |
| Stat budget validation | Exists but not in load path | **Wire into load path** |
| Line budget | count_decide_lines() exists | Adapt for strategy() |

### Sandbox Extraction Plan

1. Copy `bot_scanner.py` + `sandbox.py` into npc-race
2. Rename `decide` → `strategy`, adjust timeout and stat fields
3. Flip import model from blocklist to allowlist during the copy
4. Wire stat budget validation into the car load path
5. Build and ship Race
6. Extract `npc-sandbox` shared package from the two implementations
7. Both games depend on `npc-sandbox` going forward
8. Backport allowlist to Wars

**Why copy first:** Generalizing from one implementation is guessing. Generalizing from two is pattern matching. The second game will surface differences we can't predict (async execution? track data exposure? timeout too tight?). Extraction takes an afternoon once you have two working consumers.

### What You Can't Prevent (And Shouldn't Try)

Reading the engine source to understand exactly how physics work and writing a perfect strategy. That's not cheating — that's the game. Reading the source IS the skill ceiling. The line is: **reading the engine is allowed, modifying it at runtime is not.**

---

## Distribution Strategy

### Package Names

| Game | PyPI package | CLI command | Import |
|------|-------------|-------------|--------|
| NPC Wars | `npc-wars` | `npcwars` | `import npcwars` |
| NPC Race | `npc-race` | `npcrace` | `import npcrace` |
| NPC Fighter | `npc-fighter` | `npcfighter` | `import npcfighter` |
| (series) | `npc-series` | — | — |

### CLI Pattern (every game)

```bash
pip install npc-race
npcrace init                  # Scaffold: cars/, replays/, npcrace.toml
npcrace wizard                # Interactive car builder
npcrace validate cars/my.py   # AST scan + stat budget check
npcrace run --seed 42         # Run a race, deterministic
```

**Framework:** argparse subcommands (zero new deps). `init/wizard/validate` are universal. The "do the thing" command matches the game's vocabulary: `npcwars battle`, `npcrace run`, `npcfighter fight`.

**Config:** TOML via stdlib `tomllib` (Python 3.11+). Config file: `npcwars.toml`, `npcrace.toml`, etc. This pins the series to Python >=3.11. Dropping to 3.10 would require either a `tomli` backport (violates zero-deps principle) or switching to JSON config (viable — replays are already JSON). Decision: stay 3.11+ unless user demand proves otherwise.

**Minimum Python:** 3.11 (for `tomllib`). All games ship with `requires-python = ">=3.11"`.

### Platforms

| Platform | Purpose |
|----------|---------|
| **GitHub** | Primary home. Each game = own repo under `fivedollarfridays`. README is the landing page. |
| **PyPI** | `pip install npc-wars`, `pip install npc-race`, etc. |
| **Steam** | Phase 6. Free listing as "The NPC Series" (one $100 Steamworks fee). Requires PyInstaller or similar to bundle Python + engine into a binary — real packaging task. Workshop for file sharing. Don't let this block launch. |
| **itch.io** | Mirror of GitHub releases. Pay-what-you-want (default $0). |
| **Reddit** | r/gamedev, r/indiegaming, r/python. Replays as GIFs/videos. |
| **YouTube** | Race replays, tournament brackets, strategy breakdowns. |
| **Discord** | Community server. Channels per game. File sharing + tournaments. |

### Release Strategy

Launch all announced titles simultaneously. Ship with:
- NPC Wars (complete)
- NPC Race (complete)
- NPC Fighter (complete enough to play)
- Kitchen, Heist, Fleet, Pitch, Dungeon listed as "coming soon" with spec docs and templates
- Colony announced as final title (hardest build — needs frame-delta replays proven first)

### Local Development Structure

Flat siblings under `~/projects/`:
```
~/projects/npc-wars/     # Battle royale (done)
~/projects/npc-race/     # Racing (next)
~/projects/npc-fighter/    # Fighting (after race)
~/projects/npc-sandbox/  # Shared security (after race ships)
```
No wrapper directory. Series relationship lives in the GitHub org, not the filesystem.

---

## Architecture Constraints (All Games)

| Metric | Source Files | Test Files |
|--------|-------------|------------|
| Lines (error) | < 400 | < 600 |
| Lines (warning) | < 200 | < 400 |
| Function length | < 50 lines | < 50 lines |
| Functions per file | < 15 | < 30 |
| Imports per file | < 20 | < 40 |

---

## Build Order

### Phase 1: Ship NPC Wars (complete)
- [x] 14 sprints complete (1810 tests, all passing)
- [x] CLI distribution (`pip install npc-wars`)
- [x] Security hardening (AST scanner, builtins restriction, process isolation)
- [x] T13.12: Python version drop to 3.11
- [x] T13.13: Integration tests for match modes
- [x] T13.11: Community hooks (Discord commands)

### Phase 2: Build NPC Race
- Copy scanner/sandbox from Wars, rename decide→strategy
- **Flip to allowlist imports** during copy
- Wire stat budget into load path
- Build engine (if not already complete — bible says "done")
- Add CLI (init/wizard/validate/battle pattern)
- Add viewer (HTML canvas replay)
- Ship

### Phase 3: Build NPC Fighter
- Copy scanner/sandbox from Race (now has allowlist)
- Build fighting engine
- Bracket mode (8/16 single elimination)
- Ship

### Phase 4: Extract npc-sandbox
- Diff Wars and Race scanner/sandbox implementations
- Extract shared code into `npc-sandbox` package
- Both games depend on it
- Backport any improvements (allowlist to Wars if not already done)

### Phase 5: Announce remaining games
- Kitchen, Heist, Fleet, Pitch, Dungeon, Colony
- "Coming soon" with spec docs and file templates
- Community can see what they'll upload

### Phase 6: Simultaneous series launch
- All three playable games (Wars, Race, Fighter) on PyPI, GitHub, itch.io
- Discord server with per-game channels
- Reddit/YouTube marketing push
- Steam listing (requires PyInstaller packaging — separate task, don't block launch)

### Phase 7: Build NPC Colony
- Hardest build — hundreds of agents, pheromone diffusion, multi-colony shared map
- Requires frame-delta replay format (proven in earlier games first)
- Closest to a simulation engine; build after the game engine patterns are battle-tested across 3+ titles

### Phase 8: Discord Ranked Mode
- Do NOT build until there are active players requesting it
- Architecture documented below so engine decisions don't break compatibility
- The only hard requirement ranked mode places on the engine is **determinism** — same seed + same files = same replay, always

---

## Discord Ranked Mode

> Phase 8. Document exists to lock the architecture. Do not build until there are active players.

### Concept

Discord bot IS the ranked server. Players submit .py files as attachments. The bot validates (Tier 1 AST scan + stat budget), runs the engine in a Docker container (Tier 3 sandbox), posts replay + results back to the channel. The simulation never runs on the player's machine for ranked.

Players verify results by replaying locally against the same seed — determinism makes this trustworthy without trusting clients. No web app. No database login. No auth system. Discord handles identity, file uploads, notifications, moderation, and mobile for free.

### Trust Model

**Local mode:** Player runs engine, sees everything, results are unofficial. Stays forever.

**Ranked mode:** Player submits code, bot runs engine, results are canonical. Player never touches the ranked engine. They hand you a .py file, you hand them back a replay. They can verify the replay locally but they can't fake a result because they never ran the ranked simulation.

**Identity = Discord account.** No 2FA or encrypted keys needed because players aren't reporting results — the bot generates them. Require Discord phone verification and minimum account age to prevent alt-account abuse (configurable per server, built into Discord).

### Architecture

```
Player                    Discord Bot (host machine)              Channel
  │                              │                                    │
  ├─ /npcrace submit [car.py] ──▶│                                    │
  │                              ├─ AST scan (Tier 1)                 │
  │                              ├─ Stat budget validation            │
  │                              ├─ Store car file (local fs)         │
  │                              ├─ Reply: "GooseLoose accepted ✓"───▶│
  │                              │                                    │
  │  (race triggered by          │                                    │
  │   schedule or command)       │                                    │
  │                              ├─ Generate cryptographic seed       │
  │                              ├─ Collect all submitted cars        │
  │                              ├─ Spin up Docker container          │
  │                              │   ├─ No network                    │
  │                              │   ├─ 50MB memory cap               │
  │                              │   ├─ 30s wall clock timeout        │
  │                              │   ├─ Read-only fs (except /output) │
  │                              │   └─ Engine + car files mounted    │
  │                              ├─ Run engine, produce replay.json   │
  │                              ├─ Kill container                    │
  │                              ├─ Post replay.json as attachment───▶│
  │                              ├─ Post results embed (incl seed)──▶│
  │                              └─ Update leaderboard──────────────▶│
```

**Seed management:** Bot generates a cryptographically random seed at race trigger time. Seed is included in the results embed so players can verify locally. Admins cannot cherry-pick seeds.

### Bot Commands (per game)

Universal commands: `submit`, `withdraw`, `validate`, `leaderboard`, `mystats`, `replay`. The "run the thing" command matches game vocabulary: `race`, `battle`, `bracket`.

```
/npcrace submit    [attach .py]       Submit or update your car
/npcrace withdraw                     Remove your car from next race
/npcrace validate  [attach .py]       Dry-run AST scan + budget check
/npcrace cars                         List all submitted cars
/npcrace race      [track] [seed]     Admin-only: trigger a race
/npcrace replay    [race_id]          Fetch a past replay file
/npcrace leaderboard                  Season standings
/npcrace mystats                      Your win/place/show record
```

| Command | Who |
|---------|-----|
| submit, withdraw, validate, cars, replay, leaderboard, mystats | Everyone |
| race, battle, bracket (trigger execution) | Admin role only |

### File Storage

```
~/npc-ranked/
├── submissions/{game}/{discord_user_id}/car.py   # Latest overwrite
├── replays/{game}/{date}_{track}_{seed}.json
└── leaderboard/{game}.json                        # {user_id: {wins, podiums, races, points}}
```

No database. JSON on disk. Flat-file leaderboard works to ~100 players. SQLite (still stdlib) if it outgrows that.

### Docker Container Spec (Tier 3)

```bash
docker run --rm \
  --network none \
  --memory 50m \
  --cpus 1 \
  --read-only \
  --tmpfs /tmp:size=10m \
  -v $(pwd)/cars:/cars:ro \
  -v $(pwd)/output:/output \
  --stop-timeout 30 \
  npc-race:latest \
  python -m npcrace.cli run --cars-dir /cars --replay /output/replay.json --seed $SEED
```

One Docker image per game. Images are tiny (python:3.11-slim + engine = ~150MB). Build once, reuse for every race.

### Leaderboard Scoring

| Finish | Points |
|--------|--------|
| P1 | 25 |
| P2 | 18 |
| P3 | 15 |
| P4 | 12 |
| P5 | 10 |
| P6-P10 | 8, 6, 4, 2, 1 |
| DNF | 0 |

Season = calendar month. Monthly reset. All-time leaderboard maintained separately.

NPC Fighter tournament scoring: winner=25, finalist=18, semifinalists=12, quarterfinalists=6.

### Scheduling

**Manual:** Admin runs `/npcrace race monza`. Good for events.

**Scheduled:** Cron job on host machine triggers race via Discord webhook. The bot doesn't need to be the scheduler — cron + webhook is simpler and more reliable.

### What Discord Gives You For Free

Identity, file uploads, channels, roles, notifications, moderation, mobile, history. All replays and results persist in channel history as a free archive.

### What NOT to Build

- No web dashboard — Discord IS the dashboard
- No user accounts — Discord ID IS the account
- No replay hosting — Discord attachments ARE the host
- No matchmaking — scheduled races include everyone who submitted
- No ELO/MMR initially — simple points-per-finish
- No real-time spectating — replay posted after completion

### Ranked Mode Build Order (within Phase 8)

1. `/submit` and `/validate` commands on existing Discord bot
2. Local file storage for submissions
3. Docker image per game
4. `/race` command — admin triggers, bot runs container, posts results
5. Leaderboard JSON + `/leaderboard` command
6. Cron scheduling for automatic races
7. Extend to Wars and Fighter
8. Role assignment automation (Racer, Champion)

### Prerequisites

- At least one game engine is shippable (Phase 2+)
- AST scanner uses allowlist model
- Engine is deterministic (seeded RNG verified)
- Docker installed on host machine
- Existing Discord bot is running

---

## Game Status Tracker

| Game | Engine | Seed Files | Viewer | CLI | Sandbox | Tests | Status |
|------|--------|-----------|--------|-----|---------|-------|--------|
| NPC Wars | Done | 7 bots | Done | Done | Tier 1+2 (blocklist) | 1810 | **Complete** |
| NPC Race | Done | 5 cars | Done | — | — | — | **Next build** |
| NPC Fighter | — | — | — | — | — | — | After Race |
| NPC Kitchen | — | — | — | — | — | — | Concept |
| NPC Heist | — | — | — | — | — | — | Concept |
| NPC Fleet | — | — | — | — | — | — | Concept |
| NPC Pitch | — | — | — | — | — | — | Concept |
| NPC Dungeon | — | — | — | — | — | — | Concept |
| NPC Colony | — | — | — | — | — | — | Concept (last build) |

---

## Philosophy

### Why Free
The value isn't in the game — it's in the community. Car files, bot files, fighter files shared on Discord and GitHub. Tournament replays on YouTube. The games are the medium, not the product.

If monetization ever matters: tournament hosting, premium track/scenario packs (variety, not pay-to-win), merch, sponsored tournaments, YouTube content revenue. Games stay free forever.

### Why Open Source
The engine should be forkable. NPC Race but for boats? Fork it, build NPC Regatta. Transparency builds trust — players can read the physics, verify fairness, find and fix bugs.

### The Meta Game
The real game is learning to program through competition. A player who starts tweaking stat numbers will eventually write their first if-statement. Then state machines. Then optimization. Then they'll read someone else's car file and learn a pattern they didn't know.

The NPC Series is a stealth education platform disguised as a game series. We never say that out loud.

---

## Appendix: Future Game Ideas (Backlog)

### Ideas
- **NPC Farm** — Resource optimization. Upload a farmer AI. Manage plots, seasons, market prices.
- **NPC Poker** — Upload a poker bot. Texas hold'em. Bankroll competition over N hands.
- **NPC Rally** — Point-to-point on procedural terrain. Co-driver callouts as state input.
- **NPC Band** — Generative music. Upload a musician AI. Scored on harmony, rhythm, engagement.
- **NPC Courier** — Delivery optimization. Dynamic orders, traffic, fuel management.
