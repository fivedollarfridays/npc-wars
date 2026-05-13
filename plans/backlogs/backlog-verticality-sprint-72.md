# Verticality Sprint 72

> Add a discrete `layer: int` dimension to npc-wars positions, action space, and combat
> resolution — transforming the existing implicit height mechanic (HIGH_GROUND tiles
> giving +2 to-hit / 1.15× damage) into an explicit layered 2.5D system. Ship behind a
> feature flag with one sample layered arena and one layer-aware bot. Preserve
> byte-identical match output for pre-existing flat matches (default `layer=0`).
>
> **Type:** feature
> **Estimated Cx:** ~109
> **Tasks:** 11
>
> **Brief:** `docs/brief-verticality-sprint-72.md`

---

## Phase 1: Schema Foundation

### T72.1 — Position schema + layer field | Cx: 8 | P0

**Description:** Add a `layer: int` field (default 0) to the `SelfInfo` and `EnemyInfo` TypedDicts in `engine/types.py`, add `self.layer = 0` to `Bot.__init__` in `engine/combat.py` (≤ 2 LOC), and extend `build_match_data`/`write_match` in `engine/match_writer.py` so every position entry emits a `"layer"` key. This is the single schema change that every downstream task depends on. Because `combat.py` is at 366/400 LOC, the Bot edit must stay surgical — track line count and abort-extract if the change grows past 10 LOC. Preserve byte-identical behavior for all existing bots and match replays when layer defaults to 0.

**AC:**
- [ ] `SelfInfo` and `EnemyInfo` TypedDicts in `engine/types.py` include `layer: int`
- [ ] `Bot.__init__` in `engine/combat.py` sets `self.layer = 0` by default
- [ ] `combat.py` line count ≤ 376 after change (buffer vs. 400 error threshold)
- [ ] `build_match_data` includes `"layer"` in every position entry emitted
- [ ] Existing 14 bots in `bots/` run without modification
- [ ] `tests/test_match_writer.py` and `tests/test_combat_serialization.py` pass with layer=0 default
- [ ] `bpsai-pair arch check engine/combat.py engine/types.py engine/match_writer.py` passes
- [ ] No behavioral change for existing matches — default 0 preserves byte-identical output (modulo the new field)

**Depends on:** none

---

## Phase 2: Verticality Mechanics (Parallel)

### T72.2 — Verticality action module + dispatch | Cx: 18 | P0

**Description:** Create `engine/terrain_verticality.py` (≤ 150 LOC) implementing `resolve_jump`, `resolve_drop`, and `resolve_climb` — the three new action verbs. `drop` is always legal and moves bot to `layer - 1`; `jump` requires the target tile to be `is_climbable` at `layer + 1`; `climb` is a slower jump with extra energy cost. Add `jump`, `drop`, `climb` entries to `ACTION_COSTS` and `DEFAULT_UNLOCKED_ACTIONS` in `engine/combat.py` (≤ 5 LOC total — watch the 400-LOC ceiling). Wire dispatch in `engine/rounds.py` (177 LOC currently; must stay under 200 after this change). New tests in `tests/test_terrain_verticality.py` cover legal jump, illegal jump (no support), drop from any layer, climb energy cost, and chained transitions.

**AC:**
- [ ] `engine/terrain_verticality.py` exists, ≤ 150 LOC, implements `resolve_jump`, `resolve_drop`, `resolve_climb`
- [ ] `ACTION_COSTS` in `engine/combat.py` includes entries for `jump`, `drop`, `climb`
- [ ] `DEFAULT_UNLOCKED_ACTIONS` includes the three new verbs
- [ ] `engine/rounds.py` dispatches the new verbs; total line count stays ≤ 200
- [ ] `combat.py` line count ≤ 380 after change
- [ ] `tests/test_terrain_verticality.py` covers: legal jump, illegal jump (no climbable tile above), drop from layer N → N-1, drop from layer 0 is no-op, climb energy cost, chained transitions
- [ ] `bpsai-pair arch check engine/terrain_verticality.py engine/rounds.py engine/combat.py` passes
- [ ] All existing tests still green

**Depends on:** T72.1

---

### T72.3 — Layer-aware line-of-sight | Cx: 10 | P0

**Description:** Extend `has_line_of_sight` in `engine/terrain_combat.py:110` to take layer parameters for both endpoints. Same-layer calls must preserve exact existing behavior. Cross-layer LOS is blocked unless both endpoints sit on a transition tile (where `is_climbable` is True). Update the sole call site in `engine/rounds_combat.py:176` to pass layer args from attacker and target bots. All existing `test_terrain_combat.py` tests must remain green — the new signature must be backward-compatible via default `l1=0, l2=0` or the caller update must be tight enough to not break existing fixtures.

