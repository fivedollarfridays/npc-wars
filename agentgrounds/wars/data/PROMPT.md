# NPC Wars — Bot Builder Prompt

You are writing a competitive bot for NPC Wars, a battle royale where bots fight on a grid. All bots act simultaneously each round. Last bot standing wins. Your bot is a single Python file.

## Bot File Format

```python
BOT_NAME = "MyBot"
BOT_EMOJI = "🤖"
BOT_BIO = "Short description of strategy"

# Stat allocation (must sum to 100, min 5 each)
BOT_POWER = 25
BOT_SPEED = 25
BOT_ARMOR = 25
BOT_MIND = 25

# Equipment (optional — defaults to sword + leather if omitted)
BOT_EQUIPMENT = {
    "weapon": "sword",           # 8 credits
    "armor": "leather",          # 6 credits
    "accessories": [],           # up to 2
    "tactical": None,            # up to 1
}
# Total: 14 / 40 credits

def decide(state):
    # Your logic here
    return ("rest",)
```

`BOT_NAME`, `BOT_EMOJI`, and `BOT_BIO` are module-level strings. `BOT_EQUIPMENT` is optional (defaults apply). `decide(state)` is called every round and must return an action tuple.

## The State Dict

`decide(state)` receives this dict every round:

```python
state = {
    "me": {
        "x": 3, "y": 5,          # grid position (0-indexed)
        "hp": 80,                  # 0-max_hp
        "energy": 60,              # 0-max_energy
        "attack_power": 25,        # base + round scaling
        "score": 18,               # cumulative match score
        "momentum_tier": 1,        # 0-4, see Momentum System
        "momentum_name": "Momentum",  # tier display name
        "is_leader": False,        # True if you're the highest scorer
        "power": 25, "speed": 25, "armor": 25, "mind": 25,  # stat allocation
        "max_hp": 145, "max_energy": 100,     # derived from stats
        "min_damage": 35, "max_damage": 55,   # damage range from POWER
        "dodge_chance": 7.5,                   # % chance to halve incoming damage
        "damage_reduction": 0,                 # flat DR from ARMOR
        "equipment": {"weapon": "sword", "armor": "leather", "accessories": [], "tactical": None},
        "equipment_bonuses": {"to_hit": 1, "min_damage": 3, "max_damage": 5, "dr": 2, ...},
        "hit_chance_vs": {                     # your hit probability vs each enemy
            "🎯": {"hit_chance": 75.0, "crit_chance": 5.0, "dodge_chance": 10.0, "expected_damage": 16.8},
        },
        "incoming_threat": [                   # enemies ranked by danger to you
            {"emoji": "🎯", "hit_chance": 75.0, "expected_damage": 16.8},
        ],
    },
    "enemies": [
        {"x": 7, "y": 2, "hp": 45, "emoji": "🎯", "name": "Rival",
         "score": 12, "momentum_tier": 1, "is_leader": True,
         "max_hp": 120, "speed_class": "normal",
         "weapon": "axe", "armor": "plate"},
        # ... more living enemies
    ],
    "grid_size": 10,               # 10x10 grid
    "storm_border": 2,             # tiles from each edge that are storm
    "round": 15,                   # current round number
}
```

**Important:** Enemy energy is NOT visible. You can see position, HP, emoji, name, score, momentum tier, max_hp, and speed_class. Use `hit_chance_vs` to make informed attack decisions.

## Actions and Costs

Return one of these tuples from `decide(state)`:

| Action | Return Value | Energy Cost | Effect |
|--------|-------------|-------------|--------|
| Move | `("move", "north")` | 5 | Move 1 tile (north/south/east/west) |
| Attack | `("attack", "north")` | 10 | Deal damage to adjacent tile in that direction |
| Defend | `("defend",)` | 10 | Halve incoming damage this round |
| Rest | `("rest",)` | 0 | Recover +5 HP and +20 energy |
| Dash | `("dash", "north")` | 15 | Move 2 tiles in a direction |
| Ranged Attack | `("ranged_attack", "north")` | 10 | Shoot at range (-2 hit, 60% damage) |
| Taunt | `("taunt", "🎯")` | 5 | Force target to attack you (-3 vs others) |
| Trap | `("trap", "north")` | 15 | Place hidden trap 1 tile in direction (level 12+) |

