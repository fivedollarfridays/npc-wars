# Agent Wars v2 — One-Year Strategic Proposal

> **Date:** 2026-03-18
> **Status:** Draft
> **Scope:** Complete game redesign targeting March 2027
> **Premise:** Wars is the flagship. Every design decision here becomes the template for the entire Agent Grounds platform.

---

## Executive Summary

Agent Wars today is a strong simulation engine with a weak game identity. Bots are interchangeable. There's no attachment, no progression, no reason to return tomorrow. The core loop (write code, fight, watch) works but lacks the depth that creates a competitive scene.

This proposal redesigns Wars around five interlocking systems that transform it from a coding sandbox into a competitive game with lasting engagement. Each system amplifies the central thesis: **your Python file is your character sheet.**

The five components:

1. **Identity System** — ANSI character rendering with visual state feedback
2. **Stat Allocation** — Four-stat build system creating emergent archetypes
3. **Combat Overhaul** — D&D-inspired probabilistic attack resolution
4. **Progression Engine** — Level-gated code capacity and ability unlocks
5. **Custom Abilities** — Player-authored power-ups with constrained budgets

Supporting infrastructure: terrain maps, camera/viewer evolution, balance framework.

---

## Component 1: Identity System

### Problem

Emoji characters are a visual dead end. They carry no game state, support no progression feedback, and create no player attachment. A bot at 100 HP looks identical to one at 5 HP. A tier 4 leader looks the same as a fresh spawn except for a label in the roster.

### Strategic Goal

Every bot should be visually distinct AND visually readable. A glance at the grid should tell you who's winning, who's wounded, who's dangerous, and who's the leader — without reading the roster.

### Design

#### Character Glyphs

Players choose a single Unicode glyph from an approved set (box-drawing, geometric shapes, symbols, card suits, arrows, stars, etc.). This replaces emoji.

```python
BOT_GLYPH = "◆"    # Player's chosen identity
```

Approved glyph categories:
- Geometric: `◆ ◇ ● ○ ■ □ ▲ △ ▼ ▽ ★ ☆ ◈ ◉`
- Symbols: `⚔ ⚡ ☠ ♠ ♣ ♥ ♦ ⬥ ⬡ ⬢ ☗ ☖`
- Arrows: `➤ ⮞ ⮝ ⮟ ⮜`
- Custom Unicode block (expandable)

Glyphs are single-width characters. No multi-cell characters — the grid stays clean.

#### Dynamic Rendering Layer

The glyph itself is fixed. Everything around it is dynamic:

**Color encoding (foreground):**

| HP Range | Color | ANSI |
|----------|-------|------|
| 75-100% | Bright white | `\033[97m` |
| 50-74% | Green | `\033[32m` |
| 25-49% | Yellow | `\033[33m` |
| 1-24% | Red | `\033[31m` |
| Dead | Dim gray | `\033[90m` |

**Background encoding (class archetype):**

| Primary Stat | Background Hint | Meaning |
|-------------|----------------|---------|
| POWER | Dim red | Damage dealer |
| SPEED | Dim cyan | Mobile/evasive |
| ARMOR | Dim blue | Defensive |
| MIND | Dim magenta | Energy/ability focused |

Background is subtle — just enough to create visual grouping without noise.

**Aura rendering (adjacent cells):**

Current aura system extends to encode more state:

| State | Aura Style | Adjacent Cell Render |
|-------|-----------|---------------------|
| Momentum tier 1-2 | None | — |
| Momentum tier 3 | Warm glow | `·` in yellow |
| Momentum tier 4 | Intense glow | `·` in bold red |
| Leader | Crown particles | `·` replaced with dim `♦` |
| Custom ability ready | Pulse | Alternating dim/bright on sub-frames |
| Wounded (<25%) | Flicker | Character dims every other frame |
| Defending | Shield outline | Adjacent cells show `░` |

#### Death Animation (Terminal)

On elimination, the character doesn't just disappear. Over 2-3 sub-frames:
1. Glyph inverts (background/foreground swap)
2. Glyph dims
3. Glyph replaced with `×` in dim gray, then empty

In the browser viewer: particle explosion, screen shake, kill cam.

### Technical Scope

| Work Item | Estimate | Dependencies |
|-----------|----------|-------------|
| Glyph registry + validation | S | None |
| Renderer color-by-HP | M | None |
| Renderer background-by-class | M | Component 2 (stat allocation) |
| Extended aura system | M | Existing overlay.py |
| Death animation sub-frames | M | Existing action frame system |
| Viewer canvas equivalents | L | Viewer refactor |
| PROMPT.md + bot format update | S | All above |

### Risk

Players emotionally attached to emoji. **Mitigation:** Support emoji as glyph choices. `BOT_GLYPH = "🤖"` still works — it's just rendered differently in the surrounding system.

---

## Component 2: Stat Allocation

### Problem