**AC:**
- [ ] `has_line_of_sight(terrain, x1, y1, x2, y2, l1=0, l2=0)` signature extended (or equivalent with layer params)
- [ ] Same-layer calls (l1 == l2) return identical results to pre-change implementation
- [ ] Cross-layer calls (l1 != l2) return False unless both endpoints are on `is_climbable` tiles
- [ ] `engine/rounds_combat.py:176` updated to pass layer args
- [ ] `tests/test_terrain_combat.py` extended with layer-aware LOS cases: same-layer (preserved), cross-layer blocked, cross-layer at transition tiles allowed
- [ ] All existing `test_terrain_combat.py`, `test_terrain_combat_wiring.py`, and `test_rounds_combat.py` tests pass
- [ ] `bpsai-pair arch check engine/terrain_combat.py engine/rounds_combat.py` passes

**Depends on:** T72.1

---

### T72.4 — Cylindrical storm | Cx: 6 | P1

**Description:** Update `engine/grid.py` so `is_in_storm(x, y)` ignores layer — the storm is a cylinder, damaging the same (x, y) footprint on every elevation. Update spawn logic so bots can spawn on any layer the arena defines (most arenas stay layer-0-only; layered arenas can distribute spawns). Existing storm tests must pass unchanged because the signature stays `(x, y)` — the change is semantic (storm semantics are layer-invariant), not syntactic.

**AC:**
- [ ] `engine/grid.py::is_in_storm(x, y)` documented as layer-invariant (cylinder semantics)
- [ ] `spawn_positions` accepts an optional `layer_distribution` (or similar) that defaults to all-layer-0
- [ ] Existing `tests/test_grid.py` and `tests/test_grid_storm_spawn.py` pass unchanged
- [ ] New test: spawning on a layered arena distributes bots across layers per the arena definition
- [ ] New test: a bot on layer 1 inside the storm footprint takes storm damage identically to a layer-0 bot
- [ ] `bpsai-pair arch check engine/grid.py` passes

**Depends on:** T72.1

---

### T72.5 — Arena schema + hills arena | Cx: 12 | P0

**Description:** Extend `engine/terrain.py::TerrainMap` with `max_layer_at(x, y) -> int` (returns highest legal layer for a tile, 0 for single-layer tiles) and `is_climbable(x, y, layer) -> bool` (returns True if a bot at `(x, y, layer)` can jump/climb to `(x, y, layer+1)`). Ship one sample layered arena called "hills": a central pillar with layer-0 base and layer-1 top, four climb-point tiles around the pillar, surrounded by flat layer-0 terrain. Existing single-layer arenas continue to work with implicit `max_layer_at == 0`. `get_random_map()` must exclude layered arenas unless the feature flag (introduced in T72.10) is on, so current ladder matches continue to draw flat arenas.