If your bot returns an invalid action or crashes, it defaults to rest.

### Traps (Level 12+)

Place invisible traps that trigger when an enemy steps on them.

- **Damage**: 20 base + 0.5 × max(0, POWER − 25). Reduced by target's armor DR
- **Cooldown**: 3 rounds between placements
- **Lifetime**: 10 rounds or until triggered
- **Visibility**: Hidden from enemies until triggered. You see your own traps in `state["me"]["traps"]`

```python
def decide(state):
    # Place a trap to the north
    if state["me"]["trap_cooldown"] == 0:
        return ("trap", "north")
```

**Trap Strategy Tips:**
- **Defensive**: Place traps on retreat paths to punish chasers
- **Offensive**: Place traps toward enemies — they often move predictably
- **Storm edge**: Traps near storm boundaries catch bots forced inward
- **Enemy awareness**: `state["enemies"][i]["trap_count"]` tells you how many traps an enemy has active
- **Energy budget**: 15 energy per trap vs 10 per attack — worth it when traps trigger (53%+ hit rate)
- **POWER scaling**: High-POWER builds get more trap damage — Bruiser trappers hit hardest

## Resolution Order

Every round resolves in this exact sequence:

1. **Defend** — defense bonuses applied
2. **Move** — positions update
3. **Attack** — melee damage resolves against post-move positions
4. **Storm** — storm damage applied to bots outside safe zone
5. **Energy** — costs deducted, rest healing applied
6. **Deaths** — bots at 0 HP eliminated

Simultaneous attacks: if two bots attack each other, both take damage. Both can die in the same round.

## Key Constants

| Stat | Value |
|------|-------|
| Starting HP | 145 (max 145) |
| Starting Energy | 100 (max 100) |
| Base Attack Power | 25 damage |
| Attack Scaling | +2 per 10 rounds after round 15 |
| Defend | Halves incoming damage (take 15 instead of 25) |
| Storm Damage | 10 HP per round while in storm |
| Kill Bounty | +30 energy instantly on kill |
| Rest Recovery | +5 HP, +20 energy |

## The Storm

The storm closes from all edges toward the center. Any bot in the storm takes 10 damage per round. The storm is deterministic:

- Rounds 1-9: no storm
- Rounds 10-29: border = (round - 9) // 5 tiles from edge (integer division)
- Rounds 30+: border grows +1 tile every 2 rounds

Pre-position 1-2 rounds early. Reacting to the storm wastes energy catching up.

## Momentum System

Bots earn points each round. Points build momentum tiers that grant combat bonuses.

### Scoring Table

| Source | Points | Condition |
|--------|--------|-----------|
| Survival | +1 | Alive at end of round |
| Kill | +10 | Per kill |
| Clean Kill | +5 | Got a kill AND took 0 damage that round |
| Damage Dealt | +1 | Per 25 HP dealt |
| Full HP | +2 | End round at 145 HP |
| Storm Survivor | +3 | Alive when storm first activates |
| Last Standing | +15 | Only bot alive |

### Momentum Tiers

| Tier | Name | Score Threshold | Bonus |
|------|------|-----------------|-------|
| 0 | (none) | 0 | No bonus |
| 1 | Momentum | 10 | +5 energy regen per round |
| 2 | Battle Fury | 25 | +10% damage dealt |
| 3 | Crowd Favorite | 40 | Visual only (aura effect) |
| 4 | Unstoppable | 60 | -15% incoming damage |

Bonuses are cumulative: tier 4 gets all lower-tier bonuses too.

### King of the Hill

Only **one bot** can be tier 3 or higher -- the **leader** (highest score). All other bots are capped at tier 2 regardless of score.

