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