**AC:**
- [ ] `TerrainMap.max_layer_at(x, y) -> int` returns highest legal layer (defaults 0 for existing tiles)
- [ ] `TerrainMap.is_climbable(x, y, layer) -> bool` returns True at transition tiles
- [ ] Hills arena added: central pillar with layer-0 + layer-1, 4 climb-point tiles, flat surround
- [ ] `get_random_map()` excludes layered arenas when verticality flag is off (or the flag hook is stubbed if T72.10 hasn't landed yet — T72.10 wires the real flag)
- [ ] All existing arena tests in `tests/test_terrain.py` pass unchanged
- [ ] New test: hills arena constructs without error; `max_layer_at` returns expected values for pillar vs. surround
- [ ] `bpsai-pair arch check engine/terrain.py` passes — `terrain.py` stays ≤ 400 LOC

**Depends on:** T72.1

---

## Phase 3: Bot + Viewer (Parallel)

### T72.6 — Sample layer-aware bot | Cx: 8 | P1

**Description:** Create `bots/layered_sentinel.py` — a demonstration bot that uses the new verticality action space. Behavior: prefers climbing to layer 1 when outnumbered (enemies visible > allies), drops back to layer 0 to retreat when HP < 30%, otherwise plays standard aggressive logic. This bot exists to prove the action space is complete and usable by player-written code. Add `tests/test_bots_layered_sentinel.py` that runs the bot's `decide(state)` against a hills-arena game state and asserts it returns valid actions. Verify all 14 pre-existing bots in `bots/` still run without modification (they default to layer 0 and use the pre-existing action set).

**AC:**
- [ ] `bots/layered_sentinel.py` exists and implements `decide(state) -> dict`
- [ ] Bot climbs to layer 1 when outnumbered in visible enemies
- [ ] Bot drops to layer 0 when HP < 30
- [ ] Bot returns valid action dicts for all reachable states on the hills arena
- [ ] `tests/test_bots_layered_sentinel.py` covers: climb-when-outnumbered, drop-on-low-hp, plays a full match on hills arena without crashing
- [ ] All 14 existing bots in `bots/` run a sample match without code modification
- [ ] `bpsai-pair arch check bots/layered_sentinel.py` passes

**Depends on:** T72.2, T72.5

---

### T72.7 — Viewer layer indicator | Cx: 15 | P1

**Description:** Update the Canvas renderer in `viewer/viewer.html` + `viewer/js/*` so bots on layer 1+ render with a visible indicator — color border, elevation shadow, or small layer-number badge. Existing flat matches (all bots on layer 0) must render visually identical to before. Do not grow `viewer/js/effects.js` (511 LOC, already over warning) or `viewer/js/events.js` (417 LOC); prefer a new small module like `viewer/js/layer_indicator.js` (≤ 100 LOC). The exact file set is a call during implementation — the constraint is simply: no viewer JS file may grow past 600 LOC.

**AC:**
- [ ] Bots on layer 1+ render with a distinguishable visual indicator (border, shadow, or badge)
- [ ] Flat matches (all positions at layer 0) render visually identical to the pre-change viewer
- [ ] No viewer JS file grows past 600 LOC
- [ ] New file (if any) is ≤ 100 LOC and passes `bpsai-pair arch check`
- [ ] Existing viewer tests (`test_viewer_*`) pass unchanged
- [ ] Manual smoke: load a hills-arena match JSON and verify layer indicator appears
- [ ] Manual smoke: load a pre-verticality match JSON and verify no regression

**Depends on:** T72.1

---

## Phase 4: Regression + Rebalance

### T72.8 — Back-compat regression | Cx: 8 | P0

**Description:** Add `tests/test_match_backcompat_verticality.py` that replays at least 20 representative pre-existing match JSON files (selected from `results/`) through the post-verticality engine and asserts byte-identical output modulo the new `"layer": 0` field. Use a normalized-diff comparator that strips the layer field from the new output before comparing to the stored baseline. This is the single gate that catches any T72.1–T72.4 regression against the 700+ test files and match fixtures. Must run in under 60 seconds.

**AC:**
- [ ] `tests/test_match_backcompat_verticality.py` exists
- [ ] ≥ 20 representative match replays selected from `results/` as fixtures
- [ ] Each fixture replays to byte-identical match JSON under the new engine, modulo layer field
- [ ] Normalized-diff comparator strips `"layer": 0` entries from new output before comparison
- [ ] Test suite runs in < 60 seconds
- [ ] `bpsai-pair arch check` on new test file passes

**Depends on:** T72.1, T72.2, T72.3, T72.4

---

### T72.9 — Rebalance sanity sim | Cx: 10 | P1

**Description:** Create `scripts/sim_verticality_balance.py` — a harness that runs ~100 matches on the hills arena with mixed archetype bots (include `layered_sentinel` alongside 2–3 existing bots: `viper`, `example_tank`, `reaper`, etc.). Output: winrate distribution per bot with ±3σ bounds, logged to `results/sim-verticality/`. Produce a summary markdown at `docs/sim-verticality.md` that compares each bot's winrate on the hills arena vs. its winrate on flat arenas from recent tournament data. Flag any bot whose winrate shifts by > ±15 percentage points — that's the catastrophic-rebalance signal for T72.11's decision gate.

**AC:**
- [ ] `scripts/sim_verticality_balance.py` runs 100 matches on hills arena with mixed archetype bots
- [ ] Results written to `results/sim-verticality/` (per-match JSON + summary)
- [ ] `docs/sim-verticality.md` produced with per-bot winrate table (hills vs. flat baseline)
- [ ] ±3σ bounds computed and reported
- [ ] Any bot with winrate shift > ±15 pp is flagged in the summary
- [ ] Script runs in < 5 minutes on standard dev hardware
- [ ] `bpsai-pair arch check scripts/sim_verticality_balance.py` passes

**Depends on:** T72.2, T72.5, T72.6

---

## Phase 5: Integration + Decision

### T72.10 — Integration gate | Cx: 10 | P0

**Description:** Final integration: wire the `VERTICALITY_ENABLED` feature flag into `engine/config.py` (default False for public ladder, True for opt-in test season), update documentation in `docs/mechanics-deep-dive.md` and `docs/kill-switch-game-description.md` with the new layer concept and action verbs, run the full test suite, `ruff check .`, and `bpsai-pair arch check .`. Reconcile `.paircoder/context/state.md` with final task statuses. Push a PR and verify CI green.

**AC:**
- [ ] `VERTICALITY_ENABLED` flag present in `engine/config.py`, default False
- [ ] `T72.5`'s `get_random_map()` gate reads the real flag (not a stub)
- [ ] `docs/mechanics-deep-dive.md` updated with layer concept + jump/drop/climb verbs
- [ ] `docs/kill-switch-game-description.md` mentions the layered 2.5D mode
- [ ] `pytest` full suite green
- [ ] `ruff check .` clean
- [ ] `bpsai-pair arch check .` — no new violations (`combat.py` stays < 400 LOC)
- [ ] `.paircoder/context/state.md` reconciled with final task statuses
- [ ] PR pushed; CI green on GitHub

**Depends on:** T72.1, T72.2, T72.3, T72.4, T72.5, T72.6, T72.7, T72.8, T72.9

---

### T72.11 — Decision gate | Cx: 4 | P0

**Description:** Finalize the ship-on / ship-off call based on the T72.9 rebalance data. If any existing bot shifted winrate by > ±15 percentage points on the hills arena, `VERTICALITY_ENABLED` default remains False for the public ladder (needs a follow-on rebalance sprint before ladder exposure). Regardless, the flag defaults True for a named opt-in test season so engaged players can try layered matches voluntarily. Record the decision in `docs/sim-verticality.md`. File a follow-on ticket against the `agentgrounds-web-broadcast` repo so the Minecraft viewer can consume the new `layer` field — cross-repo contract edge, out of scope for this sprint but needs a tracking issue.

**AC:**
- [ ] Decision recorded in `docs/sim-verticality.md` with the supporting data from T72.9
- [ ] `VERTICALITY_ENABLED` default value finalized in `engine/config.py` per decision rule
- [ ] A named opt-in test season config exists with flag=True
- [ ] Follow-on issue filed against `agentgrounds-web-broadcast` for `matchTransformer.ts` to consume `layer` (reference the issue number in `docs/sim-verticality.md`)
- [ ] Brief `docs/brief-verticality-sprint-72.md` and backlog `plans/backlogs/backlog-verticality-sprint-72.md` marked as completed in `.paircoder/context/state.md`

**Depends on:** T72.9, T72.10

---

## Delivery Summary

| Task  | Title                                      | Cx | Priority | Depends on                                          |
|-------|--------------------------------------------|----|----------|-----------------------------------------------------|
| T72.1 | Position schema + layer field              | 8  | P0       | none                                                |
| T72.2 | Verticality action module + dispatch       | 18 | P0       | T72.1                                               |
| T72.3 | Layer-aware line-of-sight                  | 10 | P0       | T72.1                                               |
| T72.4 | Cylindrical storm                          | 6  | P1       | T72.1                                               |
| T72.5 | Arena schema + hills arena                 | 12 | P0       | T72.1                                               |
| T72.6 | Sample layer-aware bot                     | 8  | P1       | T72.2, T72.5                                        |
| T72.7 | Viewer layer indicator                     | 15 | P1       | T72.1                                               |
| T72.8 | Back-compat regression                     | 8  | P0       | T72.1, T72.2, T72.3, T72.4                          |
| T72.9 | Rebalance sanity sim                       | 10 | P1       | T72.2, T72.5, T72.6                                 |
| T72.10| Integration gate                           | 10 | P0       | T72.1–T72.9                                         |
| T72.11| Decision gate                              | 4  | P0       | T72.9, T72.10                                       |

**Total Cx:** 109 across 11 tasks.

## Priority Order

1. **P0 (ship or fail the sprint):** T72.1, T72.2, T72.3, T72.5, T72.8, T72.10, T72.11
2. **P1 (should ship):** T72.4, T72.6, T72.7, T72.9
3. **P2 (cut if budget overflows):** none

**Cut-list if budget overflows:** drop T72.4 first (storm cylinder semantics can land in a follow-on — the storm stays 2D-footprint-only, acceptable for prototype). Next cut T72.7 (viewer can stub layer as a printed number rather than Canvas work). Do not cut T72.6 — T72.9 needs a layered bot to play against, so dropping T72.6 invalidates the rebalance gate.