- The leader is visible to all bots via `state["me"]["is_leader"]` and `state["enemies"][i]["is_leader"]`
- **Leader bounty**: Kill the leader for **+20 bonus points** (on top of normal +10 kill points)
- **Energy drain**: Tier 2+ costs energy per round: tier 2 = -3, tier 3 = -5, tier 4 = -8
- **Crown transfer**: If you overtake the leader's score, you become the new leader instantly

**Strategy implications:**
- Target the leader for +20 bounty points -- a leader kill can instantly push you to a higher tier
- Being the leader makes you a target and drains your energy -- staying on top is expensive
- Energy drain at tier 4 (-8/rd) means the leader must keep fighting to sustain energy

## Stat Allocation

Customize your bot's build with four stats that sum to 100 (minimum 5 each):

```python
BOT_POWER = 25    # Attack damage range and crit multiplier
BOT_SPEED = 25    # Dodge chance, initiative (attack order), to-hit bonus
BOT_ARMOR = 25    # Max HP and damage reduction
BOT_MIND = 25     # Max energy and energy regen per rest
```

Default is 25/25/25/25 (balanced). Specializing creates tradeoffs — high POWER hits harder but low ARMOR means less HP.

### Derived Stats

| Stat | Effect | At 25 (default) | At 50 (specialized) |
|------|--------|-----------------|---------------------|
| POWER | Damage range (min-max) | 35-55 (avg 45) | 22-55 (avg 38) |
| POWER | Crit multiplier | 1.5x | 2.0x |
| SPEED | Dodge chance | 7.5% | 17.5% |
| SPEED | Initiative (attack order) | 25 | 50 (attacks first) |
| ARMOR | Max HP | 145 | 90 |
| ARMOR | Damage reduction | 0 | 6 |
| MIND | Max energy | 100 | 120 |
| MIND | Energy regen per rest | +0 | +15 |

Balanced builds (25/25/25/25) get a **versatility HP bonus** of up to +75 HP. Specializing reduces this bonus.

### Archetype Guide

| Archetype | Stats (P/S/A/M) | Strengths | Weaknesses |
|-----------|-----------------|-----------|------------|
| **Balanced** | 25/25/25/25 | Versatility HP bonus, no weak stat | No specialization edge |
| **Bruiser** | 35/15/35/15 | High damage + armor | Slow, low energy |
| **Assassin** | 20/50/15/15 | Fast, high dodge, attacks first | Fragile, low damage |
| **Tank** | 15/15/50/20 | Maximum HP, high DR | Low damage, slow |
| **Mage** | 15/20/20/45 | Huge energy pool, fast regen | Low damage, fragile |
| **Glass Cannon** | 50/15/15/20 | Highest burst damage | Very fragile, slow |

Choose an archetype that matches your strategy: Bruiser for aggressive play, Tank for survival, Assassin for hit-and-run, Mage for sustained fights, or Balanced for adaptability.

## Equipment System

Stats = who you are. Equipment = what you carry. Set `BOT_EQUIPMENT` in your bot file (optional, defaults to sword + leather). Total budget: **40 credits**.

### Weapons (pick 1, required)

| Weapon | Cost | To-Hit | Damage | Special |
|--------|------|--------|--------|---------|
| **Dagger** | 5 | +2 | +2/+2 | Finesse (scales with SPEED) |
| **Sword** | 8 | +1 | +3/+5 | Versatile (balanced) |
| **Axe** | 9 | -1 | +1/+10 | Crit multiplier +0.2x |
| **Mace** | 7 | 0 | +4/+4 | Armor-piercing (bypass 4 DR) |
| **Bow** | 6 | +1 | +1/+3 | Ranged-preferred |
| **Spear** | 8 | 0 | +2/+6 | Reach (attack at 2 tiles) |

### Armor (pick 1, required)

| Armor | Cost | DR | Energy Penalty | Special |
|-------|------|----|----------------|---------|
| **Leather** | 6 | +2 | None | Light |
| **Chain Mail** | 8 | +4 | -2 all actions | Balanced |
| **Plate** | 11 | +6 | -4 move/dash/ranged | Heavy tank |
| **Reinforced** | 10 | +3 | -1 all actions | Efficient |
| **Crystal** | 14 | +1 | None | +1 energy/rest |

