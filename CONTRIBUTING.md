# Contributing a Bot

Welcome! Here's how to submit your NPC Wars bot.

## Quick Start

1. **Copy the template**
   ```bash
   cp bots/template.py bots/your_bot_name.py
   ```

2. **Edit your bot** — set `BOT_NAME`, `BOT_EMOJI`, `BOT_AUTHOR`, and implement `decide(state)`

3. **Validate locally**
   ```bash
   python scripts/validate_bot.py bots/your_bot_name.py
   ```

4. **Open a PR** using the **Bot Submission** template

## Rules

| Rule | Detail |
|------|--------|
| Unique emoji | No two bots may share an emoji — it's your identifier in-game |
| No I/O | Bots must not read files, make network requests, or write anywhere |
| 1-second limit | `decide()` must return within 1 second per round |
| Valid action | Must return one of: `("rest",)` `("defend",)` `("move", dir)` `("attack", dir)` |
| Max 3 emojis | Each author may claim up to 3 emoji identifiers |

Where `dir` is one of: `"north"`, `"south"`, `"east"`, `"west"`

## The `state` Dict

Your `decide(state)` receives:

```python
{
    "me": {
        "x": int,        # your column (0 = left)
        "y": int,        # your row (0 = top)
        "hp": int,       # current HP (0–100)
        "energy": int,   # current energy (0–100)
        "attack_power": int,
        "defense": int,
    },
    "enemies": [
        {"name": str, "emoji": str, "x": int, "y": int, "hp": int},
        # ... one entry per living enemy
    ],
    "round": int,          # current round number
    "grid_size": int,      # grid is grid_size × grid_size
    "storm_border": int,   # tiles from edge consumed by storm (0 = no storm)
}
```

## Energy Costs

| Action | Cost |
|--------|------|
| `rest` | 0 (also heals +10 HP, +20 energy) |
| `defend` | 10 |
| `move` | 5 |
| `attack` | 15 |

If energy drops below 5, your bot is forced to rest that round.

## CI Checks

Every PR touching `bots/` automatically runs `scripts/validate_bot.py` on your
changed files. The PR cannot merge until validation passes.
