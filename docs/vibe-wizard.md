# NPC Wars Bot Creation Guide

Three ways to build a bot, from zero-code to full control.

---

## Level 1: Zero-Code Wizard (easiest)

The wizard generates a complete bot file from interactive prompts. No coding required.

### Quick Start

```bash
python wizard.py
```

You will be prompted for:

1. **Bot name** -- alphanumeric + underscores, 1-20 characters (e.g. `MyBot`)
2. **Emoji** -- a single emoji for the arena display (e.g. `🤖`)
3. **Author** -- your name
4. **Playstyle** -- choose from five presets:
   - `aggro` -- chase and kill everything
   - `tank` -- defend, counter, outlast
   - `kiter` -- stay at range, poke wounded
   - `opportunist` -- conserve energy, strike when advantageous
   - `chaos` -- pure random mayhem
5. **Aggression slider** (1-10) -- how eagerly the bot attacks (1 = passive, 10 = berserker)
6. **Risk tolerance slider** (1-10) -- willingness to fight at low HP (1 = cautious, 10 = reckless)

The wizard writes a ready-to-run bot file to `bots/<name>.py`.

### Non-Interactive Mode

For scripting or CI:

```bash
python wizard.py --non-interactive \
  --name MyBot \
  --emoji "🤖" \
  --author alice \
  --style aggro \
  --aggression 7 \
  --risk 3
```

All flags are required in non-interactive mode. The bot file is written to `bots/mybot.py`.

### Validate Your Bot

```bash
python scripts/validate_bot.py bots/mybot.py
```

---

## Level 2: Vibes DSL (10 lines instead of 90)

The helpers DSL wraps the raw state dict with convenience classes so you can focus on strategy, not plumbing.

### Setup

Inside your `decide()` function, import the helpers:

```python
def decide(state):
    from npcwars.helpers import Me, Enemies, Storm

    me = Me(state)
    enemies = Enemies(state)
    storm = Storm(state)
```

The imports go **inside** `decide()` -- this is the recommended pattern for DSL bots.

### Complete Example: Cognify

A storm-aware opportunist that rests until it doesn't.

```python
"""NPC Wars Bot -- Cognify (vibes DSL example)"""

BOT_NAME = "Cognify"
BOT_EMOJI = "\U0001f9e0"
BOT_BIO = "rests until it doesn't"
BOT_AUTHOR = "kevin"


def decide(state):
    from npcwars.helpers import Me, Enemies, Storm

    me = Me(state)
    enemies = Enemies(state)
    storm = Storm(state)

    # P0: Storm escape
    if storm.danger:
        return me.flee_storm()

    adj = enemies.adjacent()
    killable = [e for e in adj if e["hp"] <= me.attack_power]

    # P1: Energy crisis
    if me.energy < 15 and not killable:
        return me.rest()

    # P2: Finish kills
    if killable:
        target = min(killable, key=lambda e: e["hp"])
        return me.attack(target)

    # P3: Defend or counter
    if adj:
        weakest = min(adj, key=lambda e: e["hp"])
        if me.hp <= 40 or len(adj) > 1:
            return me.defend()
        if weakest["hp"] <= 50:
            return me.attack(weakest)
        return me.defend()

    # P4: Rest when safe
    if me.energy < 30:
        return me.rest()

    # P5: Chase wounded
    if me.hp > 50 and me.energy >= 40:
        wounded = enemies.wounded(50)
        if wounded:
            target = min(wounded, key=lambda e: e["hp"])
            if me.dist_to(target) <= 4:
                return me.move_toward(target)

    # P6: Drift center
    return me.move_toward_center()
```

See `bots/example_vibes.py` for the runnable version.

---

## Level 3: Full Control (existing)

For maximum flexibility, work directly with the raw state dict and return action tuples.

### State Dict Format

Your `decide(state)` function receives:

```python
{
    "me": {
        "x": 5,           # grid column (0-indexed)
        "y": 5,           # grid row (0-indexed)
        "hp": 100,        # hit points (0-100)
        "energy": 100,    # energy (0-100)
        "attack_power": 25,
        "defense": 0,
    },
    "enemies": [
        {"name": "Foe", "emoji": "X", "x": 6, "y": 5, "hp": 80},
        ...
    ],
    "round": 1,          # current round number
    "grid_size": 10,     # arena is grid_size x grid_size
    "storm_border": 0,   # tiles consumed by storm on each edge
}
```