Every bot starts with identical stats (100 HP, 100 energy, 25 attack, 0 defense). The only differentiation is decision logic. This means the game has one viable "build" and the meta is purely about action sequencing. There are no interesting build decisions, no counter-building, no archetype diversity.

### Strategic Goal

Create a stat allocation system where the bot file defines not just behavior but identity. Two bots with identical `decide()` logic but different stat allocations should play differently and have different matchup profiles. The meta should have multiple viable archetypes with rock-paper-scissors dynamics.

### Design

#### Four Stats, 100-Point Budget

```python
# Bot file — stat allocation
POWER = 25    # Attack damage, crit multiplier
SPEED = 25    # Action priority, movement range, dodge chance
ARMOR = 25    # Max HP scaling, damage reduction, CC resistance
MIND = 25     # Max energy, energy regen, ability potency
```

Default is 25/25/25/25 (identical to current game). Any allocation that sums to 100 is valid. Minimum 5 per stat (no dump stats to zero).

#### Stat Effects

**POWER (5-60)**

| POWER | Min Damage | Max Damage | Crit Multiplier |
|-------|-----------|-----------|-----------------|
| 5 | 8 | 12 | 1.2x |
| 15 | 14 | 20 | 1.4x |
| 25 | 20 | 30 | 1.5x |
| 40 | 28 | 42 | 1.8x |
| 60 | 38 | 58 | 2.2x |

POWER creates damage variance. High-POWER bots are scary but not guaranteed — they might roll 28 or they might roll 42. Low-POWER bots are predictable but weak.

**SPEED (5-60)**

| SPEED | Initiative Bonus | Move Range | Dodge Chance | Dash Range |
|-------|-----------------|------------|-------------|------------|
| 5 | -3 | 1 | 0% | 1 |
| 15 | -1 | 1 | 5% | 1 |
| 25 | 0 | 1 | 10% | 2 |
| 40 | +2 | 2 | 18% | 3 |
| 60 | +5 | 2 | 28% | 4 |

SPEED determines who acts first in simultaneous resolution (initiative), whether you can dodge attacks, and movement range. High-SPEED bots control spacing — they choose engagements.

**ARMOR (5-60)**

| ARMOR | Max HP | Damage Reduction | CC Resistance |
|-------|--------|-----------------|---------------|
| 5 | 70 | 0 | 0% |
| 15 | 85 | 2 | 10% |
| 25 | 100 | 4 | 20% |
| 40 | 125 | 7 | 35% |
| 60 | 160 | 12 | 55% |

ARMOR buys survivability. High-ARMOR bots are walls — they absorb punishment and resist crowd control (taunt, knockback). But they deal less damage and move slower.

**MIND (5-60)**

| MIND | Max Energy | Energy Regen | Ability Potency | Power-Up Cooldown Reduction |
|------|-----------|-------------|----------------|---------------------------|
| 5 | 60 | 12 | 70% | 0% |
| 15 | 80 | 16 | 85% | 0% |
| 25 | 100 | 20 | 100% | 0% |
| 40 | 130 | 26 | 125% | 15% |
| 60 | 170 | 34 | 160% | 30% |

MIND is the utility stat. High-MIND bots have deep energy pools, strong abilities, and can use power-ups more frequently. They win attrition fights.

#### Emergent Archetypes

No hard classes. These emerge from stat allocation:

| Build | Stats | Playstyle | Weakness |
|-------|-------|-----------|----------|
| **Brawler** | 40/15/35/10 | High damage, tanky, slow | Gets kited, runs out of energy |
| **Assassin** | 35/40/10/15 | Burst damage, fast, fragile | Dies to tanks, punished if caught |
| **Tank** | 10/10/55/25 | Massive HP, absorbs everything | Low threat, ignored until last |
| **Controller** | 15/25/15/45 | Ability spam, energy denial | Low HP, dies to focused aggro |
| **Duelist** | 30/30/20/20 | Balanced, adaptive | No overwhelming advantage |
| **Glass Cannon** | 55/20/5/20 | Extreme burst, one-shot potential | 70 HP, dies to a stiff breeze |

#### State Dict Exposure

Bots see their own stats and can infer enemy builds:

```python
state["me"]["power"] = 35
state["me"]["speed"] = 40
state["me"]["armor"] = 10
state["me"]["mind"] = 15
state["me"]["dodge_chance"] = 0.18
state["me"]["damage_range"] = (24, 36)

# Enemies — you can see their HP (reveals ARMOR) but not exact stats
state["enemies"][0]["max_hp"] = 125   # they have high ARMOR
state["enemies"][0]["speed_class"] = "fast"  # qualitative hint
```

Enemy stats are partially hidden. You see effects (high HP, fast movement) but not exact numbers. Deduction is part of the game.

### Balance Framework

Every two weeks, run 10,000-match simulations across all archetype combinations. Target:
- No single archetype exceeds 55% win rate against the field
- Every archetype has at least one favorable matchup (>55%) and one unfavorable (<45%)
- The balanced (25/25/25/25) build should sit at 48-52% — viable but not optimal

