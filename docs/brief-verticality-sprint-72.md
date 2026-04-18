# Feature Brief: npc-wars Verticality (Sprint 72)

> Ideation-refined brief. Input to `/draft-backlog` → `engage`.
> Refines `docs/brief-verticality-for-minecraft-era.md` with codebase ground truth as of 2026-04-18.
> Upstream decision assumed: **Option C (layered 2.5D)** per the input brief's recommendation.

## Idea

Add a discrete `layer: int` dimension to npc-wars positions, action space, and
combat resolution — transforming the existing implicit height mechanic
(HIGH_GROUND tiles giving +2 to-hit / 1.15× damage) into an **explicit layered
2.5D system** where bots can jump, drop, and climb between elevation layers on
tiles that support transitions. Ship behind a feature flag with one sample
layered arena and one layer-aware bot. Preserve byte-identical match output for
pre-existing flat matches (default `layer=0`).

**Scope is deliberately narrow.** The broadcast renderer consumes whatever we
emit (cross-repo follow-on); Options A, B, D are rejected per the input brief.
Per-layer storm, continuous voxel physics, and retroactive bot rebalance are
out of scope.

## Codebase Context

### Stack

- Python 3.13 engine (`engine/`), FastAPI server, Discord bot, vanilla-JS HTML5
  Canvas viewer.
- SQLite + JSON persistence; Pillow + ffmpeg for video; procedural WAV audio.

### Size (ground truth)

- ~228 source + ~704 test files.
- **54 engine files** including the following *already-terrain-aware* modules:
  `terrain.py` (231), `terrain_combat.py` (138), `combat.py` (366),
  `combat_rolls.py` (252), `rounds.py` (177), `rounds_combat.py` (239),
  `grid.py` (134), `match_writer.py` (64), `types.py` (47), `stats.py` (159).
- Input brief's file-size estimates for `rounds.py` (claimed 350) and
  `combat.py` (claimed 365) are stale — `rounds.py` split into `rounds.py` +
  `rounds_combat.py` during earlier tech-debt sprints.

### Current Sprint

S71 (Tech Debt Cleanup) is in flight. Verticality is **S72**. State.md last
action: `T71.2 done`. Branch: `main`.

### Conflicting In-Progress Work

**None on engine core.** `bpsai-pair` reports 8 stuck `in_progress` tasks —
all TV/broadcast/commentary/Discord work:

| Task | Area |
|---|---|
| T59.1 | Highlight extractor |
| T60.3 | Code Circuit rivalry tracker |
| T61.2 | Platform commentary contract |
| T62.1 | Episode generator |
| T62.2 | Commentary video overlay |
| T64.1 | Discord match ingestion |
| T64.2 | TV rendering pipeline |
| T67.3 | Website season standings |

None of these touch `engine/types.py`, `engine/grid.py`, `engine/terrain*.py`,
`engine/combat*.py`, `engine/rounds*.py`, `engine/match_writer.py`, or
`viewer/` — the verticality sprint's file set. **No serialization risk.**
Recommend cleaning up stale status as a sprint-0 housekeeping step but not a
blocker.

### Pre-Existing Verticality Infrastructure (input brief missed this)

The game **already has a height concept** via `terrain.py` tile types:

```python
# engine/terrain.py
HIGH_GROUND = "high_ground"  # tile char: "^"
```

And `engine/terrain_combat.py` already rewards elevation:

```python
HIGH_GROUND_TO_HIT: int = 2
HIGH_GROUND_DAMAGE_MULT: float = 1.15
def has_line_of_sight(terrain, x1, y1, x2, y2): ...  # LOS exists
```

`rounds_combat.py:176` already gates attacks on LOS. **Verticality extends
this system, not replaces it.** The sprint becomes "make the implicit elevation
explicit via `layer: int`, and add transition verbs" — a significantly smaller
delta than the input brief assumed.

## Sprint-Level Constraints

### Cross-Task Arch Constraints

