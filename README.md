<!--
  This repo (package: agent-grounds) is the home of the agentgrounds arcade engine.
  It ships TWO competitive-bot games: Kill Switch (battle royale, the original
  "NPC Wars") and Code Circuit (racing). NPC Race and NPC Fighter are separate
  repos that follow the same pattern. See "Place in the agentgrounds arcade" at the
  bottom for how this fits the Fractal Framework business.
-->

# Agent Grounds

Competitive bot arena platform. Write a `decide()` function, drop it in a folder, watch AI-generated sports broadcasts of your bots competing.

**Two games. Zero dependencies. Pure Python.**

## 3-Command Demo

```bash
pip install agent-grounds
agentgrounds killswitch init
agentgrounds killswitch play
```

That's it. You just ran a battle royale with commentary, highlights, and a replay you can watch in your browser.

## Games

### Kill Switch (Battle Royale)

Bots fight on a grid. D20 combat, stat builds, equipment loadouts, shrinking storm. Last bot standing wins.

```bash
agentgrounds killswitch init        # Starter bots + arena
agentgrounds killswitch play        # Watch a match with TV broadcast
agentgrounds killswitch play --seed 42  # Deterministic replay
```

### Code Circuit (Racing)

Cars race on an oval track. Overtakes, pit strategy, tire management, safety cars.

```bash
agentgrounds circuit race           # Run a race
agentgrounds circuit race --laps 15 # Custom lap count
```

## What You Get

Every match produces a full sports broadcast:

- **Commentary** — play-by-play and color commentary with drama-tier tone scaling
- **Highlights** — auto-extracted clips from key moments
- **Personality profiles** — bots develop traits from their behavior across matches
- **Rivalries** — tracked across matches with narrative hooks
- **Ghost replays** — "what if?" alternate timelines (Kill Switch)
- **Episodes** — cold opens, intros, match commentary, post-match analysis
- **Browser viewer** — replay any match with visualizations, overlays, and audio

## Build a Bot (Kill Switch)

### With AI

```bash
agentgrounds killswitch generate --strategy "aggressive kiter"
# Paste into Claude/GPT -> save as bots/my_bot.py
```

### From Scratch

```python
BOT_NAME = "Scrappy"
BOT_EMOJI = "🥊"
BOT_BIO = "Hits the closest thing"

def decide(state):
    from agentgrounds.wars.helpers import Me, Enemies
    me = Me(state)
    foes = Enemies(state)
    if me.energy < 15: return me.rest()
    target = foes.closest()
    if target and me.dist_to(target) == 1: return me.attack(target)
    if target: return me.move_toward(target)
    return me.rest()
```

### Learn by Tweaking

```bash
agentgrounds killswitch init   # Creates bots/starter.py with guided TODOs
# Open starter.py, follow the TODOs, run `play` after each change
```

### Diagnose a Bot

`doctor` runs your bot against the shipped pool for N seeded matches and prints a
diagnostic report aimed at bot authors. For each run and aggregated, it reports:

- **locked-action attempts** — actions your bot tried that it hasn't unlocked yet
  (e.g. `trap`, `use_ability`). These silently degrade to a rest in-match, so
  `doctor` is how you find them.