Tuning levers: stat scaling curves (the tables above). Adjusting breakpoints shifts the meta without changing game mechanics.

### Technical Scope

| Work Item | Estimate | Dependencies |
|-----------|----------|-------------|
| Stat budget validation in loader | S | None |
| Stat → derived values calculator | M | None |
| Bot class refactor (variable starting stats) | M | None |
| Combat integration (damage ranges, dodge, initiative) | L | Component 3 |
| State dict exposure (own stats, enemy hints) | M | None |
| Balance simulation harness | M | Existing sim runner |
| PROMPT.md stat guide | M | All above |

### Risk

Overwhelming new players with four stats to choose. **Mitigation:** Default allocation (25/25/25/25) matches current game exactly. The template picker (Component 4) suggests allocations: "Aggressive? Try 40/25/15/20." Stat allocation is powerful but never required.

---

## Component 3: Combat Overhaul

### Problem

Current combat is deterministic and flat. 25 damage minus defense. No variance, no drama, no outplay potential. A bot that's going to lose knows it 3 rounds in advance. There are no clutch moments.

### Strategic Goal

Introduce meaningful combat variance that creates dramatic moments while keeping outcomes skill-influenced. Good bots should win more, but any fight should have a chance of producing an upset. The spectator should never know the outcome until it happens.

### Design

#### Attack Resolution

Replace flat damage with a roll-based system:

```
1. Attacker rolls: d20 + SPEED_modifier + situational_bonuses
2. Compare to defender's Armor Class (AC):
   AC = 10 + (ARMOR / 10) + terrain_bonus + defend_action_bonus
3. If roll >= AC: hit
4. If roll >= AC + 10: critical hit
5. If roll < AC: miss (0 damage)
```

**Defender can dodge (SPEED-based):**
```
After a hit is confirmed, defender rolls dodge:
dodge_roll = random.random() < dodge_chance
If dodged: damage halved (not negated — partial dodge)
```

**Damage on hit:**
```
base = random.randint(min_damage, max_damage)  # from POWER stat
if critical: base *= crit_multiplier            # from POWER stat
final = max(0, base - damage_reduction)         # from ARMOR stat
```

#### Situational Modifiers

| Situation | Modifier | Strategic Implication |
|-----------|----------|---------------------|
| High ground | +2 to hit, +15% damage | Position matters |
| Flanking (ally adjacent to target) | +3 to hit | Coordination rewarded |
| Target is resting | +5 to hit | Punish recovery |
| Target is defending | +5 AC, halve damage | Defend is strong but costs a turn |
| Attacker taunted | -2 to hit vs non-taunter | Taunt creates real disruption |
| Back attack (target moved away last round) | +3 to hit, +25% damage | Fleeing has a cost |
| Storm zone | -2 to hit (both parties) | Storm fights are chaotic |

All modifiers are visible in the state dict. Bots can calculate their exact hit probability before choosing to attack.

#### State Dict: Combat Intelligence

```python
state["me"]["hit_chance"] = {
    "🎯": {"chance": 0.72, "crit": 0.12, "expected_damage": 18.4},
    "🐢": {"chance": 0.45, "crit": 0.05, "expected_damage": 6.2},
}
state["me"]["incoming_threat"] = {
    "🎯": {"chance": 0.65, "expected_damage": 22.1},
}
```

This is the strategic depth layer. A simple bot ignores it and attacks the closest enemy. A sophisticated bot calculates expected value across all targets and picks the highest EV play. A masterful bot factors in future rounds — "If I kill the kiter now, the tank can't hide behind them next round."

#### Combat Pacing

D&D can be slow. Wars needs to be fast. Design targets:

- Average match: 25-35 rounds (current: 20-40, roughly same)
- Average bot elimination: round 12-20
- Time-to-kill for equal builds: 4-6 rounds of sustained combat
- Critical hit frequency: ~10-15% of attacks (enough to be exciting, not dominant)
- Miss frequency: 15-30% depending on builds (enough to create drama, not frustration)

#### Damage Types (Future Extension Point)

Not in year-one scope, but the architecture should support it:
- **Physical** (from POWER) — reduced by ARMOR
- **Energy** (from MIND) — reduced by MIND resistance
- **True** (from crits, power-ups) — ignores reduction

Leaving this hook allows future expansion without a combat rewrite.

### Technical Scope

| Work Item | Estimate | Dependencies |
|-----------|----------|-------------|
| Roll-based hit resolution | L | Component 2 (stats exist) |
| Dodge system | M | Component 2 (SPEED stat) |
| Damage range calculation | M | Component 2 (POWER stat) |
| Situational modifier engine | M | Component 5 (terrain) |
| Hit probability calculator for state dict | M | All above |
| Combat event schema update (roll, crit, dodge in events) | M | None |
| Renderer: miss/dodge/crit visual feedback | M | Identity system |
| Viewer: combat animations for new events | L | Viewer refactor |
| Balance tuning (10K sim runs) | M | Sim runner exists |
| PROMPT.md combat guide | M | All above |

