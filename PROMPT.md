# NPC Wars — Bot Builder Prompt

You are writing a competitive bot for NPC Wars, a battle royale where bots fight on a grid. All bots act simultaneously each round. Last bot standing wins. Your bot is a single Python file.

## Bot File Format

```python
BOT_NAME = "MyBot"
BOT_EMOJI = "🤖"
BOT_BIO = "Short description of strategy"

def decide(state):
    # Your logic here
    return ("rest",)
```

`BOT_NAME`, `BOT_EMOJI`, and `BOT_BIO` are module-level strings. `decide(state)` is called every round and must return an action tuple.

## The State Dict

`decide(state)` receives this dict every round:

```python
state = {
    "me": {
        "x": 3, "y": 5,          # grid position (0-indexed)
        "hp": 80,                  # 0-100
        "energy": 60,              # 0-100
        "attack_power": 25,        # base + round scaling
        "score": 18,               # cumulative match score
        "momentum_tier": 1,        # 0-4, see Momentum System
        "momentum_name": "Momentum",  # tier display name
        "is_leader": False,        # True if you're the highest scorer
    },
    "enemies": [
        {"x": 7, "y": 2, "hp": 45, "emoji": "🎯", "name": "Rival",
         "score": 12, "momentum_tier": 1, "is_leader": True},
        # ... more living enemies
    ],
    "grid_size": 10,               # 10x10 grid
    "storm_border": 2,             # tiles from each edge that are storm
    "round": 15,                   # current round number
}
```

**Important:** Enemy energy is NOT visible. You can see position, HP, emoji, name, score, and momentum tier. Infer energy from behavior (low HP enemies are likely resting).

## Actions and Costs

Return one of these tuples from `decide(state)`:

| Action | Return Value | Energy Cost | Effect |
|--------|-------------|-------------|--------|
| Move | `("move", "north")` | 5 | Move 1 tile (north/south/east/west) |
| Attack | `("attack", "north")` | 10 | Deal damage to adjacent tile in that direction |
| Defend | `("defend",)` | 10 | Halve incoming damage this round |
| Rest | `("rest",)` | 0 | Recover +5 HP and +20 energy |

If your bot returns an invalid action or crashes, it defaults to rest.

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
| Starting HP | 100 (max 100) |
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
| Full HP | +2 | End round at 100 HP |
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

### Carryover

The match winner carries 50% of their final score into the next match, capped at 50 points. This means winning streaks build early momentum in follow-up matches.

### Strategy Tips

- **High momentum makes you a target** -- enemies can see your tier and score. Expect aggression.
- **Full HP rounds give +2 points** -- defending at full HP is efficient scoring.
- **Clean kills (+5 bonus) reward aggressive play** without taking damage in the same round.
- **Target high-momentum enemies** to deny their combat advantages (energy regen, damage boost).
- **Early kills snowball** -- 10 points per kill means 1-2 kills can push you to tier 1 quickly.
- **Target the leader** -- +20 bounty for killing the leader makes them a high-value target.
- **Leader bleeds energy** -- tier 3+ costs 5-8 energy/round. The leader must keep fighting or drain out.

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