- **`engine/combat.py` at 366 LOC is 34 LOC from the 400 error threshold.**
  Any growth in combat.py must be ≤ ~10 LOC; new logic extracts to sibling
  modules. T1 (schema) and T2 (actions) both touch `combat.py` minimally —
  adding fields to `ACTION_COSTS` and a `layer` attr to `Bot.__init__`. If
  those two land together within budget, no extraction is required.
- **`engine/terrain_combat.py` at 138 LOC** has headroom. LOS extension in T3
  lives here, not in `combat.py`.
- **No module currently over 400 lines** among files this sprint touches.

### Oversized Files That Will Grow

- `combat.py` (see above). Growth cap: 10 LOC.
- Viewer JS: `viewer/js/effects.js` (511 LOC) and `events.js` (417 LOC) are
  already oversized — T7 (viewer layer indicator) must use a **new file** or
  extend a smaller one (TBD during `/pc-plan` discovery).

### TODOs That Become Tasks

None pre-existing touching the verticality surface.

### Cross-Task Contract Edges

- **T1 (schema) produces `layer: int` field** — consumed by T2 (action
  dispatch), T3 (LOS), T4 (storm), T5 (arena def), T6 (sample bot), T7
  (viewer), T8 (back-compat test).
- **T5 (arena) produces tile-layer metadata** — consumed by T2 (transition
  validity) and T6 (sample bot navigation).
- **T6 (sample bot) produces match JSON with non-zero layer values** —
  consumed by T8 (back-compat verifies old matches unchanged) and T9
  (rebalance needs real layered data).

## Tasks

Budget estimates below use sprint-shape comparison (S47: ~130 Cx, S71 tech-
debt: ~90 Cx per `state.md` history) rather than `bpsai-pair budget
estimate --task` (that tool needs concrete file diffs; discovery is ideation's
job, not implementation).

### T72.1 — Position schema + layer field
- **Title:** Add `layer: int` to position TypedDicts and match schema
- **Cx:** 8
- **Priority:** P0
- **Depends on:** none
- **Files:** `engine/types.py`, `engine/combat.py` (Bot init — 1-2 LOC),
  `engine/match_writer.py`, `tests/test_match_writer.py`,
  `tests/test_combat_serialization.py`
- **AC template:** migration
- **Custom AC:**
  - [ ] `SelfInfo` and `EnemyInfo` TypedDicts include `layer: int`
  - [ ] `Bot.__init__` sets `self.layer = 0` by default
  - [ ] `build_match_data` includes `"layer"` in every position entry
  - [ ] Existing bots and matches work unchanged (default 0)
  - [ ] `combat.py` line count ≤ 376 after change (buffer vs. 400)

### T72.2 — Verticality action module + dispatch
- **Title:** `jump` / `drop` / `climb` verbs and resolution
- **Cx:** 18
- **Priority:** P0
- **Depends on:** T72.1
- **Files:** `engine/terrain_verticality.py` (new), `engine/combat.py`
  (ACTION_COSTS + DEFAULT_UNLOCKED_ACTIONS — ≤ 5 LOC),
  `engine/rounds.py` (dispatch — ≤ 15 LOC),
  `tests/test_terrain_verticality.py` (new)
- **AC template:** refactor (for `rounds.py` touch) + schema (new verbs)
- **Custom AC:**
  - [ ] `terrain_verticality.py` ≤ 150 LOC, implements `resolve_jump`,
        `resolve_drop`, `resolve_climb`
  - [ ] `drop` always legal (costs nothing extra); `jump` requires tile at
        `(x,y,layer+1)` exists and is `is_climbable`; `climb` is a slower
        `jump` (extra energy cost)
  - [ ] `ACTION_COSTS` entries for jump, drop, climb
  - [ ] `rounds.py` dispatches the new verbs without growing past 200 LOC
  - [ ] Unit tests cover: legal jump, illegal jump (no support above), drop
        from layer N, climb energy cost, chained transitions

### T72.3 — Layer-aware line-of-sight
- **Title:** Extend `has_line_of_sight` to block across layer edges
- **Cx:** 10
- **Priority:** P0
- **Depends on:** T72.1
- **Files:** `engine/terrain_combat.py`, `engine/rounds_combat.py` (call site),
  `tests/test_terrain_combat.py`
