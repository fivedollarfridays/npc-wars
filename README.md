# NPC Wars

Autonomous bot battle royale. Write a `decide(state)` function, drop it in a folder, watch emojis fight on a shrinking grid. Last one standing wins.

## Quick Start

```bash
pip install npc-wars
npcwars init
npcwars wizard
npcwars battle
```

That's it. Five minutes from install to your first fight.

## How It Works

1. **`npcwars init`** -- Creates a project with starter bots and config
2. **`npcwars wizard`** -- Interactive bot builder (name, emoji, play style, tuning)
3. **`npcwars validate bots/my_bot.py`** -- Checks your bot is safe and valid
4. **`npcwars battle`** -- Runs a match with all bots in `bots/`

## Write a Bot

```python
BOT_NAME = "MyBot"
BOT_EMOJI = "🔥"
BOT_BIO = "burns everything"
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

Or use the helpers DSL:

```python
from npcwars.helpers import Me, Enemies, Storm

def decide(state):
    me, enemies, storm = Me(state), Enemies(state), Storm(state)
    if storm.danger: return me.flee_storm()
    target = enemies.weakest()
    if target and me.dist_to(target) == 1: return me.attack(target)
    if target: return me.move_toward(target)
    return me.rest()
```

## Game Rules

- **Grid**: Bots spawn on an NxN grid
- **Storm**: Shrinks the safe zone after round 20 -- stay inside or take damage
- **Energy**: Every action costs energy. Run out and you're forced to rest
- **Actions**: `rest`, `defend`, `move`, `attack` (see [CONTRIBUTING.md](CONTRIBUTING.md) for costs)

## Battle Options

```bash
npcwars battle --seed 42           # Deterministic match
npcwars battle --bots-dir my_bots  # Custom bots directory
npcwars battle --replay replays    # Save match JSON
```

## Built-in Bots

| Bot | Style | Strategy |
|-----|-------|----------|
| AggroBot 🤖 | Aggro | Chase closest, attack relentlessly |
| TankBot 🛡️ | Tank | Defend, counter adjacent enemies |
| KiteBot 🪁 | Kiter | Keep distance, poke wounded |
| ChaosBot 🎲 | Chaos | Pure random mayhem |
| Cognify 🧠 | Vibes | Storm-aware opportunist (helpers DSL) |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Three paths: submit bots, pitch ideas, report bugs.

## License

MIT
