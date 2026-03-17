# NPC Series — God Doc

> "You don't play. You code."

The definitive reference for the NPC Series: a collection of coding games where players write Python bots that compete in simulated domains. Every game follows the same architecture but tests different real-world expertise.

---

## The Formula

Every NPC game:

```
1. Player writes a Python file with decide(state) → action
2. Engine simulates the competition deterministically
3. Viewer replays the result with spectacle effects
4. AI agents can generate competitive bots from a prompt
```

The player skill is **two-dimensional**:
- **Technical:** Write or prompt code that works (Python, or prompting Claude/Gemini/GPT)
- **Domain:** Understand the real-world system being simulated (combat, racing, cooking, etc.)

---

## Games

### Launched

| Game | Domain | State | Actions | The Skill |
|------|--------|-------|---------|-----------|
| **NPC Wars** | Battle royale | position, HP, energy, enemies, storm | move, attack, defend, rest | Game theory: energy management, defend-counter, storm prediction, pattern denial |

### Announced

| Game | Domain | Key State Fields | Key Actions | The Real-World Knowledge |
|------|--------|-----------------|-------------|-------------------------|
| **NPC Race** | F1 racing | speed, tire_wear, fuel, weather, track_position, drs_zone | accelerate, brake, steer, pit_stop, use_drs | Tire compound strategy, weather gambles, undercut timing, fuel saving, slipstream physics |
| **NPC Fighter** | 1v1 fighting | hp, stamina, stance, distance, combo_meter | punch, kick, block, dodge, special | Frame data, hitbox priority, stamina economy, read-and-react patterns |
| **NPC Kitchen** | Fine dining | stations, orders, ingredients, timers, temperature | chop, sear, bake, plate, rest, prep | Maillard reactions, flavor chemistry, parallel cooking coordination, plating timing |
| **NPC Colony** | Ant colony | workers, resources, threats, territory, pheromones | forage, build, defend, scout, breed | Swarm intelligence, resource allocation, expansion vs defense tradeoffs |
| **NPC Heist** | Crew heist | roles, alarms, guards, loot, escape_routes | move, hack, lockpick, distract, grab | Stealth mechanics, role specialization, timing windows, escape optimization |
| **NPC Fleet** | Naval combat | ships, wind, ammunition, formation, morale | sail, fire, board, retreat, signal | Wind advantage, formation tactics, ammunition conservation, morale management |
| **NPC Pitch** | Startup pitch | slides, audience_mood, time_remaining, questions | present, demo, pivot, answer, close | Storytelling arc, audience psychology, objection handling, demo timing |
| **NPC Dungeon** | Dungeon crawl | party, rooms, monsters, loot, torch_light | move, fight, rest, loot, flee | Party composition, resource conservation, risk-reward on rooms, torch management |

---

## Architecture (Shared Across All Games)

### The Contract

Every game implements this interface:

```python
# Bot file format (player-authored)
BOT_NAME = "MyBot"        # display name
BOT_EMOJI = "🤖"          # grid/track identifier
BOT_BIO = "description"   # flavor text

def decide(state: dict) -> tuple:
    """Called every tick. Return an action tuple."""
    return ("rest",)
```

The `state` dict and valid action tuples are game-specific. Everything else is shared.

### Shared Infrastructure (~70% of each repo)

| Component | Description | Shared? |
|-----------|-------------|---------|
| **CLI skeleton** | `npc{game} init/validate/play/watch/generate` | Yes — same commands, different nouns |
| **Security scanner** | AST allowlist (math, random, collections, itertools, functools) | Yes — identical |
| **Docker sandbox** | Ephemeral container, no network, resource limits | Yes — identical |
| **ANSI renderer** | Terminal grid/track/kitchen with emoji, HP/fuel/timer bars | Framework shared, layout game-specific |
| **HTML viewer** | Canvas-based replay with spectacle effects | Framework shared, visuals game-specific |
| **Replay format** | `{ticks: [{positions, events, ...}]}` | Structure shared, fields game-specific |
| **PROMPT.md** | AI agent prompt (rules + state + strategies + examples) | Template shared, content game-specific |
| **Starter bot** | Priority ladder with commented TODOs | Pattern shared, decisions game-specific |
| **`generate` command** | AI-assisted bot creation (print prompt or call API) | Yes — identical flow |
| **Helpers DSL** | Convenience wrappers for the state dict | Pattern shared, classes game-specific |
| **Match modes** | Standard vs extended game configurations | Pattern shared, constants game-specific |
| **Diff view** | Post-match stat comparison overlay | Yes — identical |
| **Server layer** | FastAPI + Redis queue + lobby + fill bots | Yes — identical, fill bot strategies differ |
| **Rate limiting** | Session-based submission throttling | Yes — identical |
| **Player registry** | SQLite CRUD | Yes — identical |