- **plague rounds** — rounds your bot spent passive/idle and accrued plague damage.
- **forced-rest rounds** — rounds where your bot ran out of energy and was forced
  to rest (it couldn't afford any action).
- **storm damage / storm deaths** — damage taken inside the storm and whether the
  storm killed you.
- **placement** — where your bot finished each match.

```bash
agentgrounds killswitch doctor bots/my_bot.py --matches 10 --seed 1
agentgrounds killswitch doctor bots/my_bot.py --pool-dir bots   # vs your own pool
```

The command **exits non-zero** when your bot disconnects (crashes) or attempts any
locked action, so you can drop it straight into CI:

```bash
agentgrounds killswitch doctor bots/my_bot.py --matches 20 || echo "bot has issues"
```

## Game Features (Kill Switch)

- D20 combat with crits, dodge, initiative
- 4-stat allocation (POWER / SPEED / ARMOR / MIND)
- 23 equipment items across 4 slots (40-credit budget)
- 5 terrain maps with walls, water, high ground, cover
- Momentum system with King of the Hill
- Traps, abilities, tactical items
- XP progression across 30 levels
- Shrinking storm zone forces fights
- Adaptive Watcher boss that reads your patterns

## How It Works (Architecture)

```
agentgrounds/
├── __main__.py          # CLI dispatcher (killswitch | circuit)
├── wars/                # Kill Switch game
│   ├── cli/             # Commands (init, play, generate, watch, sim, ...)
│   ├── builtin_bots/    # 7 example bots
│   └── helpers.py       # Me, Enemies, Storm convenience API
├── circuit/             # Code Circuit game
│   └── cli/             # Commands (race)
engine/                  # Game engines + TV pipeline
├── game.py              # Kill Switch match engine
├── circuit.py           # Code Circuit race engine
├── tv_pipeline.py       # Post-match TV enrichment
├── commentary.py        # Kill Switch commentary
├── circuit_commentary.py # Code Circuit commentary
├── personality.py       # Bot personality profiling
├── rivalry.py           # Rivalry tracking
├── highlights.py        # Highlight extraction
├── episode.py           # Episode generator
├── ghost_replay.py      # What-if alternate timelines
└── decision_trace.py    # Bot decision tracing
viewer/                  # Browser-based match viewer
├── viewer.html          # Unified entry point
└── js/                  # Game-aware renderers + controls
```

**Engine**: Pure Python, zero dependencies. Deterministic via seeded RNG.

**TV Pipeline**: After each match, `tv_pipeline.py` enriches the JSON with commentary, highlights, profiles, rivalries, and episode structure.

**Viewer**: Static HTML/JS. Load a match JSON, get play/pause/speed controls, commentary ticker, code overlay, and game-specific visualizations.

## All Commands

```bash
# Kill Switch
agentgrounds killswitch init                    # Set up arena with starter bots
agentgrounds killswitch play                    # Run and watch a match
agentgrounds killswitch play --seed 42          # Deterministic match
agentgrounds killswitch play --no-watch         # Skip playback, print results
agentgrounds killswitch play --no-tv            # Skip TV generation
agentgrounds killswitch generate --strategy "." # Build AI prompt for bot creation
agentgrounds killswitch wizard                  # Interactive bot builder
agentgrounds killswitch validate bots/my.py     # Check bot is valid
agentgrounds killswitch doctor bots/my.py        # Diagnose a bot (CI-friendly)
agentgrounds killswitch battle --replay dir     # Batch run, save replays
agentgrounds killswitch sim --matches 100       # Batch simulation
agentgrounds killswitch watch match.json        # Replay a match
agentgrounds killswitch watch-web               # Browser replay viewer

# Code Circuit
agentgrounds circuit race                       # Run a race
agentgrounds circuit race --laps 15 --seed 7    # Custom race

# Platform
agentgrounds --version                          # Show version
```

## Getting Started

See the [Getting Started guide](docs/getting-started.md) for a complete walkthrough from install to watching your first episode.

## Links

- Full game rules: [PROMPT.md](PROMPT.md) (Kill Switch)
- Contributing: [CONTRIBUTING.md](CONTRIBUTING.md)
- Getting Started: [docs/getting-started.md](docs/getting-started.md)

## License

[MIT](LICENSE)

## Place in the agentgrounds arcade

NPC Wars / Kill Switch is a **competitive-bot product in the agentgrounds arcade** — the
arm of the Fractal Framework business that builds a community of agentic builders. The
loop: developers write a `decide()` bot, drop it in a folder, and watch AI-narrated
broadcasts of their bots competing. Matches, replays, and broadcasts are the shareable
artifacts that draw developers in and funnel them toward the wider Fractal Framework
method-and-tooling business.

- **Bot API** — you write one Python function, `decide(state)`, returning an action
  (`attack`, `move_toward`, `rest`, etc.). The `agentgrounds.wars.helpers` module (`Me`,
  `Enemies`, `Storm`) gives ergonomic accessors. See [`bots/template.py`](bots/template.py)
  and the built-in bots under [`agentgrounds/wars/builtin_bots/`](agentgrounds/wars/builtin_bots/).
- **Output** — every match writes a match JSON (the replay) under `results/`, enriched by
  the TV pipeline (`engine/tv_pipeline.py`) with commentary, highlights, personality
  profiles, rivalries, and episode structure. The browser viewer (`viewer/`) plays it back.
- **Sibling games** — `npc-race` (Code Circuit racing, separate repo) and `npc-fighter`
  (fighting game, spec-stage) follow the same code-a-bot / run-the-match / watch-the-replay
  pattern. This repo also bundles Code Circuit directly (`agentgrounds circuit race`).
- **Ecosystem** — the games are intended to run on the shared **npc-sandbox** secure
  runtime and to be rendered cinematically by **borst** (→ Unreal) and to dev-content by
  **Iris / 2MP4**. Those integrations live in sibling repos, not in this one.

> Note: this package publishes as `agent-grounds` (see `pyproject.toml`), and the CLI is
> `agentgrounds <game> ...`. The legacy `npc-wars` repo name and the `killswitch` / `wars`
> CLI aliases all refer to the same battle-royale game.
