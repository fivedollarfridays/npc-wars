# Kill Switch — Complete Game Description

> **Platform:** Agent Grounds | **Genre:** Bot-coded battle royale | **Tagline:** "You don't play. You code."

---

## What Is Kill Switch?

Kill Switch is a competitive programming game where players write Python bots that fight in a battle royale on a grid. You write a `decide(state)` function. Your bot reads the battlefield, picks an action, and fights autonomously. Last bot standing wins. You never touch the controls — your code is the player.

The game runs locally via CLI (`agentgrounds wars play`), renders in terminal or browser, and supports online matchmaking via a FastAPI server with lobby, tournaments, and leaderboards.

---

## The Bot

A bot is a single Python file:

```python
BOT_NAME = "MyBot"
BOT_EMOJI = "⚔️"
BOT_BIO = "A balanced fighter"

BOT_POWER = 30    # Damage output
BOT_SPEED = 25    # Dodge, initiative, accuracy
BOT_ARMOR = 25    # HP and damage reduction
BOT_MIND = 20     # Energy pool and regen

BOT_EQUIPMENT = {
    "weapon": "sword",
    "armor": "leather",
    "accessories": ["ring_of_health"],
    "tactical": "battle_cry",
}

def decide(state):
    me = state["me"]
    enemies = state["enemies"]

    if me["hp"] < 30:
        return ("rest",)
    if enemies:
        closest = min(enemies, key=lambda e: abs(e["x"] - me["x"]) + abs(e["y"] - me["y"]))
        if abs(closest["x"] - me["x"]) + abs(closest["y"] - me["y"]) == 1:
            return ("attack", closest["emoji"])
        dx = closest["x"] - me["x"]
        return ("move", "east" if dx > 0 else "west")
    return ("rest",)
```

That's a complete, playable bot. Run `agentgrounds wars play` and watch it fight.

---

## Core Mechanics

### Actions (8 total, unlocked by level)

| Action | Energy | Effect | Level |
|--------|--------|--------|-------|
| Rest | 0 | +5 HP, +20 energy | 1 |
| Move | 5 | 1 tile in cardinal direction | 1 |
| Attack | 10 | Melee hit on adjacent enemy | 1 |
| Defend | 10 | Halve incoming damage this round | 1 |
| Ranged Attack | 20 | Hit at distance, reduced accuracy/damage | 3 |
| Dash | 15 | Move 2 tiles at once | 5 |
| Taunt | 10 | Force enemy to attack you | 8 |
| Trap | 15 | Place invisible trap tile | 12 |

### Combat: D20 Roll System

Every attack rolls a d20:
- **To-hit:** d20 + (SPEED / 10) ≥ target AC
- **AC:** 8 base + armor DR + 6 if defending
- **Critical:** Natural 20 = base damage × crit multiplier
- **Dodge:** After a hit, defender rolls dodge chance (up to 20%) for half damage
- **Modifiers:** +3 vs resting targets, -3 when taunted (attacking non-taunter)

Damage scales with POWER stat and weapon bonuses. Armor DR subtracts flat damage.

### Stats: 100-Point Budget

Four stats, must sum to 100 (min 5, max 80 each):

| Stat | Governs |
|------|---------|
| **POWER** | Damage range, crit multiplier |
| **SPEED** | Dodge chance, initiative (attack order), to-hit bonus |
| **ARMOR** | Max HP (50 + 0.8×ARMOR), damage reduction |
| **MIND** | Max energy (80 + 0.8×MIND), energy regen |

Balanced builds (25/25/25/25) get a +75 HP versatility bonus. Skewed builds get archetype classification: Bruiser (POWER), Assassin (SPEED), Tank (ARMOR), Controller (MIND).

### Equipment: 40-Credit Budget

| Slot | Options |
|------|---------|
| **Weapon** (required) | Dagger, Sword, Axe, Mace (armor-piercing), Bow, Spear (reach 2) |
| **Armor** (required) | Leather, Chain Mail, Plate, Reinforced, Crystal |
| **Accessories** (0-2) | Ring of Health, Ring of Haste, Amulet of Crit, Charm of Evasion, Pendant of Mind, Cloak of Shadows, Boots of Speed, Compass |
| **Tactical** (0-1) | Battle Cry (1.5× damage burst), Fortify (temp DR + HP), Teleport (instant move) |

