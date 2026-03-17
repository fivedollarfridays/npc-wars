# NPC Wars — Mechanics Deep Dive

Everything your bot needs to know to win. The stuff the tutorial doesn't tell you.

---

## Resolution Order (per round)

Every round resolves in this exact sequence. Knowing this is the difference between a good bot and a dead one.

```
1. DECIDE      — all bots choose actions simultaneously
2. DEFEND      — defense bonuses applied
3. MOVE        — positions update, bump collisions resolve
4. ATTACK      — melee attacks resolve against post-move positions
5. RANGED      — ranged attacks resolve
6. STORM       — storm damage applied
7. ENERGY      — energy costs deducted, rest heals applied
8. DEATHS      — bots at 0 HP are eliminated
```

**Key insight:** Defense resolves BEFORE attacks. Attacks resolve BEFORE deaths. This means:

- Two bots attacking each other **both take damage** (and both can die)
- A defending bot takes half damage from attacks that land on the same round
- A bot can kill and be killed in the same round
- Storm damage stacks with attack damage — a bot in the storm getting hit can die from the combined total even if either alone wouldn't kill them

---

## Constants

| Stat | Value | Notes |
|------|-------|-------|
| Starting HP | 100 | Max 100 |
| Starting Energy | 100 | Max 100 |
| Attack Power | 25 base | +2 per 10 rounds after R15 |
| Defense | 0 base | 10 when defending |
| Storm Damage | 10/round | Unavoidable if in storm |
| Wall Splat | 10 bonus | When bumped into a wall |
| Kill Bounty | +30 energy | Instant refill on kill |

### Action Costs

| Action | Energy Cost | Effect |
|--------|------------|--------|
| `move` | 5 | Move 1 tile cardinal |
| `attack` | 10 | 25 damage to adjacent tile (minus target defense) |
| `defend` | 10 | Set defense to 10 (halves incoming base damage) |
| `rest` | 0 | +5 HP, +20 energy |
| `dash` | 15 | Move 2 tiles |
| `ranged_attack` | 20 | 15 fixed damage at range 2 |
| `taunt` | 10 | Force nearby bot to attack you (range 2) |

### Damage Formula

```
damage = max(0, attacker.attack_power - defender.defense)
```

- Undefended: `25 - 0 = 25 damage`
- Defended: `25 - 10 = 15 damage`
- Late game (R35): `29 - 0 = 29 damage` (base 25 + 4 from round scaling)

---

## Simultaneous Resolution: What It Means for You

Since all actions resolve simultaneously:

**Mutual kills are real.** If you and an enemy attack each other and both are below 25 HP, you both die. There's no "who goes first" — you go at the same time.

**Defend-then-counter beats pure aggro.** If an enemy is adjacent and likely to attack:
1. Round N: Defend (take 15 instead of 25)
2. Round N+1: Attack (deal full 25)
3. Net: you took 15, they took 25. You're ahead by 10 HP.

A pure aggro bot attacking every round takes 25 damage per mutual exchange. A defend-counter bot takes 15 damage per exchange. Over 4 exchanges, that's 40 HP saved.

**Rest is vulnerable.** A resting bot has 0 defense and can't retaliate. If you're adjacent to a resting bot, attacking them is the highest-value play: you deal 25 damage for 10 energy, they gain 5 HP and 20 energy — net -20 HP for them, and they wasted their turn.

---

## The Bump System

When a bot moves into an occupied tile, it **bumps** the occupant:

- The occupant gets pushed 1 tile in the movement direction
- If the pushed bot hits another bot, **chain bump** — that bot gets pushed too
- If a pushed bot hits a wall, **wall splat** — 10 bonus damage
- If a pushed bot lands in the storm, **storm bounce** — they take storm damage immediately

**Tactical uses:**
- Bump enemies into the storm for guaranteed 10 damage + ongoing storm damage
- Bump enemies into walls for 10 splat damage
- Position yourself between an enemy and the storm, then bump them in
- Chain bumps can displace multiple enemies in one move

**Two bots moving to the same empty tile:** The first in the iteration order gets the tile; the second is blocked. This is deterministic per seed but not reliably exploitable.

---

## The Storm

The storm closes predictably. You can compute exactly where it will be.

```
Rounds 1-9:    No storm (border = 0)
Rounds 10-29:  Closing phase — border = (round - 9) / 5 tiles
Rounds 30+:    Endgame — border += 1 tile every 2 rounds
```

**Extended mode:** Storm moves 50% slower (multiply round thresholds by 1.5).