### Risk

RNG frustration — "I lost because of bad rolls." **Mitigation:** Variance is bounded. A 60-POWER bot hitting a 5-ARMOR bot will connect 85%+ of the time. Rolls create drama at the margins, not at the outcome level. Over a 30-round match, skill dominates. Over a single round, anything can happen. That's what makes it watchable.

---

## Component 4: Progression Engine

### Problem

No reason to come back. A bot written today is the same bot tomorrow. There's no growth arc, no "I'm almost at the next unlock," no investment that compounds over time. Without progression, Wars is a toy you play once, not a game you play for months.

### Strategic Goal

Create a progression system where playing more (and playing well) expands what your bot can do — but never makes it automatically stronger. Progression unlocks capability, not power. A level 1 bot with perfect logic beats a level 25 bot with bad logic.

### Design

#### Experience and Leveling

```
XP earned per match:
  Base:           10 XP (participation)
  Per kill:       15 XP
  Per round survived: 2 XP
  Win bonus:      50 XP
  Placement:      2nd = 25 XP, 3rd = 15 XP
  First blood:    20 XP bonus
  Leader bounty:  25 XP bonus
```

XP is account-level, not bot-level. You level up your **pilot profile**, not individual bots. This means you can experiment with new bots without losing progress.

#### Level Progression Table

| Level | Total XP | Line Budget | New Actions | Unlocked Callbacks | Milestone |
|-------|----------|------------|-------------|-------------------|-----------|
| 1 | 0 | 50 | move, attack, rest, defend | `decide(state)` | Starting out |
| 2 | 100 | 60 | — | — | |
| 3 | 250 | 75 | ranged_attack | — | First new action |
| 5 | 600 | 100 | dash | `on_kill(state, victim)` | Mobility unlock |
| 8 | 1,200 | 125 | taunt | `setup(match_info)` | Pre-match config |
| 10 | 1,800 | 140 | — | — | Veteran threshold |
| 12 | 2,800 | 150 | trap | `react(state, event)` | Reactive play |
| 15 | 4,500 | 175 | — | — | |
| 18 | 7,000 | 200 | use_ability | `power_up()` definition | Custom ability 1 |
| 22 | 11,000 | 225 | — | `evolve(stats, history)` | Between-match adaptation |
| 25 | 15,000 | 250 | — | Second `power_up()` slot | Custom ability 2 |
| 30 | 25,000 | 300 | — | — | Master tier |

**XP curve:** ~10 matches to level 2, ~50 matches to level 5, ~150 to level 10, ~500 to level 18. First unlock feels fast. Late unlocks require real commitment.

#### Callback Definitions

**`decide(state) → action`** (Level 1)
The core function. Called every round. Returns an action tuple.

**`on_kill(state, victim) → action | None`** (Level 5)
Called immediately when your bot kills an enemy. Can return a bonus action (move only — no free attacks). Returns None for no bonus action. This lets assassin builds disengage after a kill.

**`setup(match_info) → config`** (Level 8)
Called once before the match starts. Receives: `{"players": [...], "map": "arena_3", "terrain": {...}}`. Returns a config dict that can adjust your stat allocation by ±5 points per stat (must still sum to 100). This lets you counter-build based on the lobby.

**`react(state, event) → action | None`** (Level 12)
Called when a specific event targets you (incoming attack, taunt, trap trigger). Can return a defensive action (defend, dash, use_ability). Costs double energy. This creates interrupt/counter-play dynamics.

**`power_up() → ability_definition`** (Level 18)
Defines a custom ability. See Component 5.

**`evolve(stats, history) → stat_adjustment`** (Level 22)
Called between matches in a series. Receives your cumulative stats and match history. Can shift up to 10 stat points between stats. This lets bots adapt across a tournament — if you keep losing to tanks, shift points from POWER to SPEED.

#### Line Budget Enforcement

The line budget is enforced at load time via AST counting:
- Only `decide()`, callbacks, and helper functions count
- Module-level constants (POWER, SPEED, etc.) don't count
- Import statements don't count
- Comments and docstrings don't count
- Empty lines don't count

This means actual logic lines. 50 lines of logic is a real bot. 300 lines of logic is a sophisticated system.

#### Matchmaking Brackets

To prevent level 25 bots from crushing level 1 bots:

| Bracket | Level Range | Available Actions | Power-Ups |
|---------|------------|-------------------|-----------|
| **Rookie** | 1-4 | move, attack, rest, defend | None |
| **Veteran** | 5-11 | + ranged, dash, taunt | None |
| **Elite** | 12-17 | + trap, react callback | None |
| **Champion** | 18+ | All actions, power-ups | Yes |
| **Open** | Any | All unlocks at player's level | Yes |

