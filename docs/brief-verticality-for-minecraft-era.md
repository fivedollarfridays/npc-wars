# Feature Brief: npc-wars Verticality for the Minecraft-Viz Era

> Ideation-ready brief. Input to `/ideation` → `/draft-backlog` → `engage`.
> Scope: npc-wars game-design decision with an evaluation + prototype sprint.
> Authored 2026-04-18 after a cross-repo conversation exposed that npc-wars
> being a 2D grid game leaves the incoming Minecraft broadcast viewer unable
> to use its strongest native capability (3D space, cameras, elevation) for
> actual gameplay depth.

## Idea

npc-wars is a **2D grid-based tactical combat game** — every `(x, y)` is a
single flat tile, combat is horizontal, and no vertical concept exists.
Meanwhile the broadcast product is pivoting its renderer from a custom
Three.js pipeline to Minecraft (sibling repo `agentgrounds-web-broadcast`,
see `ROADMAP.md` + `backlog-broadcast-sprint-04.md` there), which is
inherently 3D. The viewer can render beautiful 3D cameras around a 2D
game, but the **game itself** gains nothing from the third dimension — bots
can't jump, hide behind terrain, take high ground, or drop from above.

This brief proposes a **focused evaluation + prototype sprint** to answer:
**should npc-wars extend its game model with a discrete vertical dimension
(layered 2.5D), and if so, what's the minimal viable implementation that
preserves existing bot compatibility and gameplay balance?**

The sprint explicitly does **not** resolve the broadcast renderer question
(that's decided separately in the sibling repo — broadcast v0 assumes flat
gameplay regardless of what npc-wars does next). It's a game-design sprint
for npc-wars: evaluate four postures, pick one, prototype it behind a
feature flag, measure the cost/benefit.

## Codebase Context

### Stack

- **Python 3.x** engine (`engine/`), CLI (`scripts/`, `play.py`, `wizard.py`),
  server (FastAPI, `server/`), discord bot (`discord_bot/`)
- **Vanilla JS** viewer (`viewer/viewer.html` + CSS + JS) — HTML5 Canvas
- **SQLite + JSON** persistence (`data/`, `results/`)
- **Pillow + ffmpeg** for video generation; procedural WAV audio

### Size (approximate)

- ~228 source files, ~704 test files (per `brief-kill-switch-tv.md`)
- 54 engine files, 24 CLI files, 21 server files, 10 viewer JS files
- Oversized files >200 LOC: 34 source files; viewer/js (effects 511, events 417),
  engine (combat 365, rounds 350, watcher_controller 255), server
  (rival_debrief 357, rival_factory 348)

### Current Sprint

Per `docs/road-to-completion.md` and recent work: S47 (Tournaments Phase 3B)
shipped; S48–S49 active around browser flow and security hardening; S50–S57
completed in assessment / launch-readiness / rival polish / tech-debt / queue
resilience. Kill Switch TV brief (`brief-kill-switch-tv.md`) proposes a
procedural broadcast layer orthogonal to gameplay. **This verticality brief
sits between game-engine work and TV/broadcast work** — it changes the game
model, which the broadcast layer then visualizes.

### Conflicting In-Progress Work

None known at brief authorship. Verify during `/ideation` Step 0.

## What Exists That This Touches

### Bot + Position Model — `engine/types.py`, `engine/combat.py`

Current Bot has `x: int, y: int` grid coords. Action space is
cardinal (north/south/east/west) + attack patterns. No `z` field, no
elevation awareness. Any verticality extension adds a new dimension to
`BotState` and a new action verb (`jump` / `climb` / `drop`).

### Grid + Storm — `engine/grid.py`

Grid is a 2D square (`grid_size × grid_size`, default
`max(10, sqrt(player_count) × 5)`). Storm is a shrinking border ring
— concentric rectangles of damaging tiles. Both assume single-plane.
Verticality forces: does the storm extend vertically (cylinder), or does
each layer have its own storm (stacked rectangles)?

### Combat Resolution — `engine/combat.py`, `engine/rounds.py`, `engine/match_phases.py`

Hit resolution today assumes horizontal line-of-sight and same-plane
adjacency. Ranged attacks use grid-distance in (x, y). Verticality breaks
this unless we say "same layer only for melee, any layer for ranged" (which
is a meaningful rebalance).

### Match JSON Schema — `engine/match_writer.py`