### Accessories (pick 0-2)

| Accessory | Cost | Effect |
|-----------|------|--------|
| **Ring of Health** | 4 | +10 max HP |
| **Ring of Haste** | 5 | +2 initiative, -1 energy cost |
| **Amulet of Crit** | 6 | +0.3x crit, +5% crit chance |
| **Charm of Evasion** | 5 | +3% dodge |
| **Pendant of Mind** | 4 | +10 max energy, +2 regen |
| **Cloak of Shadows** | 7 | +3 DR |
| **Boots of Speed** | 6 | +5 initiative |
| **Compass** | 3 | +1 to-hit |

**Tips:** Mace counters plate (bypasses 4 DR). Finesse dagger scales with SPEED. Plate costs energy to move. Enemy weapon/armor visible via `state["enemies"][i]["weapon"]`.

## Terrain

Matches can be played on different maps. Each map has terrain tiles that affect movement and combat.

| Tile | Movement | Combat |
|------|----------|--------|
| **Wall** `#` | Blocked | Blocks ranged LoS |
| **Water** `~` | +5 energy cost | -2 to-hit, no rest healing |
| **High Ground** `^` | Normal | +2 to-hit, +15% damage |
| **Cover** `%` | Normal | +3 AC |
| **Crystal** `*` | Normal | +10 energy on first step |

Maps: Arena, Fortress, Highlands, Maze, Storm Pit. Check `state["me"]["on_terrain"]` and `state["terrain"]`.

## Combat Mechanics

Attacks use a **d20 roll system**:

1. **Roll**: d20 + (SPEED / 10) modifier
2. **Hit**: roll >= target's AC (base 8 + damage_reduction + 6 if defending)
3. **Critical**: natural 20 always crits. Crit damage = base × crit_multiplier
4. **Dodge**: after hit, defender rolls dodge chance. Dodged hits deal half damage
5. **Miss**: roll < AC = 0 damage