- **AC template:** refactor
- **Custom AC:**
  - [ ] `has_line_of_sight(terrain, x1, y1, l1, x2, y2, l2)` new signature
  - [ ] Same-layer calls unchanged in behavior
  - [ ] Cross-layer LOS blocked unless both endpoints are at a transition tile
  - [ ] `rounds_combat.py:176` updated to pass layer args
  - [ ] All existing `test_terrain_combat.py` tests still green (default
        layer=0 preserves old behavior)

### T72.4 — Cylindrical storm
- **Title:** Storm damage applies on every layer with matching (x, y)
- **Cx:** 6
- **Priority:** P1
- **Depends on:** T72.1
- **Files:** `engine/grid.py`, `tests/test_grid.py`,
  `tests/test_grid_storm_spawn.py`
- **AC template:** refactor
- **Custom AC:**
  - [ ] `is_in_storm(x, y)` ignores layer (cylinder semantics)
  - [ ] Spawn logic works per-layer: bots can spawn on layer 0 or 1+ based on
        arena definition
  - [ ] Existing storm tests pass unchanged

### T72.5 — Arena schema + hills arena
- **Title:** Extend terrain to carry per-tile layer metadata; ship one layered arena
- **Cx:** 12
- **Priority:** P0
- **Depends on:** T72.1
- **Files:** `engine/terrain.py`, `tests/test_terrain.py`, one new arena def
- **AC template:** schema
- **Custom AC:**
  - [ ] `TerrainMap` gains `max_layer_at(x, y) → int` and
        `is_climbable(x, y, layer) → bool`
  - [ ] One sample "hills" arena: central pillar (layer 0 + 1), four climb-
        point tiles, flat layer-0 surround
  - [ ] `get_random_map()` excludes layered arenas unless feature flag is on
  - [ ] Existing single-layer arenas unchanged (implicit `max_layer_at = 0`)

### T72.6 — Sample layer-aware bot
- **Title:** `bots/layered_sentinel.py` demonstrates the action space
- **Cx:** 8
- **Priority:** P1
- **Depends on:** T72.2, T72.5
- **Files:** `bots/layered_sentinel.py` (new), `tests/test_bots_layered_sentinel.py` (new)
- **AC template:** refactor (behavioral contract)
- **Custom AC:**
  - [ ] Bot `decide(state)` returns valid action dict
  - [ ] Bot prefers climbing to layer 1 when outnumbered
  - [ ] Bot drops to retreat when HP < 30%
  - [ ] Plays a full match on the hills arena without crashing
  - [ ] 14 existing bots still run without modification

### T72.7 — Viewer layer indicator
- **Title:** Show layer in Canvas renderer
- **Cx:** 15
- **Priority:** P1
- **Depends on:** T72.1
- **Files:** `viewer/viewer.html`, `viewer/js/*` (exact file set TBD at
  `/pc-plan`: prefer smaller files or new module over `effects.js`/`events.js`)
- **AC template:** refactor
- **Custom AC:**
  - [ ] Bots on layer 1+ render with a visible indicator (color border or
        elevation shadow)
  - [ ] Existing flat matches render identically (visual regression check)
  - [ ] No viewer JS file grows past 600 LOC

### T72.8 — Back-compat regression
- **Title:** All pre-existing match replays produce byte-identical JSON
- **Cx:** 8
- **Priority:** P0
- **Depends on:** T72.1, T72.2, T72.3, T72.4
- **Files:** `tests/test_match_backcompat_verticality.py` (new),
  `results/*.json` as fixtures
- **AC template:** gate
- **Custom AC:**
  - [ ] Pick ≥ 20 representative match replays from `results/`
  - [ ] Each replays to byte-identical match JSON under new engine (modulo
        added `"layer": 0` field — use a normalized-diff comparator)
  - [ ] Test runs in < 60s