Current per-round entry:
```
"positions": [{ "emoji": "🤖", "x": 2, "y": 4, "hp": 100, ... }]
```
Adds `"layer": 0` (int, 0-indexed bottom-up) if Option C is chosen. Broadcast
consumers (agentgrounds-web-broadcast `matchTransformer.ts`) must handle
missing-field fallback for back-compat with old matches.

### Character Schema — `engine/types.py` (character/archetype)

Archetype classification (Bruiser/Assassin/Tank/Controller/Balanced) doesn't
currently factor mobility. A layered mode might add **mover archetypes** —
bots that prefer layer-hopping — but that's a bonus, not required.

### Stat System — `engine/stats.py`

100-point budget across power/speed/armor/mind. Speed drives initiative +
dodge. For layered 2.5D, does **speed** determine jump reliability, or is
jumping always deterministic? This is the first rebalance decision.

### Existing Viewer — `viewer/viewer.html` + `.js`

Canvas renderer draws the 11×11 grid with emoji/shape markers. A layered
mode needs the viewer to show **either**:
- Multiple layer slices stacked vertically in a "floorplan" view, OR
- A top-down view with bots colored or bordered by their current layer

Both are viewer-only work (no engine changes to render).

### Tests — `tests/` (particularly `tests/test_match_writer.py`,
`tests/test_combat.py`, `tests/test_grid.py`)

Any new dimension means new tests for: position validity, layer transitions,
layer-aware combat, storm-per-layer, spawn-per-layer. Back-compat tests
verify 2D matches still play identically.

## Sprint-Level Constraints

### Cross-Task Arch Constraints

- `engine/combat.py` at 365 LOC is already close to the 400-LOC error
  threshold. Any combat-system verticality changes probably need to be
  extracted into a sibling module (`combat_verticality.py`, ~50-80 LOC)
  rather than inline-grown.
- `engine/rounds.py` at 350 LOC similarly close. Layer-transition logic
  (jump action resolution) likely wants its own file.

### Oversized Files That Will Grow

- `combat.py`, `rounds.py`, `watcher_controller.py` (at 255 LOC) — avoid
  inline growth; extract.

### TODOs That Become Tasks

None pre-existing on the verticality question. The brief itself becomes
the backlog root.

### Cross-Task Contract Edges

- **Engine → match schema** — whatever new field ships must be backward-
  compatible for existing match replays.
- **Engine → existing bots** — ALL existing `decide(state)` functions
  submitted by players must continue to return valid actions. Default
  layer = 0 for bots that don't implement layer-awareness.
- **Engine → viewer** — viewer schema version bump; old matches still load.
- **npc-wars → agentgrounds-web-broadcast** — broadcast's
  `matchTransformer.ts` needs to either ignore `layer` or map it to a
  Minecraft y-offset. Broadcast side is not in this sprint.

## The Four Postures (for /ideation to pick from, not all four to build)

### Option A — Strictly Flat (status quo)

- npc-wars stays 2D. Bots cannot jump, climb, or drop.
- Minecraft viewer fakes all verticality via cameras + environmental props.
- **Cost:** zero.
- **Benefit:** broadcast pivot unblocked; existing bots untouched; tournament
  meta undisturbed.
- **Drawback:** npc-wars underuses the Minecraft platform long-term.

### Option B — Flat + Visual Embellishment

- npc-wars stays 2D. Broadcast renderer *pretends* bots jump / get launched
  on dramatic events.
- **Cost:** ~1 sprint of drama-scripting on the broadcast side. **Zero
  npc-wars cost.**