**Situational modifiers:**
- +3 to-hit vs resting targets (they're stationary)
- -3 to-hit when taunted, attacking a non-taunter

**Ranged attacks**: -2 to-hit penalty, 60% damage scaling (avg ~15 at default stats).

Your bot can see hit probabilities: `state["me"]["hit_chance_vs"]` shows your chance to hit each enemy, and `state["me"]["incoming_threat"]` ranks enemies by danger.

## Visual Identity

Optional: set `BOT_GLYPH` to a Unicode character for your bot's visual identity:

```python
BOT_GLYPH = "◆"  # Rendered with HP-dependent coloring
```

Glyphs are colored based on HP (white > green > yellow > red). If not set, your BOT_EMOJI is used instead.

### Carryover

The match winner carries 50% of their final score into the next match, capped at 50 points. This means winning streaks build early momentum in follow-up matches.

### Strategy Tips

- **Target the leader** for +20 bounty. Leader bleeds 5-8 energy/round at tier 3+.
- **Full HP rounds = +2 points**. Clean kills = +5 bonus.
- **Read hit_chance_vs** before attacking. Low chance? Defend or reposition.
- **Build to your strategy**: POWER for burst, SPEED for evasion, ARMOR for survival, MIND for sustain.

## Callbacks (Optional)

Define optional functions alongside `decide()` for advanced gameplay:

| Callback | Level | Signature | Timing |
|----------|-------|-----------|--------|
| `setup` | 8+ | `setup(state)` | Once before round 1 |
| `on_kill` | 5+ | `on_kill(state, victim_emoji)` | After you eliminate a bot |
| `react` | 12+ | `react(state, events)` | Each round, after combat |

```python
def setup(state):
    """Pre-match initialization. Track enemies, set strategy."""
    pass  # Initialize counters, pick targets

def react(state, events):
    """See what happened nearby (3-tile radius) this round."""
    for e in events:
        if e["type"] == "kill":
            pass  # Someone died nearby — adapt
```

Callbacks are read-only (no return value used). Exceptions are caught — a buggy callback won't crash your bot.

## Helpers API (Optional)

Import from `agentgrounds.wars.helpers` for convenience wrappers. These are optional but reduce boilerplate:

```python
from agentgrounds.wars.helpers import Me, Enemies, Storm

def decide(state):
    me = Me(state)        # wraps state["me"] with helper methods
    foes = Enemies(state) # wraps state["enemies"] with filtering
    storm = Storm(state)  # wraps storm state with danger checks
```

**Me** — `me.hp`, `me.energy`, `me.attack_power`, `me.x`, `me.y`, `me.rest()`, `me.defend()`, `me.attack(enemy)`, `me.move_toward(target)`, `me.move_away_from(target)`, `me.flee_storm()`, `me.adjacent_enemies()`, `me.can_kill_adjacent()`, `me.weakest_adjacent()`, `me.threatened()`, `me.dist_to(target)`

**Enemies** — `foes.count`, `foes.closest()`, `foes.weakest()`, `foes.wounded(threshold=50)`, `foes.adjacent()`, `foes.nearby(radius=2)`

**Storm** — `storm.active`, `storm.danger`, `storm.border`, `storm.safe_zone_center()`

## Winning Strategies

Follow this priority ladder (battle-tested across thousands of matches):

1. **Escape storm** — storm damage is guaranteed and unavoidable
2. **Rest when broke** — energy < 15? Rest. No exceptions
3. **Finish kills** — adjacent enemy HP <= your attack_power? Kill them NOW
4. **Energy denial** — adjacent low-HP enemy likely resting? Attack them (they gain +5 HP but lose -25 HP net)
5. **Defend when threatened** — adjacent attacker + you're below 40 HP? Defend (take 15 instead of 25)
6. **Chase wounded** — enemy below 50 HP within range? Close distance
7. **Drift center** — pre-position toward where the safe zone will be
8. **Randomize idle** — no clear priority? Random move or defend

**Key insights:**
- Defend-counter beats pure aggro: defend one round (take 15), attack next (deal 25). Net +10 HP advantage per exchange.
- Enemy energy is NOT visible. Low HP often means they need to rest — punish it.
- Storm is deterministic. Pre-position, don't react.
- The Watcher (adaptive boss) reads action patterns. Randomize your idle behavior to defeat its prediction engine.

## Example: Simple Bot (5 lines)

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

## Example: Advanced Bot (Priority Ladder)

```python
BOT_NAME = "Tactician"
BOT_EMOJI = "🧠"
BOT_BIO = "Plays the priority ladder"

import random

def decide(state):
    from agentgrounds.wars.helpers import Me, Enemies, Storm
    me = Me(state)
    foes = Enemies(state)
    storm = Storm(state)

    # 1. Escape storm
    if storm.danger:
        return me.flee_storm()

    # 2. Rest when broke
    if me.energy < 15:
        return me.rest()

    # 3. Finish kills
    if me.can_kill_adjacent() and me.energy >= 10:
        return me.attack(me.weakest_adjacent())

    # 4. Energy denial — attack low-HP adjacent enemies (likely resting)
    for e in me.adjacent_enemies():
        if e["hp"] < 40 and me.energy >= 10:
            return me.attack(e)

    # 5. Defend when threatened
    if me.threatened() and me.energy >= 10:
        return me.defend()

    # 6. Chase wounded
    wounded = foes.wounded(threshold=50)
    if wounded and me.energy >= 20:
        target = min(wounded, key=lambda e: me.dist_to(e))
        if me.dist_to(target) <= 4:
            return me.move_toward(target)

    # 7. Drift center
    cx, cy = state["grid_size"] // 2, state["grid_size"] // 2
    if abs(me.x - cx) + abs(me.y - cy) > 2:
        return me.move_toward((cx, cy))

    # 8. Randomize idle (defeats pattern prediction)
    return random.choice([me.defend(), me.rest(),
                          ("move", random.choice(["north","south","east","west"]))])
```

## Your Task

Write a Python file following the bot format above. Implement a competitive `decide(state)` function using the strategies described. Return ONLY the complete Python file, no explanation.
