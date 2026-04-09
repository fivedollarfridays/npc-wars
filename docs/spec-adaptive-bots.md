# Spec: Adaptive Bot Mechanics for NPC Wars

> Porting the NPC Race adaptation levels into the NPC Wars engine

---

## Context

NPC Race defines four levels of bot adaptation. NPC Wars already implements some of these through the Watcher system and player profiles, but player-authored bots are stateless — they reset every match. This spec adds cross-match learning for player bots and an evolutionary tournament mode.

---

## Level 1: Reactive Adaptation (Already Done)

**Status: Complete.** Every bot already has full reactive capability through the `state` dict.

The helpers DSL (`Me`, `Enemies`, `Storm`) provides:
- Position awareness (distance to enemies, storm border)
- HP/energy monitoring (threatened, can_kill_adjacent)
- Storm prediction (active, danger, safe_zone_center)

**What's already reactive in NPC Wars that Racing is building:**

| Racing Reactive Feature | NPC Wars Equivalent |
|------------------------|---------------------|
| Adjust pit timing based on gaps | Adjust rest timing based on energy + enemy proximity |
| Switch push/conserve based on position | Switch aggro/defensive based on HP and enemy count |
| Tire wear monitoring | Energy monitoring (below threshold → rest) |
| Weather adaptation | Storm prediction (pre-position before border closes) |

**No work needed.** The starter bot (`bots/starter.py`) demonstrates all of this with tunable thresholds.

---

## Level 2: Cross-Match Learning (NEW — Player Bot Persistence)

**Status: Gap.** The Watcher learns across matches, but player bots don't.

### Design

Add a `bot_memory` dict that persists between matches for each bot. The engine saves it as JSON after each match and loads it before the next.

**State dict addition:**
```python
state = {
    "me": {...},
    "enemies": [...],
    # ... existing fields ...
    "memory": {}  # persistent dict — survives between matches
}
```

**Return value extension:**
```python
def decide(state):
    # Read what worked before
    last_strategy = state["memory"].get("best_strategy", "aggro")

    # ... decision logic ...

    # Store learnings for next match
    state["memory"]["best_strategy"] = "defend-counter"
    state["memory"]["matches_played"] = state["memory"].get("matches_played", 0) + 1

    return ("attack", "north")
```

**Engine changes:**
1. `engine/game.py` — load bot memory from `data/bot_memory/{emoji}.json` before match
2. Pass `memory` dict into state via `engine/state.py:build_state()`
3. After match, save updated memory dicts to disk
4. Memory is per-bot (keyed by emoji), max 10KB per bot (prevent abuse)
5. `npcwars init` creates `data/bot_memory/` directory
6. `npcwars play --fresh` flag clears all bot memory for a clean start

**Security:**
- Memory is a plain dict — no code execution, just JSON serialization
- Size limit prevents memory-based DoS
- Bot scanner doesn't need changes (memory is engine-managed, not bot-imported)