### Game-Specific (~30% of each repo)

| Component | Why It's Unique |
|-----------|-----------------|
| **State dict** | Each domain has completely different observable state |
| **Action set** | Each domain has different valid actions with different costs |
| **Physics engine** | The simulation model IS the game (bump physics vs tire degradation vs heat transfer) |
| **Constants** | HP/energy vs tire compounds/fuel vs cook times/temperatures |
| **Helpers DSL classes** | `Me/Enemies/Storm` vs `Car/Track/Weather` vs `Chef/Kitchen/Orders` |
| **PROMPT.md content** | Domain knowledge is the moat — F1 tire strategy, Maillard reactions, etc. |
| **Winning strategies** | Emerge from the physics, completely different per game |
| **Spectacle effects** | Thematic to the domain (explosions vs tire smoke vs fire/steam) |
| **Built-in bots** | Demonstrate domain strategies, not generic patterns |

---

## The Three Player Tracks

Every NPC game supports three ways to play:

### 1. Agent Arena (prompting)

```bash
npc{game} generate --strategy "aggressive tire conservation" | pbcopy
# Paste into Claude/Gemini/GPT → get bot → save to bots/
npc{game} play --seed 42
```

The PROMPT.md is the product. It contains enough domain knowledge that an AI can write a competitive bot. The player's skill is crafting the strategy description, not writing code.

**This is the spectator sport.** "My Claude F1 driver vs your Gemini chef" is inherently shareable.

### 2. Learn to Code (education)

```bash
npc{game} init
# Open bots/starter.py
# Read the TODOs, change a number, see what happens
npc{game} play --seed 42
```

Each starter bot is a working priority ladder with comments explaining what each decision does and suggesting alternatives to try. The feedback loop is instant.

### 3. CLI Game (the DOS experience)

```bash
npc{game} play
```

One command. ANSI grid renders in the terminal. Watch your bot fight/race/cook in real time. No browser, no server, just the terminal.

---

## Build Order

### Phase 1: NPC Wars (DONE → shipping experience layer)
- ✅ Core engine (18 sprints, 2170 tests)
- 🔧 S20: Experience layer (renderer, play, watch, generate, PROMPT.md, starter bot)
- 📦 S19: PyPI release

### Phase 2: NPC Racing
- Copy Wars' experience layer infrastructure (CLI, renderer framework, scanner, sandbox, generate)
- Build racing-specific engine (tire degradation, weather, pit strategy)
- Write racing PROMPT.md with real F1 domain knowledge
- Write racing starter bot with racing-specific TODOs
- Ship to PyPI as `npc-race`

### Phase 3: Extract npc-sdk
- Compare Wars and Racing implementations
- Extract shared CLI framework, scanner, sandbox, renderer engine, generate command
- Both games depend on `npc-sdk` going forward
- Each new game: `pip install npc-sdk` + write the 30% domain-specific code

### Phase 4: Remaining Games
- Each game is ~30% new code on top of npc-sdk
- The PROMPT.md (domain knowledge) is the biggest per-game effort
- Launch all announced titles for series volume

---

## Security Model

**Allowlist, not blocklist.** Every game uses the same scanner:

```python
ALLOWED_IMPORTS = {"math", "random", "collections", "itertools", "functools"}
# Plus the game's own helpers module (npcwars.helpers, npcrace.helpers, etc.)
```

Everything else is rejected at scan time. Combined with:
- Restricted `__builtins__` at exec time
- Docker sandbox with `--network=none --memory=256m --cpus=1 --pids-limit=50 --read-only`
- 10-second hard timeout
- Stat budget validation (no infinite HP bots)

---

## Technical Principles

1. **Python stdlib only for engines** — no numpy, no pandas, no ML libs in the simulation
2. **Single HTML viewer** — one file, no build step, loads from JSON
3. **Replay-based** — all visualization is post-hoc from deterministic match data
4. **Deterministic** — seeded RNG, reproducible matches for debugging
5. **Sandboxed execution** — user code never touches the network or filesystem
6. **No premature abstraction** — copy first, extract after two working implementations

---

## Key Metrics

| Metric | Target |
|--------|--------|
| Time to first match | < 60 seconds (`pip install` + `init` + `play`) |
| Time to first custom bot | < 5 minutes (paste PROMPT.md into AI, save result) |
| Time to understanding | < 10 minutes (starter bot TODOs explain the game) |
| Bot validation time | < 1 second |
| Match execution time | < 5 seconds |
| CLI playback | Real-time at 1x, instant at 4x |