- **Drawback:** viewer-shown events diverge from game state (a bot that
  "flies 4 blocks up" on a hit didn't actually move). Erodes broadcast
  faithfulness. **Recommend rejecting.**

### Option C — Layered 2.5D

- npc-wars adds a discrete `layer` field to positions. Layers are whole-
  number elevation levels (0=ground, 1=elevated platform, 2=rooftop, etc.).
- New action verbs: `jump <dir>` (move +1 layer on a tile that supports it),
  `drop <dir>` (move -1 layer, always legal), `climb <dir>` (slower, costs
  energy). Existing move verbs default to same-layer.
- Line-of-sight blocked across layer edges unless at a transition tile.
- Storm is cylindrical (same border shape on every layer — no layer-specific
  storm).
- Arena per game mode defines which tiles are multi-layer (stairs, ladders,
  pillars) — keeps most tiles single-layer for existing tactical feel.
- **Cost:** 1 npc-wars sprint for engine + schema + sample bot + viewer + tests.
- **Benefit:** real tactical depth (cover, high-ground, ambush); Minecraft
  viz becomes a faithful 3D representation.
- **Backward compatibility:** existing matches all-layer-0; existing bots
  operate on layer 0 exclusively; tournament meta gets a version bump for
  future seasons that opt in to layered arenas.

### Option D — Full 3D (continuous vertical)

- npc-wars becomes a voxel game with gravity, falling damage, block cover.
- **Cost:** 2-3 sprints; fundamental rewrite.
- **Drawback:** it's no longer npc-wars — it's a different game. Existing
  bot meta dies. **Recommend rejecting.**

### Primary Recommendation

**Option C — layered 2.5D.** Scope this sprint as "evaluate + prototype
Option C, ship behind a feature flag with one sample arena and one sample
layer-aware bot."

## Candidate Tasks for /ideation to Scope

These are **candidate tasks**, not prescribed ones. `/ideation` should use
its discovery step to refine Cx estimates, dependencies, and ordering.

- **T.1 — Schema + position model.** Add `layer: int` to `BotState`, default
  0. Update `match_writer.py` to include layer in per-round positions.
  Back-compat: emit `layer: 0` for all current bots.
- **T.2 — Layer-transition module.** New `engine/combat_verticality.py`
  (≤120 LOC). Implements `jump`, `drop`, `climb` resolution; validates
  tile-supports-transition.
- **T.3 — Line-of-sight across layers.** Update hit resolution in
  `engine/rounds.py` (or a new sibling) to block LOS across layer edges
  except at transition tiles.
- **T.4 — Cylindrical storm.** Update `engine/grid.py` to project the
  shrinking border across all layers. Layer-specific storm variants
  explicitly **out of scope** for the prototype.
- **T.5 — Arena schema.** Arena files define which tiles are multi-layer.
  Start with one "hills" arena (e.g., central pillar with ladders on four
  sides, surrounded by flat layer-0 terrain).
- **T.6 — Sample layer-aware bot.** One bot (`bots/layered_sentinel.py`)
  that uses the layer system — prefers high ground when outnumbered, drops
  to retreat. Exists to prove the action space works.
- **T.7 — Viewer update.** `viewer/viewer.html` + `.js` updated to show
  layer (either stacked slices or color-coded). Existing 2D matches still
  render identically.
- **T.8 — Back-compat regression tests.** Run ALL existing match replays
  through the new engine; output must be byte-identical to current engine
  output when `layer` defaults to 0 throughout.
- **T.9 — Rebalance sanity check.** Play ~100 matches with mixed old and
  new bots on a layered arena. Measure winrate delta; surface any
  catastrophic imbalance before closing the sprint.
- **T.10 — Integration gate.** All previous tasks green + a layered-mode
  sample match JSON produced + a Kill Switch TV-style commentary track on
  that match reads naturally with layer events mentioned.
- **T.11 — Decision gate.** If rebalance data shows catastrophic imbalance,
  the sprint ends with a "layered-mode keeps flag-disabled by default,
  needs rebalance sprint before shipping" verdict. Otherwise, flag defaults
  to on.

## Dependency Graph (rough — /ideation should refine)

```
T.1 (schema)
  ├── T.2 (transitions) ──┐
  ├── T.3 (LOS)          ─┼── T.5 (arena) ── T.6 (sample bot) ──┐
  └── T.4 (storm)        ─┘                                      │
                                                                  │
                            T.7 (viewer) ─────────────────────────┤
                                                                  │
                            T.8 (backcompat regress) ─────────────┤
                                                                  │
                            T.9 (rebalance) ───────────────────── T.10/T.11 (gate)
```

## File Collision Matrix (pre-analysis)

- T.2 and T.3 both touch `engine/rounds.py` (action resolution dispatches
  to transitions AND combat). Recommend T.2 extracts transitions into a
  new file, T.3 stays in rounds.py — zero collision.
- T.4 touches `engine/grid.py`. No other tasks modify it.
- T.7 touches viewer-only files. No collision with engine tasks.
- T.8 is read-only on engine; just runs existing matches. No collision.

## Sprint Budget Estimate (pre-/ideation)

Rough Cx targets: T.1=10, T.2=15, T.3=15, T.4=10, T.5=10, T.6=15, T.7=20,
T.8=10, T.9=15, T.10=20, T.11=5 → ~145 Cx. Comparable shape to prior npc-
wars sprints (S47 at ~130 Cx per `road-to-completion.md`). `/ideation`
should refine via `bpsai-pair budget estimate` per task.

## Integration Points

- **Inside npc-wars:** T.1's schema change is consumed by T.2-T.7 and T.10.
  T.8's back-compat tests catch regressions from T.1-T.4. T.9's rebalance
  data feeds T.11's gate decision.
- **Cross-repo (agentgrounds-web-broadcast):** the `layer` field added by
  T.1 needs a mapping in broadcast's `matchTransformer.ts`. That mapping
  work is **not in this sprint** — it's a broadcast-side follow-on. A
  ticket should be filed against the broadcast repo once T.1 lands.
- **Discord bot / leaderboard:** existing UIs care about winners and kills,
  not positions. No change required.

## Out of Scope

- **Option A (flat)** — status quo, no work needed. Document the current
  state of the game, don't rebuild anything.
- **Option B (visual embellishment)** — rejected as it creates viewer/game
  state divergence. No implementation work.
- **Option D (full 3D)** — too big, different game.
- **Full per-layer storm mechanics** — out of prototype scope.
  Cylindrical storm only.
- **Racing game (`code_circuit`) elevation** — racing has its own
  design space (banked turns, inclines, jumps). Not a simple extension
  of layered 2.5D. Treat as a separate future design sprint.
- **Broadcast renderer updates** — the Minecraft viewer in the sibling
  broadcast repo will get updated to consume `layer` data in a
  broadcast-side follow-on sprint, not here.
- **Retroactive balance changes** — existing bots and existing match
  JSON continue to work with `layer: 0` defaults. Tournament meta for
  current season uses Option A (flat).
- **AI-generated layered bots** — the Watcher system and bot-author
  assistants can adapt later.
- **Viewer 3D rewrite** — the Canvas viewer gets a layer indicator
  (T.7), not a full 3D reengineering. That's broadcast's job, not this
  viewer's.

## Pre-flight Blockers (clear before /engage)

1. **A decision on whether to pursue Option C.** This brief recommends it,
   but the choice is a product/design call. `/ideation` should flag that
   this brief's outcome is conditional on approving Option C; if product
   chooses Option A, the sprint collapses to "update docs to formalize
   2D-flat as locked for the foreseeable future."
2. **Test-suite green on current engine.** `pytest` and `ruff check`
   clean on npc-wars main before we touch the bot state model.
3. **Broadcast pivot memory reviewed.** The sibling broadcast memory at
   `~/.claude/projects/-home-kmasty-projects-agentgrounds-web/memory/project_minecraft_bedrock_pivot.md`
   (or its future Java successor) records what the broadcast side expects
   from npc-wars. Any conflicts surface before kickoff.
4. **Reserve a season for evaluation.** Layered 2.5D ships behind a flag;
   existing tournament season continues unaffected. No live players should
   be forced into layered arenas without notice.

## Exit Criteria

- [ ] `engine/types.py` emits positions with a `layer` field, default 0
- [ ] `engine/combat_verticality.py` (or similar) exists, implements jump/
      drop/climb, ≤120 LOC
- [ ] LOS resolution respects layer boundaries
- [ ] Storm mechanic extends across layers as a cylinder
- [ ] One sample layered arena ships
- [ ] One sample layer-aware bot ships
- [ ] Viewer displays layer info
- [ ] All pre-existing match replays produce byte-identical match JSON
      under the new engine
- [ ] Rebalance sanity test (~100 matches) produces within-3σ winrate
      distribution relative to a flat-mode baseline
- [ ] Kill Switch TV commentary still reads naturally on a layered match
      (manual review, not blocking)
- [ ] Feature flag defaults to off for public ladder; on for a test season
- [ ] Docs updated (`docs/mechanics-deep-dive.md` + `kill-switch-game-description.md`)

## Connection to Broadcast Work (cross-repo context)

The agentgrounds-web-broadcast repo is pivoting its match renderer from
a Three.js implementation to Minecraft (their sprint BC4 is the pivot
spike, per their `ROADMAP.md`). That work is not gated by npc-wars
verticality — broadcast v0 ships with **Option A (flat) assumed** and uses
3D cameras + environmental props to compensate for visual flatness. A
decision here does not block them.

However, once broadcast v0 ships on Option A, the *most natural next
upgrade* to the broadcast is layered 2.5D support — one Minecraft y-level
per layer, with ladders rendered as ladders. That upgrade is cheap on
the broadcast side IF this npc-wars sprint ships Option C with the
proposed schema (`layer: int` field). If this sprint instead concludes
"stay flat forever," the broadcast pivot is still fine; it just never
needs the layer abstraction.

Either outcome is coherent. This sprint decides which future we're in.

---

Brief ready. Hand to `/ideation`:
```
/ideation docs/brief-verticality-for-minecraft-era.md
```
