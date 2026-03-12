# NPC Wars 🪿

Spectator battle royale where you write a Python function and watch your emoji fight.

## Quick Start

```bash
# Run a match
python3 run_match.py

# Watch the replay
# Open viewer/match.html in your browser
# Load results/match_001.json via the file picker
# OR open: viewer/match.html?match=../results/match_001.json
```

## Write a Bot

Copy `bots/template.py` → `bots/your_bot.py` and implement `decide(state)`.

```python
BOT_NAME = "YourBot"
BOT_EMOJI = "🦊"
BOT_BIO = "something cool"
BOT_AUTHOR = "you"

def decide(state):
    # state["me"] = {x, y, hp, energy, attack_power, defense}
    # state["enemies"] = [{name, emoji, x, y, hp}, ...]
    # state["round"], state["grid_size"], state["storm_border"]
    #
    # Return one of:
    #   ("move", "north"|"south"|"east"|"west")
    #   ("attack", "north"|"south"|"east"|"west")
    #   ("rest",)
    #   ("defend",)
    return ("move", "north")
```

## Seed Bots

| Emoji | Name | Strategy |
|-------|------|----------|
| 🪿 | GooseLoose | Balanced hunter — chases wounded, avoids storm |
| 🤖 | AggroBot | Pure aggression — chase and attack nonstop |
| 🛡️ | TankBot | Defend + counterattack — outlast everyone |
| 🎯 | KiteBot | Hit and run — maintain distance |
| 🎲 | ChaosBot | Pure random — chaos incarnate |

## How It Works

- All bots start at 100 HP, 100 energy
- Every action costs energy (move=5, attack=15, defend=10, rest=0)
- Storm closes in after round 20, forcing bots to center
- Last emoji alive wins

the goose is loose.