The safe zone is always centered on the grid. `Storm.safe_zone_center()` returns the center — but the real play is **pre-positioning**. If you know the storm closes 1 tile at round 15, be inside that line by round 13. Bots that react to the storm waste energy catching up; bots that predict it save that energy for fighting.

---

## Attack Power Scaling

All bots start with 25 attack power. **The wizard's aggression slider does NOT change this.** It only changes how often your bot decides to attack.

Attack power increases by round:
```
Rounds 1-15:   25 base
Rounds 16-25:  27 (+2)
Rounds 26-35:  29 (+4)
Rounds 36-45:  31 (+6)
...
```

This means late-game fights are more lethal. A round-40 bot deals 31 damage undefended — that's 4 hits to kill from full HP, vs 4 hits at the start. The scaling is identical for all bots, so it doesn't create asymmetry — it creates urgency.

---

## Energy Economy

Energy is the real resource. HP is your life; energy is your ability to do anything about it.

| State | You should... | Why |
|-------|--------------|-----|
| Energy < 10 | Rest | Can't afford any action except rest |
| Energy 10-20 | Defend or rest | One action then you're broke |
| Energy 30-50 | Be selective | 2-3 actions before needing rest |
| Energy 50+ | Be aggressive | You can sustain a fight |
| Kill a bot | Go wild | +30 energy bounty, you're rich |

**Energy denial:** Attacking a resting bot is the highest-EV play because:
- They spent their turn resting (+5 HP, +20 energy)
- You deal 25 damage (-25 HP)
- Net for them: -20 HP, +20 energy — terrible trade
- They didn't even get to use that energy

---

## The Watcher (The Cringe)

The adaptive boss bot spawns mid-match when conditions are met. It reads your action patterns and counters them.

**How it learns:** Every round, it records what you do in each context (low HP, adjacent enemy, storm closing, etc.). After a few rounds, it predicts your most likely action and picks the counter.

**How to beat it:** Randomize your idle behavior. When you're not executing a clear priority (kill/flee/rest), alternate between defend and random moves. The Cringe's `PatternTable.predict()` needs consistency to exploit — uniform random actions converge to equal probabilities, making its counter-selection random too.

**Rubber-banding:** The Watcher's accuracy cap scales with your performance. Doing well? It gets more accurate. Struggling? It backs off. You can't brute-force it by being bad — it adapts in both directions.

---

## Priority Ladder (Battle-Tested)

The bots that win consistently follow this priority order:

```
1. ESCAPE STORM      — storm damage is guaranteed and unavoidable
2. REST WHEN BROKE   — energy < 15? Rest. No exceptions.
3. FINISH KILLS      — adjacent enemy ≤ attack_power HP? Kill them NOW
4. ENERGY DENIAL     — adjacent resting enemy? Attack them
5. DEFEND WHEN HIT   — adjacent attacker + you're below 40 HP? Defend
6. CHASE WOUNDED     — enemy below 50 HP? Close distance
7. PRE-POSITION      — drift toward where the safe zone WILL be
8. RANDOMIZE IDLE    — no clear priority? Random move or defend (anti-Watcher)
```

**What loses:**
- Attacking into empty tiles (10 energy for nothing)
- Ignoring the storm (10 guaranteed damage/round adds up fast)
- Always attacking (pure aggro loses to defend-counter)
- Never attacking (survive to final 2, lose to someone with more HP)
- Predictable patterns (The Watcher reads you)

---

## The `state` Dict — Complete Reference

```python
state = {
    "me": {
        "x": 3, "y": 5,          # grid position
        "hp": 80,                  # 0-100
        "energy": 60,             # 0-100
        "attack_power": 25,       # base + round scaling
    },
    "enemies": [
        {
            "name": "Rival",
            "emoji": "🎯",
            "x": 7, "y": 2,
            "hp": 45,
            # NOTE: enemy energy is NOT visible!
        },
        # ... more enemies
    ],
    "grid_size": 10,
    "storm_border": 2,            # tiles from edge that are storm
    "round": 15,
    "bumps_last_round": [...],    # bump events from previous round
}
```

---

## Testing Your Bot

```bash
# Validate (security scan)
npcwars validate bots/my_bot.py

# Run a seeded match and watch in terminal
npcwars play --seed 42

# Run 10 matches with different seeds and compare results
for i in $(seq 1 10); do npcwars play --seed $i --no-watch; done

# Re-watch a saved replay
npcwars watch results/match_001.json --speed 4
```

**Seed tip:** Use the same seed to test changes. If your bot wins with seed 42 but loses after a code change, you broke something. If it wins with more seeds after the change, you improved.