### Terrain: 5 Maps

| Map | Feature |
|-----|---------|
| Arena | Open — pure combat |
| Fortress | Central walls with corridors |
| Highlands | High ground tiles (+2 hit, +15% damage) |
| Maze | Complex wall patterns |
| Storm Pit | Open, fast storm |

Tile types: Open, Wall (blocks movement + ranged LoS), Water (+5 energy cost, -2 hit), High Ground, Cover (+3 AC), Crystal (+10 energy on first step).

### Storm

The playfield shrinks over time:
- Rounds 1-9: No storm
- Round 10+: Border closes inward
- Storm damage: 10 HP/round
- Forces bots to fight, prevents camping

---

## Depth Systems

### Momentum & Scoring

Bots earn points each round (kills, damage, survival). Points unlock momentum tiers:

| Tier | Name | Threshold | Bonus |
|------|------|-----------|-------|
| 1 | Momentum | 10 | +5 energy/round |
| 2 | Battle Fury | 25 | +10% damage |
| 3 | Crowd Favorite | 40 | Visual aura |
| 4 | Unstoppable | 60 | -15% incoming damage |

**One-Leader Rule:** Only the top scorer reaches tier 3+. Killing the leader gives +20 bonus points. Leaders pay an energy drain per round.

### Traps

Level 12+ bots can place invisible traps:
- 20 base damage (scales with POWER)
- 3-round cooldown, 10-round lifetime
- Invisible until triggered by enemy stepping on tile
- Strategic area denial

### Custom Abilities

Level 18+ bots define a custom ability via `power_up()` callback:
- Types: damage, heal, shield, slow
- Player-defined potency, range, cooldown, energy cost
- Enables unique playstyles

### Callbacks

| Callback | Level | Purpose |
|----------|-------|---------|
| `setup(state)` | 8 | Pre-match initialization |
| `on_kill(state, victim)` | 5 | React to kills |
| `react(state, events)` | 12 | See nearby combat events |
| `power_up(state)` | 18 | Define custom ability |
| `evolve(state, history)` | 22 | Adapt across matches |

### XP & Leveling (30 levels)

- XP from kills, survival, placement, first blood, leader bounties
- Levels unlock new actions, callbacks, and higher line budgets (50 → 300 lines)
- Progression gates ensure bots grow in complexity

---

## Three Ways to Play

### 1. Agent Arena (AI Prompting)

```bash
agentgrounds wars generate --strategy "aggressive close-range fighter"
```

Outputs a PROMPT.md tuned for the game. Paste into Claude/GPT → get a bot → save to `bots/` → play. The prompt IS the product — domain knowledge is the moat.

### 2. Learn to Code (Education)

```bash
agentgrounds wars init
```

Scaffolds starter bots with commented TODOs. Edit numbers, run immediately, see results. Instant feedback loop from zero coding experience.

### 3. CLI Game (Terminal Experience)

```bash
agentgrounds wars play
```

ANSI grid renders in terminal with combat animations, kill feed, and rich post-match summary. No browser, no server, no dependencies beyond Python.

---

## Visual Systems

### Terminal Renderer
- ANSI grid with colored bots, terrain tiles, storm border
- Combat sub-frame animations (action → resolve split)
- Kill feed, HP bars, standings overlay
- Final frame with winner highlight

### Browser Viewer (Canvas)
- Geometry Wars aesthetic — bots rendered as geometric shapes (circle, square, triangle, hexagon, diamond) based on archetype
- Color-coded by build type (blue=tank, red=bruiser, purple=assassin, green=controller)
- Weapon indicators, armor border thickness, HP-dependent glow
- Full replay controls: play/pause, scrubber, speed (0.5×-4×)