### Return Value

Return an action tuple. See the **Valid Actions** table below.

### Existing Examples

| File | Strategy |
|------|----------|
| `bots/example_aggro.py` | Chase closest, attack always |
| `bots/example_tank.py` | Defend-heavy, counter when adjacent |
| `bots/example_kiter.py` | Maintain range, poke wounded |
| `bots/example_random.py` | Random valid actions |
| `bots/template.py` | Blank starting point |

---

## API Reference

### Me

Create with `me = Me(state)`.

**Properties** (read-only):

| Property | Type | Description |
|----------|------|-------------|
| `x` | `int` | Grid column |
| `y` | `int` | Grid row |
| `hp` | `int` | Hit points |
| `energy` | `int` | Current energy |
| `attack_power` | `int` | Damage per attack |
| `defense` | `int` | Defense stat |
| `grid_size` | `int` | Arena dimension |
| `storm_border` | `int` | Storm tiles per edge |
| `round` | `int` | Current round |

**Actions** (return action tuples):

| Method | Returns | Description |
|--------|---------|-------------|
| `rest()` | `("rest",)` | Rest, restore energy |
| `defend()` | `("defend",)` | Defend, reduce incoming damage |
| `attack(enemy)` | `("attack", dir)` | Attack toward enemy |
| `flee_storm()` | `("move", dir)` | Move toward center (alias for `move_toward_center`) |
| `move_toward(target)` | `("move", dir)` | Move toward target (dict or (x,y) tuple) |
| `move_away_from(target)` | `("move", dir)` | Move away from target |
| `move_toward_center()` | `("move", dir)` | Move toward grid center |

**Awareness** (query methods):

| Method | Returns | Description |
|--------|---------|-------------|
| `dist_to(target)` | `int` | Manhattan distance to target |
| `adjacent_enemies()` | `list[dict]` | Enemies at distance 1 |
| `nearby_enemies(radius=2)` | `list[dict]` | Enemies within radius |
| `can_kill_adjacent()` | `bool` | Any adjacent enemy hp <= attack_power? |
| `weakest_adjacent()` | `dict or None` | Lowest-hp adjacent enemy |
| `threatened()` | `bool` | Adjacent enemies AND (hp<40 or outnumbered) |

### Enemies

Create with `enemies = Enemies(state)`.

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `count` | `int` | Number of living enemies |

**Query Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `closest()` | `dict or None` | Nearest enemy by manhattan distance |
| `weakest()` | `dict or None` | Lowest-hp enemy |
| `wounded(threshold=50)` | `list[dict]` | Enemies with hp < threshold |
| `adjacent()` | `list[dict]` | Enemies at manhattan distance 1 |
| `nearby(radius=2)` | `list[dict]` | Enemies within manhattan distance |

### Storm

Create with `storm = Storm(state)`.

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `active` | `bool` | True when storm_border > 0 |
| `danger` | `bool` | True when in storm or within 1 tile of it |
| `border` | `int` | Raw storm_border value |

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `safe_zone_center()` | `(int, int)` | Center coordinates of the safe zone |

---

## Valid Actions

Every `decide()` function must return one of these action tuples.

| Action | Tuple Format | Energy Cost | Effect |
|--------|-------------|-------------|--------|
| Move | `("move", direction)` | 5 | Move 1 tile in direction |
| Attack | `("attack", direction)` | 10 | Deal damage to adjacent enemy in direction |
| Defend | `("defend",)` | 10 | Reduce incoming damage by 10 this round |
| Rest | `("rest",)` | 0 | Restore 20 energy and 10 HP |
| Ranged Attack | `("ranged_attack", direction)` | 20 | Deal 15 damage at range (requires unlock) |
| Taunt | `("taunt",)` | 10 | Force nearby enemies to target you (requires unlock) |
| Dash | `("dash", direction)` | 15 | Move 2 tiles in direction (requires unlock) |

**Directions:** `"north"`, `"south"`, `"east"`, `"west"`

**Notes:**
- If energy is insufficient, the action fails and the bot rests instead.
- Ranged Attack, Taunt, and Dash require progression unlocks (not available to new bots by default).
- Invalid actions count as failures. After 3 consecutive failures, the bot is forced to rest.
