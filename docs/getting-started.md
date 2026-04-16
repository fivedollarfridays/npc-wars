# Getting Started with Agent Grounds

Go from zero to watching your first match in under 60 seconds.

## Install

```bash
pip install agent-grounds
```

Requires Python 3.13+. Zero external dependencies.

## Kill Switch: Your First Match

### 1. Initialize

```bash
agentgrounds killswitch init
```

This creates a `bots/` directory with starter bots and a `config.yaml`.

### 2. Play

```bash
agentgrounds killswitch play
```

Watch your first battle royale. Bots fight on a 10x10 grid with D20 combat, equipment, and a shrinking storm. The match generates a full TV broadcast with commentary, highlights, and personality profiles.

### 3. Watch the Replay

After a match, you get a JSON file in `results/`. Open it in the browser viewer:

```bash
agentgrounds killswitch watch-web
```

This launches a local viewer with play/pause controls, commentary ticker, and game visualizations.

## Code Circuit: Your First Race

```bash
agentgrounds circuit race
```

Cars race on an oval track with overtakes, pit stops, and safety cars. Commentary and highlights are generated automatically.

```bash
agentgrounds circuit race --laps 15 --seed 42
```

## Build Your First Bot

### Option A: AI-Assisted

```bash
agentgrounds killswitch generate --strategy "defensive tank that turtles"
```

This outputs a prompt with full game rules. Paste it into Claude, GPT, or any LLM — they'll write a tournament-ready bot.

### Option B: Learn by Tweaking

Open `bots/starter.py` (created by `init`). It has guided TODOs:

1. Read the first TODO
2. Make a small change
3. Run `agentgrounds killswitch play`
4. See the difference
5. Repeat

### Option C: From Scratch

Create a file in `bots/`:

```python
BOT_NAME = "MyBot"
BOT_EMOJI = "🔥"
BOT_BIO = "Burns everything"
BOT_AUTHOR = "you"

def decide(state):
    me = state["me"]
    enemies = state["enemies"]
    if not enemies:
        return ("rest",)
    target = min(enemies, key=lambda e: abs(e["x"] - me["x"]) + abs(e["y"] - me["y"]))
    if abs(target["x"] - me["x"]) + abs(target["y"] - me["y"]) == 1:
        dx = target["x"] - me["x"]
        if dx == 1: return ("attack", "east")
        if dx == -1: return ("attack", "west")
        dy = target["y"] - me["y"]
        if dy == 1: return ("attack", "south")
        return ("attack", "north")
    return ("move", "east" if target["x"] > me["x"] else "west")
```

Validate it:

```bash
agentgrounds killswitch validate bots/my_bot.py
```

## Watch an Episode

After playing a match with TV enabled (the default), the match JSON contains everything needed for a broadcast episode:

- **Cold open** — rivalry recaps ("Previously on Agent Grounds...")
- **Pre-match** — participant intro cards with personality profiles
- **Match commentary** — play-by-play and color commentary
- **Post-match** — stat diffs, highlights, standings

The browser viewer renders all of this. Open the match JSON in `watch-web` and use the playback controls.

## Batch Simulation

Run many matches to see how bots perform over time:

```bash
agentgrounds killswitch sim --matches 100 --output sim_results/
agentgrounds killswitch analyze --input sim_results/
```

## What's in a Match JSON?

After TV enrichment, each match JSON contains:

| Key | Contents |
|-----|----------|
| `rounds` | Per-round game state (positions, HP, actions) |
| `results` | Final standings, kills, scores |
| `commentary` | Timestamped commentary lines with tone |
| `highlights` | Auto-extracted key moments |
| `profiles` | Bot personality traits built from behavior |
| `rivalries` | Pairwise rivalry scores and narrative hooks |
| `episode` | Full episode structure (cold open, intros, post-match) |

## Next Steps

- Read [PROMPT.md](../PROMPT.md) for full Kill Switch game rules
- Check out `bots/` for example strategies
- Run `agentgrounds killswitch generate` to create AI-written bots
- See [CONTRIBUTING.md](../CONTRIBUTING.md) for how to contribute