Ranked play uses brackets. Casual play uses Open. Tournaments specify their bracket.

### Technical Scope

| Work Item | Estimate | Dependencies |
|-----------|----------|-------------|
| XP/level system + persistence (SQLite) | M | None |
| Line budget enforcer (AST counter) | M | Existing scanner |
| Action unlock gating in sandbox | M | None |
| Callback dispatch system in game loop | L | None |
| `on_kill` callback integration | M | Game loop |
| `setup` pre-match hook | M | Game loop |
| `react` interrupt system | L | Combat overhaul |
| `evolve` between-match hook | M | Tournament system |
| Matchmaking bracket logic | M | XP system |
| CLI: `agentgrounds wars profile` command | S | XP system |
| Post-match XP summary display | S | XP system |
| PROMPT.md progression guide | M | All above |

### Risk

Progression creates a barrier for new players. **Mitigation:** Three approaches:
1. The Rookie bracket is the full game from today — 4 actions, 50 lines, pure strategy. It's complete and fun on its own.
2. AI-generated bots auto-set to the player's level — `generate --auto` respects your line budget.
3. Progression is fast early — you unlock ranged_attack by match ~25, which takes a single afternoon.

Second risk: smurf accounts. **Mitigation:** IP/device fingerprinting for ranked. Casual play doesn't care.

---

## Component 5: Custom Abilities (Power-Ups as Code)

### Problem

Every bot at the same level has the same toolkit. There's no way to surprise your opponent with something they haven't seen before. The meta becomes solved because all options are public knowledge.

### Strategic Goal

Give players a constrained design space to create unique abilities. Your custom ability is YOUR signature move — other players know its name and description but not its exact parameters. This adds a prediction/deduction layer to the meta-game.

### Design

#### Ability Definition

At level 18, players define a `power_up()` function:

```python
def power_up():
    return {
        "name": "Void Step",
        "description": "Blink through shadows to strike from behind",
        "type": "teleport_attack",
        "budget_allocation": {
            "potency": 20,    # damage/heal amount
            "range": 15,      # tiles of reach
            "duration": 0,    # rounds of effect
            "area": 0,        # tiles of AoE
            "cooldown": 15,   # spent on reducing cooldown
        },
        "energy_cost": 25,
    }
```

#### Budget System

Every ability has a **50-point budget** distributed across five dimensions:

| Dimension | Effect Per Point | Example at 25 pts | Example at 50 pts |
|-----------|-----------------|-------------------|-------------------|
| **Potency** | +1.2 damage/heal per point | 30 damage | 60 damage |
| **Range** | +0.12 tiles per point | 3 tiles | 6 tiles |
| **Duration** | +0.2 rounds per point | 5 rounds | 10 rounds |
| **Area** | +0.08 radius per point | 2-tile radius | 4-tile radius |
| **Cooldown** | -0.2 rounds per point | 5-round CD (from base 10) | 0-round CD (no cooldown, but weak) |

Base cooldown is 10 rounds. Base energy cost is 20. Players can increase energy cost to 30/40 for +10/+20 bonus budget points (risk/reward — expensive abilities are stronger but drain you faster).

#### Ability Types

Players choose from a menu of effect types. Each type uses the budget differently:

| Type | Primary Dimension | Effect |
|------|------------------|--------|
| **damage** | Potency | Deal damage to target(s) |
| **heal** | Potency | Restore own HP |
| **lifesteal** | Potency (split) | Deal damage, heal for 50% of amount |
| **teleport** | Range | Move instantly to target location |
| **teleport_attack** | Range + Potency | Teleport to enemy + strike |
| **shield** | Duration + Potency | Absorb next N damage for M rounds |
| **slow** | Duration + Area | Reduce enemy SPEED in radius for M rounds |
| **reveal** | Range + Duration | See exact enemy stats for M rounds |
| **knockback** | Range + Potency | Push enemy N tiles + deal damage |
| **trap** | Duration + Area | Place invisible zone, triggers on entry |
| **buff_self** | Duration + Potency | Boost own stat temporarily |
| **debuff_target** | Duration + Potency | Reduce target stat temporarily |

#### Visibility Rules

What opponents see:

| Information | Visible? | When |
|-------------|----------|------|
| Ability name | Yes | Always (in state dict) |
| Ability description | Yes | Always |
| Ability type | Yes | After first use in the match |
| Budget allocation | No | Never |
| Cooldown status | Partial | "ready" / "on cooldown" (not exact rounds) |
| Energy cost | No | Never (but inferable from energy drops) |

This creates an information asymmetry game. You know their ability is called "Void Step" and it's a teleport_attack. You don't know if it hits for 20 or 60, or if its range is 2 tiles or 6. After they use it once, you can estimate — but they might have allocated differently than you think.

#### State Dict: Ability Information