**What bots can learn:**
- Which strategies won against which opponents
- Optimal energy thresholds for this bot roster
- Storm timing patterns (already deterministic, but bots could cache computations)
- Opponent behavior patterns (DIY version of the Watcher's PatternTable)

### Starter Bot Memory Example

```python
# In bots/starter.py, add a memory-aware priority:
matches = state["memory"].get("matches_played", 0)
if matches > 0:
    # After a few matches, we know our win rate
    wins = state["memory"].get("wins", 0)
    win_rate = wins / matches
    if win_rate < 0.2:
        # We're losing — try being more aggressive
        ENERGY_THRESHOLD = 20  # lower = more aggressive
```

---

## Level 3: Evolutionary Tournament Mode (NEW)

**Status: Gap.** No tournament infrastructure exists.

### Design

Add a `npcwars tournament` command that runs N matches, identifies winners, mutates their parameters, and breeds new generations.

**The flow:**
```bash
npcwars tournament --generations 10 --matches-per-gen 20 --population 8
```

1. **Generation 0:** Load all bots from `bots/` as the starting population
2. **Run matches:** Each generation runs N matches with random pairings
3. **Score:** Rank bots by win rate across the generation
4. **Select:** Keep the top 50% (winners)
5. **Mutate:** For each winner, create a mutant by tweaking threshold constants:
   - Parse the bot source with AST
   - Find numeric literals in comparisons (e.g., `if me.energy < 30`)
   - Randomly adjust by ±20%
   - Save as a new bot file (`bots/gen1_starter_v1.py`)
6. **Fill:** Random crossover or new wizard-generated bots fill remaining slots
7. **Repeat** for N generations
8. **Output:** The best bot from the final generation, with a lineage report

**Key constraints:**
- Only mutate numeric thresholds, not logic structure
- Mutations must pass `npcwars validate`
- Each generation's best bot is preserved (elitism)
- Tournament results saved to `data/tournament/` with full lineage

**CLI:**
```
npcwars tournament --generations 10 --matches-per-gen 20 --population 8
npcwars tournament --resume data/tournament/run_001/  # continue from checkpoint
npcwars tournament --best data/tournament/run_001/    # show best bot
```

### Why This Is Powerful for the Agent Arena

The prompt becomes: "Here's my bot. It wins 30% of matches. Analyze its strategy and suggest specific threshold changes to improve it." Then the tournament validates the AI's suggestions at scale.

---

## Level 4: ML-Based (Deferred — Sandbox Conflict)

**Status: Intentional gap.**

The security sandbox blocks `numpy`, `torch`, and other ML imports. This is correct — untrusted code should not have access to ML libraries in a hosted environment.

**Options if we ever want this:**
1. **Unsafe local mode:** `npcwars play --unsafe` disables the import allowlist for local-only matches (never on the server)
2. **Pre-trained model API:** Bot calls a local inference server instead of importing torch directly
3. **Engine-provided features:** The engine computes features (enemy distance matrix, action history) and passes them in the state dict. The bot just does weighted sums — no ML imports needed.

**Recommendation:** Defer. Levels 1-3 provide enough depth. Level 4 is a fundamentally different product (ML training platform vs coding game).

---

## Implementation Plan

### Sprint 21: Bot Memory (Level 2) — 6 tasks, ~120 Cx

| Task | Title | Cx | Depends |
|------|-------|----|---------|
| T21.1 | Bot memory storage module (`data/bot_memory.py`) | 20 | — |
| T21.2 | Wire memory into state dict (`engine/state.py`, `engine/game.py`) | 25 | T21.1 |
| T21.3 | Memory persistence (save after match, load before) | 20 | T21.2 |
| T21.4 | Memory size limit enforcement (10KB cap) | 15 | T21.3 |
| T21.5 | `--fresh` flag for `npcwars play` and `npcwars battle` | 15 | T21.3 |
| T21.6 | Update starter bot with memory-aware example + integration test | 25 | T21.5 |

### Sprint 22: Tournament Mode (Level 3) — 7 tasks, ~160 Cx

| Task | Title | Cx | Depends |
|------|-------|----|---------|
| T22.1 | Tournament runner (`npcwars/tournament.py`) | 30 | — |
| T22.2 | Bot scoring and ranking system | 20 | T22.1 |
| T22.3 | AST-based threshold mutation engine | 35 | — |
| T22.4 | Generation lifecycle (select, mutate, fill) | 25 | T22.2, T22.3 |
| T22.5 | `npcwars tournament` CLI command | 20 | T22.4 |
| T22.6 | Tournament state persistence + resume | 15 | T22.5 |
| T22.7 | Best bot export + lineage report | 15 | T22.6 |

---

## Cross-Game Applicability

This spec applies to every NPC game:

| Feature | NPC Wars | NPC Racing | NPC Kitchen |
|---------|----------|------------|-------------|
| Bot memory | Track opponent patterns, win rates | Track tire strategy per track, weather adaptation | Track recipe timing success rates |
| Tournament | Evolve combat thresholds | Evolve pit timing, tire choice, push/conserve balance | Evolve cooking temperatures, timing windows |
| Mutation targets | Energy thresholds, chase distances, HP triggers | Pit lap windows, tire wear limits, fuel targets | Cook time margins, temperature offsets |

The memory storage module and tournament runner are **100% shareable** across games — they operate on bot files and numeric thresholds without knowing the domain. Add to the `npc-sdk` extraction list.

---

## What This Means for the Product

**Level 2 (memory) changes the game identity.** Bots that learn make the game a living system. Your bot gets better the more you play. The prompt becomes: "My bot has played 50 matches and stores its learnings in memory. Analyze this memory JSON and suggest how to use it better."

**Level 3 (tournament) is the content engine.** One `npcwars tournament` run generates 10 generations of evolved bots. The best one becomes a new built-in challenger. "Beat the evolved bot" is a natural progression goal.

**Together, they create a flywheel:** Play → Learn → Evolve → Challenge → Play.
