# Contributing to Agent Grounds

> **You don't PR game logic. You build bots and pitch ideas.**
>
> The engine is maintained by one person. This keeps the game balanced, the meta intentional, and the codebase stable.

## Ways to Contribute

### 1. Bot Showcase

Submit your bot to `showcase/` via PR.

```bash
# Build a bot with AI
agentgrounds killswitch generate --strategy "your idea" | pbcopy
# Paste into Claude, Gemini, or GPT — save response as bots/your_bot.py

# Or use the interactive wizard
agentgrounds killswitch wizard

# Validate and submit
agentgrounds killswitch validate bots/your_bot.py
cp bots/your_bot.py showcase/
# Open a PR
```

The `agentgrounds killswitch generate` command creates a full prompt from [PROMPT.md](PROMPT.md) with game rules, state API, and strategy tips — so any LLM can write a competitive bot.

Must pass `agentgrounds killswitch validate`. Gets merged as-is — this is a community gallery.

### 2. Commentary Templates

The commentary system uses template strings that get filled with match context. You can add templates to make broadcasts more varied.

**Kill Switch commentary** lives in `engine/commentary.py`. Templates are organized by event type and drama tier:

```python
# Example: adding a kill commentary template
# In engine/commentary.py, find the kill templates dict and add:
"calm": [
    "{killer} eliminates {victim} with a clean strike.",
    # Add yours here
],
"hype": [
    "{killer} DESTROYS {victim}! The crowd goes wild!",
    # Add yours here
],
```

**Code Circuit commentary** lives in `engine/circuit_commentary.py` and `engine/commentary_templates.py`. Templates cover overtakes, pit stops, safety cars, weather changes, and more.

**How to add templates:**

1. Find the template file for the game (`commentary.py` or `commentary_templates.py`)
2. Locate the event type you want to enrich (kill, overtake, spin, etc.)
3. Add new template strings using the same `{placeholder}` format
4. Templates are picked randomly — more templates = more variety
5. Run `python -m pytest tests/` to make sure nothing broke
6. Open a PR to `engine/`

### 3. Spectacle Effects

The spectacle system adds visual effects to dramatic moments in the browser viewer.

**Kill Switch effects** are driven by `engine/spectacle.py` which scores drama per round. The viewer in `viewer/js/` renders effects based on drama tier:

| Drama Tier | Effect |
|-----------|--------|
| calm | Normal rendering |
| heating | Subtle screen shake |
| intense | Color pulse, speed change |
| hype | Full screen effects, kill cam |
| chaos | Maximum visual intensity |

**To add a new effect:**

1. Add the effect logic to the appropriate `viewer/js/` module
2. Wire it to a drama tier or event type
3. Test in the browser viewer with a match JSON
4. Open a PR with a screenshot or recording

### 4. Add a New Game

Agent Grounds is a platform — Kill Switch and Code Circuit are the first two games. The architecture supports adding more.

**What a new game needs:**

1. **Engine** (`engine/your_game.py`) — pure Python, deterministic, produces match JSON with rounds and results
2. **CLI** (`agentgrounds/your_game/cli/`) — at minimum: a command to run a match
3. **TV enrichment** (`engine/your_game_tv.py`) — add commentary, highlights, profiles using the platform contracts
4. **Platform contracts** — use `engine/platform_events.py` GameEvent and `engine/platform_commentary.py` CommentaryLine so your game works with the existing episode generator and viewer

**Platform contracts your game should implement:**

```python
# Events — adapt your game events to GameEvent
from engine.platform_events import GameEvent

# Commentary — produce CommentaryLine objects
from engine.platform_commentary import CommentaryLine
```

5. **Register in dispatcher** — add your game to `agentgrounds/__main__.py`:

```python
GAMES = {
    "killswitch": "agentgrounds.wars.cli",
    "circuit": "agentgrounds.circuit.cli",
    "yourgame": "agentgrounds.yourgame.cli",
}
```

6. **Tests** — TDD. Write tests before implementation
7. **PROMPT.md** — if your game has player-authored bots, write a bot builder prompt

**Start with a proposal:** open an issue or submit to `suggestions/` describing the game concept, player interaction model, and how it fits the platform.

### 5. Suggestions

Want to improve the game? Submit a suggestion:

1. Copy `suggestions/TEMPLATE.md` to `suggestions/your-idea.md`
2. Fill it out
3. Open a PR to `suggestions/`

Suggestions are reviewed in batches. Accepted ideas move to `suggestions/accepted/`.

### 6. Bug Reports

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
        "power": int, "speed": int, "armor": int, "mind": int,
        "equipment": {...}, "hit_chance_vs": {...},
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
| `rest` | 0 (+5 HP, +20 energy) |
| `defend` | 10 |
| `move` | 5 |
| `attack` | 10 |
| `dash` | 15 |
| `ranged_attack` | 10 |
| `taunt` | 5 |
| `trap` | 15 |
