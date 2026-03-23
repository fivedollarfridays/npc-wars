# Agent Grounds -- Wars

Autonomous bot battle royale. Write a `decide(state)` function, drop it in a folder, watch bots fight.

## Install

```bash
pip install agent-grounds
```

## Play

```bash
agentgrounds wars init        # Set up arena with starter bots
agentgrounds wars play        # Watch your first match
```

## Build a Bot with AI

```bash
agentgrounds wars generate --strategy "aggressive kiter" | pbcopy
# Paste into Claude/GPT -> save response as bots/my_bot.py
agentgrounds wars play
```

The `generate` command builds a complete prompt from the game rules so the AI writes tournament-ready code.

## Learn by Tweaking

Open `bots/starter.py` -- it has guided TODOs that teach game mechanics:

1. Open the file (created by `agentgrounds wars init`)
2. Read the TODOs -- each one teaches a mechanic
3. Make a small change, run `agentgrounds wars play`, see the difference

## Write from Scratch

```python
BOT_NAME = "MyBot"
BOT_EMOJI = "X"
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

## Game Features

- D20 combat with crits, dodge, initiative
- 4-stat allocation (POWER / SPEED / ARMOR / MIND)
- 23 equipment items across 4 slots
- 5 terrain maps with walls, water, high ground
- Traps, abilities, tactical items
- XP progression across 30 levels
- Post-match stat diff vs lifetime average
- Shrinking storm zone forces fights

## Commands

```bash
agentgrounds wars init                    # Set up project with starter bots
agentgrounds wars play                    # Run and watch a match
agentgrounds wars play --seed 42          # Deterministic match
agentgrounds wars play --no-watch         # Skip playback, print results
agentgrounds wars generate --strategy "..." # Build AI prompt for bot creation
agentgrounds wars wizard                  # Interactive bot builder
agentgrounds wars validate bots/my.py     # Check bot is valid
agentgrounds wars battle --replay dir     # Batch run, save JSON replays
```

## Links

- Full game rules: [PROMPT.md](PROMPT.md)
- Contributing: [CONTRIBUTING.md](CONTRIBUTING.md)

## License

MIT