### T72.9 — Rebalance sanity sim
- **Title:** ~100 matches on hills arena, winrate delta analysis
- **Cx:** 10
- **Priority:** P1
- **Depends on:** T72.2, T72.5, T72.6
- **Files:** `scripts/sim_verticality_balance.py` (new), results logged to
  `results/sim-verticality/`
- **AC template:** gate
- **Custom AC:**
  - [ ] Script runs 100 matches with mixed archetype bots on hills arena
  - [ ] Outputs winrate distribution + ±3σ bounds
  - [ ] Produces a markdown summary in `docs/sim-verticality.md`
  - [ ] Flags any bot with winrate > old baseline ±15 pp (catastrophic
        rebalance signal)

### T72.10 — Integration gate
- **Title:** Everything green, flag wired, docs updated
- **Cx:** 10
- **Priority:** P0
- **Depends on:** T72.1–T72.9
- **Files:** `engine/config.py` (flag), `docs/mechanics-deep-dive.md`,
  `docs/kill-switch-game-description.md`, `.paircoder/context/state.md`
- **AC template:** gate
- **Custom AC:**
  - [ ] `VERTICALITY_ENABLED` feature flag (default False for ladder, True
        for opt-in test season)
  - [ ] Full test suite green
  - [ ] `ruff check .` clean on all touched files
  - [ ] `bpsai-pair arch check .` → no new violations (combat.py stays < 400)
  - [ ] Docs updated with new action verbs and layer concept
  - [ ] State.md reconciled with final task statuses
  - [ ] PR pushed, CI green

### T72.11 — Decision gate
- **Title:** Ship-on / ship-off call based on T72.9 data
- **Cx:** 4
- **Priority:** P0
- **Depends on:** T72.9, T72.10
- **Files:** `engine/config.py` (flag default), `docs/sim-verticality.md`
  (decision record)
- **AC template:** gate
- **Custom AC:**
  - [ ] Decision recorded: flag default remains OFF for public ladder if
        T72.9 shows > ±15 pp winrate shift for any existing bot
  - [ ] Flag defaults ON for a named opt-in test season regardless
  - [ ] Follow-on ticket filed against `agentgrounds-web-broadcast` to
        consume the new `layer` field (cross-repo contract edge)

## Dependency Graph

```
Wave 0:  T72.1 (schema)
           │
Wave 1:  T72.2 (verb module) ──┐
         T72.3 (LOS)           ├── all depend on T72.1 only
         T72.4 (storm)         │
         T72.5 (arena)         ─┘
           │
Wave 2:  T72.6 (sample bot)    depends on T72.2 + T72.5
         T72.7 (viewer)        depends on T72.1 only (could run in Wave 1)
           │
Wave 3:  T72.8 (backcompat)    depends on T72.1–T72.4
         T72.9 (rebalance sim) depends on T72.2, T72.5, T72.6
           │
Wave 4:  T72.10 (integration gate) depends on T72.1–T72.9
           │
Wave 5:  T72.11 (decision gate) depends on T72.9, T72.10
```

Wave 1 has max parallelism of 4. Wave 2 has 2. Wave 3 has 2. T72.7 (viewer)
could slot into Wave 1 but is deferred to Wave 2 to keep viewer-side
iteration after schema has settled in code.

## File Collision Matrix

For each parallel wave, pairwise file intersections:

**Wave 1 — T72.2 × T72.3 × T72.4 × T72.5:**

| Pair | Intersection | Verdict |
|---|---|---|
| T72.2 ∩ T72.3 | none | safe (T72.2 = rounds.py + new verticality module; T72.3 = terrain_combat.py + rounds_combat.py) |
| T72.2 ∩ T72.4 | none | safe (T72.2 = rounds.py; T72.4 = grid.py) |
| T72.2 ∩ T72.5 | none | safe (T72.2 = verbs/rounds; T72.5 = terrain.py) |
| T72.3 ∩ T72.4 | none | safe |
| T72.3 ∩ T72.5 | terrain_combat.py + terrain.py — but T72.5 only extends terrain.py; T72.3 touches terrain_combat.py | safe — different files inside the terrain/ family |
| T72.4 ∩ T72.5 | none | safe |