```python
state["me"]["ability"] = {
    "name": "Void Step",
    "ready": True,
    "cooldown_remaining": 0,
    "times_used": 2,
}
state["enemies"][0]["ability"] = {
    "name": "Iron Fortress",
    "ready": False,  # on cooldown
    "type": "shield",  # revealed after first use
    "times_used": 1,
}
```

#### Using Abilities in `decide()`

```python
def decide(state):
    if state["me"]["ability"]["ready"]:
        target = find_best_target(state)
        if should_use_ability(state, target):
            return ("use_ability", target["emoji"])
    # ... normal decision logic
```

The action `("use_ability", target)` triggers the ability. For self-targeted abilities (heal, shield, buff_self): `("use_ability", "self")`. For area abilities: `("use_ability", x, y)`.

#### Second Ability Slot (Level 25)

At level 25, players define a second `power_up`:

```python
def power_up():
    return [
        {"name": "Void Step", ...},       # Ability 1
        {"name": "Shadow Veil", ...},      # Ability 2
    ]
```

Usage: `("use_ability", target, 0)` for ability 1, `("use_ability", target, 1)` for ability 2.

Two abilities with independent cooldowns create combo potential. "Void Step in, then Shadow Veil for stealth" becomes a playstyle.

### Technical Scope

| Work Item | Estimate | Dependencies |
|-----------|----------|-------------|
| Ability definition schema + validation | M | None |
| Budget system calculator | M | None |
| 12 ability type implementations | XL | Combat system |
| Cooldown tracking per bot | S | None |
| Ability resolution in combat phases | L | Component 3 |
| MIND potency scaling integration | M | Component 2 |
| State dict: ability exposure (partial info) | M | None |
| Viewer: ability FX per type | L | Viewer refactor |
| Terminal: ability feed events | M | Existing feed system |
| AI generation: ability-aware PROMPT.md | M | All above |
| Balance: ability type simulation | L | Sim runner |

### Risk

Degenerate abilities that break the game. **Mitigation:**
1. Budget cap is hard — you can't create a 50-damage, 6-range, no-cooldown nuke because the math doesn't allow it
2. Energy cost floor (20) means abilities can't be spammed
3. Cooldown floor (2 rounds even at max investment) prevents permanent effects
4. Type menu is fixed — players combine parameters, they don't invent new mechanics
5. Bi-weekly balance sims flag outliers for tuning

---

## Supporting Systems

### Terrain Maps

#### Map Pool (Year One: 5 Maps)

| Map | Layout | Favors | Key Feature |
|-----|--------|--------|-------------|
| **Arena** | Open field, no terrain | Brawlers, balanced builds | Pure combat, current game |
| **Fortress** | Central walls, 4 corridors | Tanks, trap users | Chokepoints force engagement |
| **Highlands** | Elevated center, water edges | Kiters, ranged builds | High ground advantage |
| **Maze** | Dense wall grid, many paths | Assassins, teleport abilities | Line-of-sight matters |
| **Storm Pit** | Small safe zone, fast storm | Glass cannons, aggressive builds | Quick elimination, high drama |

#### Terrain Types

| Terrain | Movement | Combat | Energy |
|---------|----------|--------|--------|
| **Open** | Normal | Normal | Normal |
| **Wall** | Blocked | Blocks ranged, blocks LoS | — |
| **Water** | -1 movement range | -2 to hit | No rest healing |
| **High Ground** | Normal | +2 to hit, +15% damage from above | Normal |
| **Cover** | Normal | +3 AC when behind | Normal |
| **Power Crystal** | Normal | Normal | +10 energy on first step |

#### State Dict: Terrain

```python
state["terrain"] = {
    "type": "fortress",
    "walls": [(3,2), (3,3), (3,4), ...],
    "water": [(0,5), (0,6), ...],
    "high_ground": [(5,5), (5,6), (6,5), (6,6)],
    "cover": [(2,4), (7,3)],
    "crystals": [(4,0), (4,9)],
}
state["me"]["on_terrain"] = "high_ground"
state["me"]["has_cover_from"] = ["north", "east"]
```

### Camera and Viewer

#### CLI Viewer Enhancements

| Feature | Description | Priority |
|---------|-------------|----------|
| Kill pause | 0.5s pause + highlight frame on elimination | P1 |
| Terrain rendering | Unicode box-drawing for walls, `≈` for water, `^` for hills | P1 |
| Post-match summary | Stats table with trends, printed after match | P1 |
| Ability usage feed | "[R12] ◆ used Void Step on ◇" in kill feed | P2 |
| Round-by-round rewind | `--round 15` flag on watch command | P3 |

#### Browser Viewer Overhaul

| Feature | Description | Priority |
|---------|-------------|----------|
| Smooth movement interpolation | Lerp between grid positions | P1 |
| Kill cam | 1.5s slow-mo on elimination, zoom to action | P1 |
| Ability FX | Per-type visual effects (teleport shimmer, shield bubble, etc.) | P1 |
| Screen shake | On crits, multi-kills, leader bounty | P2 |
| Auto-zoom | Camera tracks clusters of combat | P2 |
| Spectator mode: follow bot | Click a bot to track it | P2 |
| Generative sound | Web Audio API: impact, movement, ability, ambient | P3 |
| Picture-in-picture | Split view when action happens in 2 locations | P3 |

