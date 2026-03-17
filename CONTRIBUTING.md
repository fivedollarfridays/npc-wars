# Contributing to NPC Wars

> **You don't PR game logic. You build bots and pitch ideas.**
>
> The engine is maintained by one person. This keeps the game balanced, the meta intentional, and the codebase stable.

## Three Ways to Contribute

### 1. Bot Showcase

Submit your bot to `showcase/` via PR.

```bash
# Build a bot with AI
npcwars generate --strategy "your idea" | pbcopy
# Paste into Claude, Gemini, or GPT — save response as bots/your_bot.py

# Or use the interactive wizard
npcwars wizard

# Validate and submit
npcwars validate bots/your_bot.py
cp bots/your_bot.py showcase/
# Open a PR
```

The `npcwars generate` command creates a full prompt from [PROMPT.md](PROMPT.md) with game rules, state API, and strategy tips -- so any LLM can write a competitive bot.

Must pass `npcwars validate`. Gets merged as-is -- this is a community gallery.

### 2. Suggestions

Want to improve the game? Submit a suggestion:

1. Copy `suggestions/TEMPLATE.md` to `suggestions/your-idea.md`
2. Fill it out
3. Open a PR to `suggestions/`

Suggestions are reviewed in batches. Accepted ideas move to `suggestions/accepted/`.

### 3. Bug Reports

Found a bug? Open an issue with:
- What happened
- What you expected
- Steps to reproduce

## Bot Rules

| Rule | Detail |
|------|--------|
| Unique emoji | No two bots share an emoji |
| No I/O | No file reads, network, or writes |
| 1-second limit | `decide()` must return within 1 second |
| Valid action | `("rest",)` `("defend",)` `("move", dir)` `("attack", dir)` |
| Max 3 emojis | Each author may claim up to 3 identifiers |

## The `state` Dict

```python
{
    "me": {
        "x": int, "y": int, "hp": int, "energy": int,
        "attack_power": int, "defense": int,
    },
    "enemies": [{"name": str, "emoji": str, "x": int, "y": int, "hp": int}],
    "round": int,
    "grid_size": int,
    "storm_border": int,
}
```

## Energy Costs

| Action | Cost |
|--------|------|
| `rest` | 0 (+10 HP, +20 energy) |
| `defend` | 10 |
| `move` | 5 |
| `attack` | 15 |