`engine/combat.py` is touched by T72.1 (Wave 0, serial) — Wave 1 does not
touch it, so the 400-LOC ceiling is not at risk from parallelism.

**Wave 2 — T72.6 × T72.7:** no file overlap. T72.6 = `bots/` + tests; T72.7 =
`viewer/`. Safe.

**Wave 3 — T72.8 × T72.9:** T72.8 = test-only (read-only on engine); T72.9 =
new script + results dir. Safe.

## Sprint Budget

| Metric | Value |
|---|---|
| Total Cx | **109** |
| Task count | 11 |
| P0 count | 6 (T72.1, 72.2, 72.3, 72.5, 72.8, 72.10, 72.11 — 7) |
| P1 count | 4 (T72.4, 72.6, 72.7, 72.9) |
| P2 count | 0 |

Cx is lighter than the input brief's rough 145 because the sprint rides on
**existing terrain/LOS/tile infrastructure**. S47 shipped at ~130 Cx; S71 at
~90 Cx. This sprint sits between them in scope.

**Cut-list if budget overflows:** drop T72.4 (storm stays flat, acceptable
for prototype — cylindrical semantics can land in a follow-on) or T72.7
(viewer indicator can be stubbed as a printed layer number rather than
Canvas work). T72.6 (sample bot) cannot be cut without invalidating T72.9
(rebalance sim needs a layered bot to play against).

## Integration Points

### Inside npc-wars

- **T72.1's `layer` field** is the single schema change every downstream
  task depends on. Breaks nothing when defaulted to 0.
- **T72.5's arena extension** (`max_layer_at`, `is_climbable`) is consumed
  by T72.2 (transition validity) and T72.6 (bot navigation).
- **T72.8 (back-compat)** is the single gate that catches T72.1–T72.4
  regressions against the 700+ existing test files and match fixtures.

### Cross-Repo (`agentgrounds-web-broadcast`)

- **Schema contract:** `matchTransformer.ts` in the broadcast repo will need
  to accept and pass through the new `layer` field. Not in this sprint —
  filed as a follow-on ticket in T72.11.
- **Broadcast v0 assumption:** broadcast is pivoting to Minecraft and ships
  v0 with flat gameplay assumed. This sprint is **decoupled** from the
  broadcast pivot; neither blocks the other.

### Outside

- **Discord bot / leaderboard / website:** care about winners and stats,
  not positions. No change.

## Out of Scope

- Options A (status quo), B (visual-only), D (full voxel 3D) — per input brief.
- Per-layer storm variants — cylindrical only.
- Racing game (`code_circuit`) elevation — separate future design.
- Retroactive rebalance of existing bots — opt-in test season only.
- Minecraft viewer updates in `agentgrounds-web-broadcast` — cross-repo
  follow-on, tracked in T72.11.
- AI-assisted layered-bot generation (Watcher system adaptation) — future
  sprint.
- Full 3D Canvas viewer rewrite — T72.7 is a layer indicator, not a 3D
  renderer.

## Pre-flight Blockers

1. **Product approval of Option C.** Input brief recommends it; ideation
   confirms the cost is manageable (109 Cx, rides on existing terrain
   infrastructure). Not blocking backlog drafting; blocking engage kickoff.
2. **S71 tech-debt sprint closed** (recommend, not required — no file
   collisions exist between S71 tasks and verticality files).
3. **8 stuck in_progress tasks cleaned up** — none collide, but keeping them
   open pollutes status reporting. Recommend a sprint-0 task: `bpsai-pair
   task update <id> --status done` for each, per maintainer review.
4. **`AGENTS.md` missing** — `bpsai-pair validate` flags it. Fix via
   `bpsai-pair validate --fix` or manual creation before engage.
5. **`pytest` green on `main`** before kickoff. Verify with
   `pytest -q && ruff check .`.

---

Brief ready. To generate the backlog:

```
/draft-backlog docs/brief-verticality-sprint-72.md
```