### Post-Match Experience

After every match, the CLI prints:

```
┌─────────────────────────────────────────────┐
│              MATCH COMPLETE                  │
│                                              │
│  Your Bot: ◆ Wraith (Assassin build)        │
│  Result:   2nd place — 3 kills, 22 rounds   │
│  Score:    52 pts (peaked: Tier 3)           │
│                                              │
│  ── Stats vs Lifetime Average ──            │
│  Win Rate:    35% → 38%  ▲ +3%             │
│  Avg Kills:   1.8 → 2.4  ▲ +33%           │
│  Avg Survived: R18 → R22  ▲ +22%           │
│  Damage/Round: 8.2 → 11.4 ▲ +39%          │
│                                              │
│  ── Matchup Profile ──                      │
│  vs Tank builds:   2W / 5L (28%)  ▼ weak   │
│  vs Speed builds:  4W / 2L (67%)  ▲ strong │
│  vs Mind builds:   3W / 3L (50%)  ─ even   │
│                                              │
│  ── Progression ──                          │
│  Level 7 → 8  (+85 XP)                     │
│  🔓 UNLOCKED: taunt action                  │
│  🔓 UNLOCKED: setup() callback              │
│  Next unlock: trap (Level 12, 1600 XP away) │
│                                              │
│  💡 Tip: You died to tanks 3x this session. │
│     Try shifting 5 pts from POWER → SPEED   │
│     to disengage after burst combos.         │
└─────────────────────────────────────────────┘
```

This is the diff. This is the game.

---

## Implementation Roadmap

> **Updated 2026-03-21** — Revised to reflect actual progress and new systems (equipment, traps, code-built characters) added since original proposal.

### Phase 1: Foundation (Q2 2026) — ✅ COMPLETE

**Goal:** Stat allocation + combat overhaul. The game feels different.

| Sprint | Focus | Status | PR |
|--------|-------|--------|-----|
| S25 | Momentum & scoring system | ✅ Done | #20 |
| S26 | King of the Hill momentum refinement | ✅ Done | #21 |
| S27 | Stat budget system (POWER/SPEED/ARMOR/MIND) | ✅ Done | #22 |
| S28 | Roll-based combat overhaul (d20 mechanics) | ✅ Done | #23 |
| S29 | Dodge, modifiers, initiative, hit probability | ✅ Done | #24 |
| S30 | Visual identity (glyphs, HP colors, auras) | ✅ Done | #25 |
| S31 | Balance tuning + passivity plague + Phase 1 gate | ✅ Done | #27 |

**Outcomes:** 6 archetypes viable (45-55% win rates), d20 combat with crits/dodges/momentum, visual identity system, 3000+ tests.

### Phase 2: Depth (Q3 2026) — ✅ COMPLETE

**Goal:** Progression + equipment + terrain + abilities. The game has build diversity and a reason to return.

| Sprint | Focus | Status | PR |
|--------|-------|--------|-----|
| S32 | XP and leveling system (30 levels, SQLite profiles) | ✅ Done | #27 |
| S33 | Callback infrastructure + trap action | ✅ Done | #28 |
| S34 | Trap polish & balance (feed FX, on_kill, trapper bot) | ✅ Done | #29 |
| S35 | Equipment system (weapon/armor/accessories, 40-credit budget) | ✅ Done | #30 |
| S36 | Tactical items + ability system (power_up, evolve callbacks) | ✅ Done | #31 |
| S37 | Terrain engine (5 maps, walls, water, high ground, cover) | ✅ Done | #32 |
| S38 | Post-match experience (diff view, matchup profiles, progression) | ✅ Done | #33 |
| S39 | Phase 2 balance gate (1000-match sim, feed refactor) | ✅ Done | #34 |

**Outcomes:** 3-axis build system (stats + equipment + abilities), 5 terrain maps, post-match diff view, archetype classification, 13 builtin bots, 3600+ tests. Balance: no bot >60%, no archetype >60%.

**New since original proposal:**
- **Equipment system (S35):** D&D-inspired gear slots (weapon, armor, 2 accessories, tactical) with 40-credit budget. Inspired by NPC Race's component system. Stats = who you are, equipment = what you carry. Weapons modify to-hit/damage, armor modifies DR/energy costs, accessories add stat bonuses.
- **Trap action (S33-34):** Hidden zones placed on tiles, trigger on enemy movement. POWER-scaled damage, 3-round cooldown. Fully rendered in CLI feed/overlay.
- **Tactical items (S36):** Activated equipment abilities (Battle Cry, Fortify, Teleport, Overdrive) bridging equipment into the ability system.
- **Terrain (S37):** Moved from S35-36 to S37. Not conflicting with equipment — terrain is grid-layer, equipment is combat-layer. Both additive.