### Video Export (MP4)
- PIL frame generation + FFmpeg encoding
- Spectacle effects: slow-mo for dramatic moments, shatter on kills
- Audio: synthesized combat SFX, hype music escalation

### Spectacle Engine
- Scores each round for drama (0-5 tiers: calm → chaos)
- Triggers visual effects: shatter, fire_border, slow_mo, glitch, skull_flash, pulse_wave
- Informs audio mixer intensity

---

## Online Systems

### Server (FastAPI + Redis + SQLite)

| System | Status | What It Does |
|--------|--------|-------------|
| Bot submission | Working | Upload Python, AST validation, store in DB |
| Lobby | Backend working | Collects players, 30s timer, auto-fill with AI bots |
| Match queue | Working | Redis-backed job queue, worker processes matches |
| Leaderboard | Working | Rankings by wins, win rate, kills |
| Player profiles | Working | Career stats, match history, streaks |
| Stat diff | Working | Per-match comparison vs lifetime averages |
| Cosmetic store | Working | Color palettes, glow effects, weapon skins, death/trail effects |
| Tournament brackets | Working | 8/16/32 player elimination, automated match runner |
| Discord notifications | Working | Match start/end announcements |

### Security Sandbox
- **Tier 1:** AST blocklist (dangerous imports/builtins)
- **Tier 2:** Restricted builtins, process isolation, 1s timeout
- **Tier 3 (planned):** Docker containers, no network, 50MB memory limit

---

## Special Features

### The Cringe (Adaptive Boss)
- NPC bot (🍆) with full action access
- Adapts strategy based on player patterns
- Tracked encounters for progression rewards
- Optional spawn in special modes

### Helper DSL
Optional convenience wrappers for cleaner bot code:
```python
from agentgrounds.wars.helpers import Me, Enemies, Storm
me = Me(state)         # me.hp, me.move_toward(enemy), me.flee_storm()
foes = Enemies(state)  # foes.closest(), foes.weakest(), foes.adjacent()
storm = Storm(state)   # storm.active, storm.danger, storm.safe_zone_center()
```

### Match Modes
- **Standard:** 200 rounds, 100 HP, normal storm
- **Extended:** 400 rounds, 200 HP, 50% slower storm

---

## Where We Are in the Gameplay Loop

### What's Complete (Phases 1-3B)

```
Phase 1: Foundation (S1-S31)     ████████████████████ DONE
  Engine, combat, movement, stats, equipment, terrain,
  momentum, storm, CLI, terminal renderer, viewer,
  bot generation, helpers DSL, validation, sandbox

Phase 2: Depth (S32-S39)         ████████████████████ DONE
  XP/leveling, callbacks, traps, abilities, equipment
  system, tactical items, terrain engine, post-match
  experience, balance tuning

Phase 3A: Playable Product       ████████████████████ DONE
  (S40-S43)
  PyPI release, browser viewer overhaul, server layer
  (FastAPI + lobby + matchmaking), leaderboard, Discord

Phase 3B: Spectacle (S44-S47)    ████████████████████ DONE
  Character visual system, kill cam + sound + preflight,
  cosmetics + store, tournament brackets
```

### Current State

**The engine is feature-complete.** 3600+ tests, all passing. Every system listed above works. The game runs locally, renders beautifully in terminal and browser, and has a working server with lobby, tournaments, and leaderboards.

### What's Missing: The Connected Browser Flow

The gap is **not features** — it's **flow**. Everything exists as islands:

| What Works | What Doesn't |
|------------|-------------|
| Editor submits bots | Editor doesn't show real lobby state |
| Lobby collects players | No browser UI for the lobby |
| Matches run and produce replays | No auto-redirect from lobby to viewer |
| Viewer plays replays beautifully | Viewer doesn't connect to live matches |
| Results exist in match JSON | No dedicated results screen |
| Tournaments have bracket API | Tournament pages work standalone |

**The next phase is wiring these into a single player journey:** land → write bot → see opponents → countdown → watch match → see results → play again.

This is documented in `docs/proposal-kill-switch-browser-flow.md` — estimated 4 sprints (S48-S51) to complete the connected browser experience.
