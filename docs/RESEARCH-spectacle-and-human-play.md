# NPC Wars: Spectacle, Human Play & The Watcher

> Research document — game design direction for NPC Wars v2
> Date: 2026-03-13
> Status: Pre-planning (approved direction, not yet tasked)

---

## Design Thesis

NPC Wars should have **the spectacle of gladiators, the cuteness of teletubbies, and the bright-light addictiveness of a slot machine.** The entire system incentivizes good code — writing a clever `decide()` function is the only path to progression.

---

## Table of Contents

1. [Balance Rework](#1-balance-rework)
2. [Bumper Physics](#2-bumper-physics)
3. [Spectacle Engine](#3-spectacle-engine)
4. [Sound Design](#4-sound-design)
5. [Human Play — Copilot Mode](#5-human-play--copilot-mode)
6. [The Bounty System](#6-the-bounty-system)
7. [The Watcher (🍆)](#7-the-watcher-)
8. [Line Budget & Streak Rewards](#8-line-budget--streak-rewards)
9. [Action Unlocks](#9-action-unlocks)
10. [Match Modes](#10-match-modes)
11. [Community & Content Flywheel](#11-community--content-flywheel)
12. [Technical Architecture](#12-technical-architecture)
13. [Current State Baseline](#13-current-state-baseline)
14. [Open Questions](#14-open-questions)

---

## 1. Balance Rework

### Problem

The current meta rewards passivity. ChaosBot (pure random) won match 001. The storm kills more bots than combat does. Rest is free and heals 10 HP + 20 energy, making aggression a net-negative trade.

### Current Constants

| Constant | Current | Problem |
|----------|---------|---------|
| `STARTING_HP` | 100 | Fine |
| `STARTING_ATTACK_POWER` | 15 | Too low — 7 hits to kill undefended |
| `DEFEND_BONUS` | 10 | Reduces damage to 5, making TTK 20 rounds |
| `REST_HEAL` | 10 | Too high — negates ~1 attack per rest |
| `REST_ENERGY_RESTORE` | 20 | Fine |
| `ATTACK_COST` | 15 | Expensive — only 6 attacks before forced rest |
| `STORM_DAMAGE` | 10 | Fine |
| Storm start | Round 21 | Too late — 20 rounds of dead midgame |

### Proposed Changes

| Constant | New Value | Rationale |
|----------|-----------|-----------|
| `STARTING_ATTACK_POWER` | 25 | TTK drops from 7 to 4 hits undefended |
| `REST_HEAL` | 5 | Nerfs turtle strategy; 2 rests to undo 1 hit |
| `ATTACK_COST` | 10 | Allows more sustained aggression |
| Storm start round | 10 | Compresses dead midgame by 11 rounds |
| Kill bounty | +30 energy | Rewards aggression, enables kill chains |
| Damage scaling | +2 attack per 10 rounds after R15 | Late-game fights resolve faster |

### Expected Impact

- TTK drops from 7 rounds to 4 (undefended) or 7 (defending, down from 20)
- Rest no longer fully negates one attack (heals 5 vs 25 damage taken)
- Kill bounty creates snowball potential for aggressive bots
- Storm at R10 forces earlier encounters on the grid
- Passive bots lose the war of attrition; smart aggression is rewarded

---

## 2. Bumper Physics

### Concept

Bots collide. When a bot moves into a tile occupied by another bot, the target is knocked back 1-2 tiles in the direction of impact. Chain reactions occur when a knocked bot hits another bot.

### Mechanics

| Interaction | Effect |
|-------------|--------|
| **Bump** | Move into occupied tile → target knocked 1 tile in impact direction |
| **Chain bump** | Knocked bot hits another bot → secondary knockback |
| **Wall splat** | Knocked into grid edge → bonus 10 damage, no further movement |
| **Storm bounce** | Knocked into storm zone → immediate storm tick (10 damage) |
| **Dash bump** | Dash (unlocked action) moves 2 tiles, bumps anything in path |

### Resolution Order

Bumps resolve during Phase 3 (Movement), after the moving bot's position updates:

1. Moving bot enters occupied tile
2. Occupant is pushed 1 tile in the movement direction
3. If pushed into another bot → chain bump (recursive, max depth 5)
4. If pushed into wall → wall splat damage, stay at edge
5. If pushed into storm → storm damage applied immediately

### State Dict Addition

```python
state["bumps_this_round"] = [
    {"pusher": "🦆", "target": "🤖", "direction": "east", "chain": False},
    {"pusher": "🤖", "target": "🔴", "direction": "east", "chain": True},
]
```

### Why It Matters

Bumpers solve the pacing problem organically. Bots collide, chain reactions cascade, and the grid becomes a pinball table. Positioning matters because getting bumped into the storm or a wall is devastating. The spectacle engine (Section 3) amplifies chain bumps into visual events.

---

## 3. Spectacle Engine

### Philosophy

**Generative composition from authored building blocks.** The system does not use LLMs or procedural generation for individual effects. Instead, a `SpectacleEngine` scores each round's "drama level" and selects which pre-authored effects to layer.

### Drama Scoring

```python
drama_score = (
    kills * 3
    + bumper_chains * 2
    + near_death_escapes * 4
    + streak_events * 5
    + watcher_sync_milestone * 3
    + human_override_count * 1
)
```

### Effect Escalation

| Drama Score | Tier | Effects |
|-------------|------|---------|
| 0-3 | **Calm** | Normal rendering, ambient audio |
| 4-7 | **Heating up** | Subtle screen pulse, crowd murmur rises |
| 8-12 | **Intense** | Camera shake on hits, crowd cheers on kills |
| 13-18 | **Hype** | Slow-mo on kills, fire border, bass drop stingers |
| 19+ | **CHAOS** | Full screen shake, multiball pinball FX, crowd roar, every hit sparks |

### Trigger → Effect Map (Viewer & Video)

| Trigger | Visual | Audio | Kill Feed |
|---------|--------|-------|-----------|
| Standard kill | Victim emoji shatters, particles | Impact boom | "🦆 eliminated 🤖" |
| Kill streak (3+) | Screen shake + fire border | Air horn + bass drop | "🦆 UNSTOPPABLE" |
| Near-death escape (<5 HP survived) | Slow-mo frame + spotlight | Tension strings release | "🦆 BY A THREAD" |
| Bumper chain (3+) | Pinball multiball FX + score popups | Cascading bumper dings | "MULTI-BUMP x4" |
| Last 2 alive | Split-screen zoom + VS graphic | Boss fight music shift | "FINAL SHOWDOWN" |
| Storm kill | Static/glitch effect | Thunder crack | "🤖 CONSUMED BY THE STORM" |
| Watcher spawns | Screen darkens 1s, bass drop | Ominous chord | "🍆 THE WATCHER HAS ENTERED" |
| Watcher kill | Purple shockwave + slow-mo | Distorted boom | "🍆 CLAIMS ANOTHER" |
| Human enters | Spotlight + crowd gasp | Record scratch | "A HUMAN HAS ENTERED THE ARENA" |
| Human dies | Grey-out + sad trombone | Deflating balloon | "HUMANITY FALLS" |

### Implementation Layers

1. **Engine layer**: `SpectacleEngine` class consumes round events, computes drama score, emits spectacle metadata into match JSON
2. **Viewer layer**: HTML/JS reads spectacle metadata, triggers CSS animations + Web Audio stingers
3. **Video layer**: Pillow renderer reads spectacle metadata, composites effects per frame, audio mixed in ffmpeg

The match JSON schema extends with:

```json
{
    "rounds": [{
        "spectacle": {
            "drama_score": 14,
            "tier": "hype",
            "triggers": ["kill_streak", "bumper_chain"],
            "effects": ["screen_shake", "fire_border", "slow_mo"]
        }
    }]
}
```

---

## 4. Sound Design

### Three-Layer Audio Model

| Layer | Purpose | Behavior |
|-------|---------|----------|
| **Ambient** | Background mood | Cute, bubbly baseline (teletubby energy). Darkens as storm closes. Volume dips during stingers. |
| **Stingers** | Event reactions | 0.3-1s audio clips triggered by game events. Multiple can overlap. |
| **Hype track** | Escalation | Music intensity follows drama score. Quiet early, EDM drop on streak, boss music for last 2. |

### Stinger Library (minimum viable)

| Event | Sound | Duration |
|-------|-------|----------|
| Hit (normal) | Cartoon punch | 0.3s |
| Hit (critical/low HP) | Heavy impact | 0.5s |
| Kill | Explosion + crowd pop | 0.8s |
| Kill streak | Air horn | 1.0s |
| Bump | Pinball bumper ding | 0.2s |
| Chain bump | Cascading dings (pitch rises) | 0.5s |
| Wall splat | Thud + crack | 0.4s |
| Storm damage | Electric zap | 0.3s |
| Rest/heal | Gentle chime | 0.3s |
| Near-death | Tension sting | 0.5s |
| Watcher spawn | Ominous bass chord | 1.5s |
| Human enter | Record scratch + crowd gasp | 1.0s |
| Match end | Victory fanfare or defeat drone | 2.0s |

### Implementation

- **Video renderer**: Pre-mixed audio tracks composed by the render pipeline. Each stinger is a WAV/MP3 asset. `ffmpeg` mixes ambient + stingers + hype into the final MP4 audio stream.
- **HTML viewer**: Web Audio API. Stingers loaded as `AudioBuffer`, triggered by event playback. Ambient/hype as looping `<audio>` elements with gain automation tied to drama score.
- **Asset source**: Royalty-free libraries (freesound.org, mixkit) or generated via a tool like sfxr/jsfxr for retro 8-bit stingers that match the cute aesthetic.

---

## 5. Human Play — Copilot Mode

### Core Concept

Humans don't replace their bot — they **augment** it. The bot's `decide()` runs every round. The human can override the bot's decision within a 2-second input window. If no override, the bot's decision executes.

### Why Copilot Over Replacement

- **Good code always matters.** Your bot is your safety net. AFK = your bot plays normally.
- **Human input adds adaptability.** You see something the bot doesn't (e.g., The Watcher's pattern).
- **No grief vector.** A human who disconnects doesn't leave an empty slot — the bot takes over seamlessly.
- **Code progression carries.** Your line budget and unlocked actions are available to you in human mode because they're your bot's earned capabilities.

### Input Methods

| Platform | Input | Latency |
|----------|-------|---------|
| **Web viewer** | WebSocket — arrow keys for move, WASD for attack direction, R/D for rest/defend | <100ms |
| **Discord** | Button grid (reaction-style) — ephemeral message per round | ~500ms |

### Round Flow With Humans

```
Round N:
  1. Bot decide() runs for all bots (including human-owned bots)  [existing]
  2. Human input window opens (2 seconds)                          [new]
  3. If human submits action → overrides their bot's decision      [new]
  4. If timeout → bot's original decision stands                   [new]
  5. All actions resolve (defense → movement → attacks → storm)    [existing]
```

### State Exposure

Humans see the same `state` dict their bot sees, rendered visually:
- Grid with all bot positions and HP bars
- Their own HP, energy, and available actions (greyed out if insufficient energy)
- Storm border highlighted
- **No additional information** — humans have zero info advantage over bots

### AFK Handling

| Consecutive missed inputs | Effect |
|---------------------------|--------|
| 1-2 | Bot plays normally, no penalty |
| 3+ | "AFK" badge appears on emoji, spectators can see |
| 10+ | Kicked from human mode, bot continues autonomously |

---

## 6. The Bounty System

### How Bots Know to Aggro Humans

When a human player is present, the engine places a **bounty** on them. The bounty is visible in every bot's `state` dict:

```python
state["bounties"] = [
    {
        "target_emoji": "👨",
        "target_x": 5,
        "target_y": 3,
        "reward": "full_restore",  # full HP + energy on kill
        "bonus_damage": 3,         # +3 rounds of +50% damage after kill
    }
]
```

### Why Bounty Over Forced Aggro

Bots aggro humans **because it's strategically optimal**, not because the engine overrides their logic. This preserves the "your code matters" thesis:

- A smart bot that checks `state["bounties"]` and hunts the human is rewarded
- A dumb bot that ignores bounties plays normally and misses out
- A clever bot that waits for someone else to weaken the human, then swoops in for the kill — that's good code

### Bounty Rewards

| Kill Target | Reward |
|-------------|--------|
| Regular bot | +30 energy (kill bounty from balance rework) |
| Human player | Full HP restore + full energy restore + 3 rounds of +50% damage |

The human bounty is massive — 5-10x the value of a regular kill. This makes hunting humans the dominant strategy without hard-coding it.

### Scaling for Co-op

| Humans in match | Bounty per human |
|-----------------|-----------------|
| 1 | Full restore + 3 rounds +50% damage |
| 2 | Full restore + 2 rounds +50% damage |
| 3-4 | Full energy only + 1 round +50% damage |

Diminishing bounty prevents bots from snowballing off multiple human kills.

---

## 7. The Watcher (🍆)

### Identity

**The Watcher** is a single, persistent, community-wide nemesis bot. It is not authored by any player. Its emoji is 🍆. It exists across all matches, learning from every human encounter.

It is always referred to as The Watcher. The eggplant is the brand.

### Spawn Conditions

The Watcher does not start in every match. It spawns mid-match when a human player demonstrates skill:

| Trigger | Threshold |
|---------|-----------|
| Human survives N rounds | 5 rounds with >50% HP |
| Human gets a kill | Any kill in human mode |
| Human overrides bot successfully | 3 overrides that result in damage dealt |

When triggered, The Watcher spawns at a random valid tile 3+ tiles from any human. Full spectacle treatment (Section 3).

### Behavior: Play the Game, Hunt Humans

The Watcher is a real match participant. It fights bots when no humans are nearby. But it **prioritizes** humans via the bounty system — and its code is good enough to always take the bounty.

When no humans are present (pure bot matches), The Watcher does not spawn.

### The Pattern Table

The Watcher's "brain" is a frequency counter per player, not a neural net:

```python
# Conceptual structure (persisted between matches)
watcher_memory = {
    "player_abc123": {
        "after_taking_damage": {"move_away": 0.73, "attack_back": 0.15, "defend": 0.12},
        "at_range_1": {"attack": 0.89, "defend": 0.06, "move": 0.05},
        "below_30_hp": {"rest": 0.61, "defend": 0.22, "move": 0.17},
        "storm_closing": {"move_to_center": 0.95, "fight": 0.05},
        "override_rate": 0.45,  # how often they override their bot
        "override_after_damage": 0.82,  # when they tend to override
    },
    "__global__": {
        # aggregated patterns across ALL humans
    }
}
```

### Counter-Action Selection

Each round, The Watcher:

1. Identifies the nearest human
2. Looks up their pattern profile (falls back to `__global__` for new players)
3. Predicts their most likely action this round
4. Selects the counter-action:
   - Human likely to move right → Watcher positions to intercept right
   - Human likely to attack at range 1 → Watcher defends then retaliates
   - Human likely to rest → Watcher rushes during the vulnerability window
   - Human likely to override → Watcher uses the bot's pattern instead

### Sync Rating (Spectator-Visible)

The Watcher has a visible **sync percentage** — how accurately it predicts the current human's next action. Displayed to spectators, NOT to the player:

> 🍆 The Watcher — Sync: 73%

| Match Phase | Typical Sync |
|-------------|-------------|
| Rounds 1-3 | 15-25% (guessing) |
| Rounds 4-7 | 40-55% (reading patterns) |
| Rounds 8-12 | 65-80% (knows your tendencies) |
| Rounds 13+ | 80-95% (you must improvise or die) |

If the human switches up (breaks their own pattern, overrides unexpectedly), sync drops by 10-15%. The meta-game for spectators: **can the human stay unpredictable faster than The Watcher adapts?**

### Rubber-Banding

The Watcher's counter-action accuracy is throttled to keep matches competitive:

| Human Performance | Watcher Accuracy Cap |
|-------------------|---------------------|
| Losing (low HP, no kills) | 60% (misses 40% of predictions) |
| Even (trading blows) | 75% |
| Winning (got kills, high HP) | 90% |
| Dominating | 95% (near-perfect reads) |

The player never knows the cap. They just feel it getting harder when they're winning and slightly easier when they're losing.

### Learning Persistence

| Scope | Retention | Purpose |
|-------|-----------|---------|
| **Within match** | 100% | Sync ramps during the match |
| **Between matches (same session)** | 70% | Escalates across a play session |
| **Between sessions** | 30% | Veterans feel recognized, newcomers aren't overwhelmed |
| **Global aggregate** | 100% | `__global__` profile never decays — The Watcher gets smarter over time as more humans play |

### Full Action Set

The Watcher has access to **every action in the game**, including all unlockable actions (Section 9). It doesn't need to earn them — it's the final boss:

| Action | Availability |
|--------|-------------|
| `move` | Always |
| `attack` | Always |
| `defend` | Always |
| `rest` | Always |
| `ranged_attack` | Always (unlocked at 3-win streak for players) |
| `dash` | Always (unlocked at 5-win streak for players) |
| `taunt` | Always (unlocked at 10-win streak for players) |

The Watcher having all abilities makes it the ultimate test — can your code + your piloting beat something with every tool?

### Co-op Behavior — Adaptive Target Rotation

The Watcher is always a **single instance**. It does not clone. In co-op matches with multiple humans, it:

1. **Maintains separate pattern profiles per human.** Each player has their own frequency table and sync rating.
2. **Rotates targets fluidly.** It stalks whichever human it currently has the highest sync on. If it reads Player A at 78% sync and Player B at 45%, it hunts A. When A starts improvising and sync drops, it pivots to B.
3. **Scales stats with human count.** More humans = more Watcher HP and energy, keeping it dangerous against a squad.

| Humans | Watcher HP | Watcher Energy | Watcher Damage |
|--------|-----------|----------------|----------------|
| 1 | 100 | 100 | 25 (standard) |
| 2 | 150 | 130 | 25 |
| 3 | 200 | 160 | 30 |
| 4 | 250 | 200 | 35 |

4. **Gathers data from every encounter simultaneously.** Even while fighting Player A, it observes what Players B/C/D do from across the grid. Their movement patterns, override tendencies, and positioning habits are all logged.
5. **Never stops adapting.** The Watcher adapts always — between targets, between rounds, between matches. There is no pause in its learning. Switching targets doesn't reset its read on the previous player.

The rotation creates a horror-movie dynamic in co-op: you never know when 🍆 will pivot from your teammate to you. And when it does, it already has data.

### Kill/Death Tracking

The Watcher's lifetime stats are public and part of the community narrative:

```
🍆 The Watcher — Lifetime Stats
Matches: 847
Kills: 2,341 (humans: 1,892 | bots: 449)
Deaths: 203
Win rate vs humans: 68%
Current form: 12-match win streak
Most-studied player: @kmasty (47 encounters, 73% sync)
```

---

## 8. Line Budget & Streak Rewards

### Core Mechanic

Every bot has a **line budget** — the maximum number of lines allowed in its `decide()` function. Bots start small and earn more lines through performance.

### Budget Progression

| Achievement | Line Reward | Cumulative Max |
|-------------|-------------|----------------|
| **Base** | 50 lines | 50 |
| Win a match | +10 lines | 60 |
| 3-win streak | +15 lines | 75 |
| 5-win streak | +25 lines | 100 |
| 10-win streak | +50 lines | 150 |
| "Most Kills" in a match | +10 lines | — |
| Survive 10 matches total | +10 lines | — |
| Beat The Watcher | +20 lines | — |
| **Hard cap** | — | **200** |

### Why This Works

- **50 lines forces elegance.** You can't brute-force strategy in 50 lines — you need clean, clever code.
- **More lines = more strategy space.** A 100-line bot can run state machines, threat modeling, prediction. A 50-line bot is reactive only.
- **Visible progression.** The community sees your line budget grow. A 150-line bot is a veteran.
- **Losing resets nothing.** You keep earned lines. Streaks just accelerate growth.
- **Natural tiers.** Scrappy 50-line newcomers vs battle-hardened 150-line veterans.
- **Incentivizes code quality over quantity.** You WANT to do more with fewer lines.

### Enforcement

The existing `bot_scanner.py` AST scanner counts lines in the `decide()` function body. Bots exceeding their budget are rejected at validation time. The budget is stored in a persistent player profile (see Section 12).

### Line Counting Rules

- Only lines inside `decide()` count (imports, constants, helper functions outside are free up to the file-level architecture limits)
- Blank lines and comments don't count
- One statement per line (no semicolon chaining — AST enforced)

---

## 9. Action Unlocks

### Progression

Beyond line budget, bots unlock new action types through win streaks:

| Streak | Unlocks | Energy Cost | Effect |
|--------|---------|-------------|--------|
| **0** | `move`, `attack`, `rest`, `defend` | 5/10/0/10 | Base actions |
| **3 wins** | `ranged_attack(direction)` | 20 | Attack tile 2 away. Lower damage (15 vs 25). |
| **5 wins** | `dash(direction)` | 15 | Move 2 tiles. Bumps anything in path. |
| **10 wins** | `taunt` | 10 | Force all bots within 2 tiles to target you next round. Tank play. |

### Design Rationale

- **Ranged attack** (3 wins): Creates kiting vs brawling tradeoffs. A 50-line bot with range can outplay a melee-only bot through positioning.
- **Dash** (5 wins): Enables aggressive engagement and escape. Synergizes with bumper physics — dash through a crowd for chain bumps.
- **Taunt** (10 wins): Enables tank/support play in co-op. Draw aggro while teammates deal damage. High-skill, high-reward.

### State Dict Additions

```python
state["me"]["unlocked_actions"] = ["move", "attack", "rest", "defend", "ranged_attack", "dash"]
state["me"]["line_budget"] = 100
state["me"]["win_streak"] = 5
```

### Matchmaking Consideration

Unlocked actions create power asymmetry. Options:
- **No matchmaking** — open field, veterans fight newcomers. The spectacle of a 50-line bot beating a 150-line veteran is content.
- **Tiered matches** — bronze (50 lines, base actions), silver (75-100 lines, ranged), gold (100+, all actions). Less chaotic but fairer.
- **Mixed with handicap** — veterans start with less HP proportional to their line budget advantage.

Recommendation: **No matchmaking for now.** The asymmetry IS the content. David vs Goliath moments drive engagement.

---

## 10. Match Modes

| Mode | Humans | Bots | Watcher | Vibe |
|------|--------|------|---------|------|
| **Classic** | 0 | 5-20 | No | Pure bot-vs-bot. The core game. |
| **Invasion** | 1 | 5-10 | Spawns if human is skilled | Solo human vs the machines. Death sentence by design — exists for the clip. |
| **Co-op Raid** | 2-4 | 10-15 | Spawns if humans are winning | Squad vs bot army. The intended human mode. |
| **Gauntlet** | 1 | Waves | After wave 5 | Survive escalating bot waves. Streamer bait. |
| **Boss Fight** | 2-4 | 1 | No | Humans vs one community bot promoted to Boss (5x HP, 2x damage, full unlocks). Weekly event. |

### Boss Fight Details

One community member's bot gets promoted to **Boss** for the week:
- 500 HP, 2x damage, all actions unlocked
- The bot's code runs unmodified — it just has boosted stats
- 2-4 humans queue to fight it live in copilot mode
- The bot author watches their creation fight real people

Discord announcement:
> **BOSS FIGHT FRIDAY**
> This week's boss: 🦆 GooseLoose (by @kmasty)
> 500 HP | Dash unlocked | 3-match win streak
> Queue opens at 8pm EST. Bring friends.

---

## 11. Community & Content Flywheel

### Content Generation by Mode

| Mode | Content Type | Platform |
|------|-------------|----------|
| Classic | "Look at my clever bot" highlights | Twitter/Discord |
| Invasion | "I got wrecked by 🍆" rage clips | YouTube/TikTok |
| Co-op | Squad coordination highlights | YouTube |
| Boss Fight | Weekly community event recaps | Discord/YouTube |
| Gauntlet | Survival run leaderboards | Discord |

### Community Hooks

| Hook | Mechanism | Engagement |
|------|-----------|------------|
| **Weekly scheduled matches** | Cron job triggers Classic match, auto-posts results to Discord | Recurring appointment |
| **Boss Fight Friday** | Weekly event, top bot promoted to boss, humans queue | Appointment viewing |
| **Seasonal leaderboard** | "Season 1: The Goose Awakens" — resets quarterly | Freshness |
| **Bot of the Week** | Most creative `decide()` spotlighted in Discord | Recognition |
| **Bounty challenges** | "First bot to beat TankBot 3 times wins a role" | Goal-directed |
| **Watcher stats** | Community-wide Watcher kill/death tracker | Shared narrative |
| **Line budget showcase** | "This 50-line bot beat a 150-liner" moments | Aspiration |

### The Watcher as Narrative Engine

The Watcher is the community's shared antagonist. Its lifetime stats, current form, and adaptation patterns are public. Players talk about it like a character:

- "The Watcher learned dash-baiting from that streamer, now it does it to everyone"
- "Someone broke 🍆's streak — sync dropped to 40% for the next three matches"
- "Season 2 Watcher reset — race to see who tames it first"

---

## 12. Technical Architecture

### New Engine Components

| Component | Purpose | Depends On |
|-----------|---------|------------|
| `engine/bumpers.py` | Collision detection, knockback, chain resolution | grid.py, combat.py |
| `engine/bounty.py` | Bounty placement, reward distribution, scaling | combat.py |
| `engine/spectacle.py` | Drama scoring, effect selection, metadata emission | rounds.py |
| `engine/watcher.py` | Pattern table, sync calculation, counter-action selection | sandbox.py, state.py |
| `engine/watcher_memory.py` | Persistent pattern storage (JSON), decay, per-player profiles | — |
| `engine/progression.py` | Line budget tracking, streak calculation, action unlock gating | — |
| `engine/human_input.py` | WebSocket/Discord input adapter, copilot override logic | sandbox.py |

### Extended State Dict

```python
{
    "me": {
        "x": int, "y": int, "hp": int, "energy": int,
        "attack_power": int, "defense": int,
        "unlocked_actions": ["move", "attack", "rest", "defend", ...],
        "line_budget": int,
        "win_streak": int,
    },
    "enemies": [
        {"name": str, "emoji": str, "x": int, "y": int, "hp": int,
         "is_watcher": bool}
    ],
    "bounties": [
        {"target_emoji": str, "target_x": int, "target_y": int,
         "reward": str, "bonus_damage": int}
    ],
    "bumps_this_round": [
        {"pusher": str, "target": str, "direction": str, "chain": bool}
    ],
    "round": int,
    "grid_size": int,
    "storm_border": int,
}
```

### Extended Match JSON

```json
{
    "rounds": [{
        "round": 1,
        "storm_border": 0,
        "positions": [...],
        "events": [
            {"type": "bump", "pusher": "🦆", "target": "🤖", "direction": "east"},
            {"type": "chain_bump", "pusher": "🤖", "target": "🔴", "direction": "east"},
            {"type": "wall_splat", "target": "🔴", "damage": 10},
            {"type": "watcher_spawn", "sync": 15},
            {"type": "human_override", "player": "👨", "original": "rest", "override": "attack east"},
            {"type": "bounty_claimed", "killer": "🦆", "target": "👨", "reward": "full_restore"}
        ],
        "spectacle": {
            "drama_score": 14,
            "tier": "hype",
            "triggers": ["kill_streak", "bumper_chain"],
            "effects": ["screen_shake", "fire_border", "slow_mo"]
        },
        "watcher_sync": 73
    }]
}
```

### Player Profile (Persistent)

```json
{
    "player_id": "github_username",
    "bot_name": "GooseLoose",
    "emoji": "🦆",
    "line_budget": 100,
    "wins": 23,
    "current_streak": 5,
    "best_streak": 8,
    "unlocked_actions": ["move", "attack", "rest", "defend", "ranged_attack", "dash"],
    "watcher_encounters": 47,
    "watcher_wins": 15,
    "watcher_losses": 32
}
```

### Real-Time Layer (Human Play)

```
                    ┌──────────────┐
                    │  Web Viewer  │◄── WebSocket ──┐
                    └──────┬───────┘                │
                           │                        │
                    ┌──────▼───────┐         ┌──────┴───────┐
                    │   Engine     │         │  Human Input  │
                    │  (tick loop) │◄────────│   Adapter     │
                    └──────┬───────┘         └──────┬───────┘
                           │                        │
                    ┌──────▼───────┐         ┌──────┴───────┐
                    │  Match JSON  │         │ Discord Buttons│
                    └──────────────┘         └───────────────┘
```

The engine tick loop becomes async when humans are present:
1. Collect bot decisions (existing — multiprocessing sandbox)
2. Open 2-second human input window (new — await WebSocket/Discord)
3. Merge decisions (override if human input received)
4. Resolve round (existing pipeline + bumper phase)

---

## 13. Current State Baseline

### What Exists and Works

- Engine: 7-phase round pipeline, 5 seed bots, seeded RNG
- Match output: Full JSON with positions, events, eliminations, stats
- HTML viewer: Canvas-based, play/pause/speed/scrubber, dark theme
- Video renderer: Pillow + ffmpeg, grid/sprites/effects/overlay
- YouTube pipeline: OAuth2 auth, resumable upload, metadata generation
- Discord bot: 10 slash commands, emoji claims, match runner, announcements
- CI: Lint, test (80% coverage gate), bot validation on PR
- Submission flow: Template, local validation, PR template, CI gate
- Tests: 44 test files, ~6,400 lines

### What Needs Building (High-Level)

| Feature | New Code | Modifies |
|---------|----------|----------|
| Balance rework | — | combat.py constants, grid.py storm timing |
| Bumper physics | bumpers.py | rounds.py (new phase), grid.py |
| Kill bounty | bounty.py | combat.py, state.py |
| Spectacle engine | spectacle.py | rounds.py, match_writer.py |
| Sound design | audio assets + mixer | video_render.py, viewer/match.html |
| Line budget system | progression.py | bot_scanner.py, loader.py |
| Action unlocks | progression.py | sandbox.py (validation), state.py |
| Human copilot mode | human_input.py | game.py (async tick), state.py |
| Bounty system | bounty.py | state.py, combat.py |
| The Watcher | watcher.py, watcher_memory.py | game.py (spawn logic), state.py |
| Viewer spectacle FX | — | viewer/match.html (CSS/JS) |
| Video spectacle FX | — | video_effects.py, video_render.py |
| Audio pipeline | audio/ module | video_render.py (ffmpeg audio mixing) |
| WebSocket server | realtime/ module | game.py, viewer/match.html |

---

## 14. Open Questions

### Game Design

1. **Matchmaking or open field?** Current recommendation: open field, no tiers. The asymmetry is content. Revisit if new player retention suffers.

2. **Watcher respawn within match?** If killed, does it come back? Current recommendation: no in-match respawn. It comes back next match with updated patterns. Death IS meaningful.

3. **Line budget for helper functions?** Only `decide()` body is counted. Helpers outside `decide()` are free (subject to file-level architecture limits). This lets advanced players build reusable utility libraries.

4. **Co-op communication?** Currently none — no chat, no pings, just positioning. This forces emergent coordination. Consider adding a single "ping" action (marks a tile for teammates) if co-op feels too chaotic.

5. **Seasonal resets?** The Watcher's `__global__` profile resets per season. Player line budgets do NOT reset — earned progression is permanent.

### Technical

6. **WebSocket framework?** Options: `websockets` (stdlib-adjacent), `FastAPI + WebSocket`, `aiohttp`. The viewer is a single HTML file — keep the server lightweight.

7. **Watcher memory format?** JSON file vs SQLite. JSON is simpler and fits the flat-file architecture. SQLite if query patterns get complex.

8. **Audio asset pipeline?** Generate 8-bit stingers with jsfxr (fits cute aesthetic) or source from royalty-free libraries. Need licensing clarity before shipping.

9. **Python version requirement?** Currently 3.13+. Should drop to 3.10+ to 10x the potential player base. The codebase uses `X | None` (3.10+) and `list[...]` generics (3.9+) — nothing requires 3.13.

10. **Hosted viewer?** GitHub Pages is the obvious choice (static HTML, zero dependencies). Add `?match=URL` support to load match JSON from any URL, enabling shareable replay links.

---

*This document captures the approved design direction as of 2026-03-13. It is a research artifact for planning — no implementation has begun. Sprint planning should reference this document when breaking work into tasks.*