**Exit criteria:** Players have meaningful build decisions across 3 axes (stats, equipment, abilities). Terrain creates positional strategy. Post-match diff makes every match feel like progress.

### Phase 3: Character & Spectacle (Q4 2026) — 8 Weeks

**Goal:** Code-built characters + viewer overhaul. The game is watchable and characters are iconic.

| Sprint | Focus | Key Deliverables |
|--------|-------|-----------------|
| S40 | **Code-built character system** | Stats + equipment → visual traits. Engine generates character appearance from code. Bulk for armor, sharp edges for speed, weapon silhouettes. |
| S41 | Browser viewer overhaul | Canvas character rendering (not emoji), smooth interpolation, terrain rendering |
| S42 | Character customization | Paid cosmetic layer on functional visuals. Players buy how their plate armor *looks*, not what it does. |
| S43 | Kill cam + screen shake + death animations | Spectacle layer — crits shake, multi-kills zoom, deaths explode |
| S44 | Generative sound | Web Audio API: impact FX, ability sounds, movement, ambient per terrain |
| S45 | Matchmaking brackets | Rookie/Veteran/Elite/Champion/Open, bracket enforcement |
| S46 | Tournament system | Claude vs GPT vs Gemini, automated iteration, spectator broadcast |
| S47 | Phase 3 gate | Full spectator experience validation |

**New since original proposal:**
- **Code-built characters (S40):** Characters whose look informs their function. The code builds the character, the system interprets it visually. A tank looks tanky, an assassin looks fast. Replaces emoji rendering in browser viewer.
- **Character customization (S42):** Monetization path — players pay for cosmetic overrides on their functional visual. Down the line: fully custom character appearance.
- **Original Phase 3 (abilities)** compressed into Phase 2 (S36). 4 ability types + tactical items instead of 12 types across 8 sprints.

**Exit criteria:** Characters are visually distinct and readable. The browser viewer is a spectator sport. Sound enhances drama. Tournaments attract viewers.

### Phase 4: Platform (Q1 2027) — 6 Weeks

**Goal:** Server, social, SDK. The game is a product and a platform.

| Sprint | Focus | Key Deliverables |
|--------|-------|-----------------|
| S48 | Server layer | Upload endpoint, matchmaking lobby, replay storage |
| S49 | Diff view | Lifetime avg vs current game, GitHub-style stat diff — "the diff IS the game" |
| S50 | Leaderboard + ranked mode | `agentgrounds wars upload`, `agentgrounds wars leaderboard` |
| S51 | Discord integration | Match announcements, leaderboard bot, challenge command |
| S52 | NPC-SDK extraction | Shared infra for Racing, Kitchen, etc. (extract after 2 working games) |
| S53 | Launch polish | Onboarding flow, template picker by archetype, documentation, marketing |

**Exit criteria:** The full create → fight → watch → diff → iterate → upload → compete loop works end-to-end in CLI and browser. The game is fun to watch. The game is fun to play. The game is fun to talk about.

---

## Success Metrics (March 2027)

| Metric | Target | Why It Matters |
|--------|--------|---------------|
| Unique bot uploads (monthly) | 500+ | People are creating |
| Matches played (monthly) | 10,000+ | People are fighting |
| Median session length | 45+ min | People are hooked |
| Return rate (7-day) | 40%+ | People come back |
| Level 10+ players | 200+ | People progress |
| Custom abilities created | 100+ unique | People design |
| Discord members | 1,000+ | Community exists |
| AI tournament viewers | 5,000+ per event | Spectator sport works |
| Archetype win rate spread | 45-55% | Game is balanced |
| Player-reported "fun" (survey) | 8/10+ | The point of everything |

---

## Open Questions

1. **Ranked vs Casual split** — Do we need both at launch, or is casual with hidden MMR sufficient for year one?
2. **Team modes** — 2v2 or 3v3 with `ally` in state dict. Huge design space but doubles the work.
3. **Seasons and resets** — Should the leaderboard reset quarterly? Should XP persist forever?
4. **Marketplace** — Can players share/sell bot strategies? Ethical and gameplay implications.
5. **Spectator betting** — Prediction market on match outcomes. Engagement booster or distraction?
6. **Mobile viewer** — Responsive canvas or native app? Year-one scope or year-two?
7. **Modding** — Can players create custom maps? Custom ability types? Where's the line?

---

## What This Doesn't Change

The fundamentals stay:
- Bot file format: `decide(state) → action` (Python, single file)
- CLI-first: every interaction scriptable, parseable, automatable
- Deterministic with seed: same seed, same inputs, same outcome (rolls use match RNG)
- Agents-developing-agents: the meta-loop where AI improves its own bots
- PROMPT.md as the knowledge moat: domain expertise baked into the generation prompt
- Free core gameplay: progression, abilities, ranked — all free
- Security model: AST scanning, sandboxed execution, no networking
