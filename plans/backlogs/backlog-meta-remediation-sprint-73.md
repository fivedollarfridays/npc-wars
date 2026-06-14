# Kill Switch Meta Remediation — Sprint 73

> Fix the three meta-breakers found in the 2026-06-10 engine deep-dive (locked-action
> self-disconnects, dead equipment bonuses, rest-spam endgame) and build the
> verification harness that makes each one a failing test instead of an archaeology
> finding. Phase 1 writes the tests that document today's broken behavior (TDD: they
> fail or xfail against the current engine); Phase 2 makes them pass; Phase 3 fixes
> the bot-author feedback loop. Source findings: `.paircoder/context/state.md`
> "What Was Just Done" (fable_strategist entry, 2026-06-10).
>
> **Type:** bugfix
> **Estimated Cx:** ~118
> **Tasks:** 10

---

### Phase 1: Verification Harness (tests first — these document the bugs)

### T73.1 — Equipment wiring audit test | Cx: 12 | P0

**Description:** New `tests/test_equipment_wiring.py`: a parametrized audit that walks every item in `EQUIPMENT_CATALOG` (`engine/equipment.py`), equips it on an otherwise-default bot, and asserts that each declared bonus field produces an observable engine difference vs. an unequipped control — to-hit via `roll_attack` with a fixed RNG, DR via computed AC, max_hp/max_energy via `create_bots`, action costs via `apply_action_cost`, regen/rest bonuses via `apply_energy_and_rest`, initiative via attack-resolution order, dodge via forced-dodge RNG. Fields known dead today (`initiative_bonus`, `dodge_bonus`, `energy_regen_bonus`, `rest_energy_bonus`, `crit_chance_bonus`) are marked `xfail(strict=True)` with a comment naming T73.4 — so the audit passes now, and T73.4 flips the xfails to real assertions. This test is the permanent guard against future placebo items.

**AC:**
- [ ] `tests/test_equipment_wiring.py` exists with one parametrized case per bonus field per catalog item
- [ ] Wired fields (weapon to_hit/min_dmg/max_dmg/crit_mult/armor_pierce/reach, armor dr/energy_penalties, accessory to_hit/dr/max_hp/max_energy/crit_mult/energy_cost_reduction) assert real engine deltas
- [ ] Dead fields are `xfail(strict=True)` — suite is green today, and silently-fixed fields turn the xfail into a failure
- [ ] Test derives the field list from `EQUIPMENT_CATALOG` itself, so a new catalog item with an unknown bonus key fails the audit
- [ ] `bpsai-pair arch check tests/test_equipment_wiring.py` passes
- [ ] Full test suite stays green

**Depends on:** none

---

### T73.2 — Pool-bot liveness test | Cx: 8 | P0

**Description:** New `tests/test_pool_bot_liveness.py`: load every shipped bot (`agentgrounds/wars/builtin_bots/` plus `bots/`, excluding `template.py`) via `engine.loader.load_bots`, run each in a 2-bot match against a stationary dummy for 20 rounds with a fixed seed, and assert the bot never increments `consecutive_failures` and never dies by `disconnected`. Today this fails for Trapper, Viper, and Mage (they return locked `trap`/`use_ability` actions and disconnect by round 4) — mark those three `xfail(strict=True)` referencing T73.5, which makes locked actions degrade gracefully and flips the xfails. Also assert every bot survives the validator (`scripts/validate_bot.validate_bot`) so shipping a broken example becomes impossible.

**AC:**
- [ ] `tests/test_pool_bot_liveness.py` runs every shipped bot 20 rounds vs a dummy and asserts zero `consecutive_failures`
- [ ] Trapper/Viper/Mage cases are `xfail(strict=True)` with a comment naming T73.5
- [ ] Every shipped bot passes `validate_bot` in the same test module
- [ ] Test discovers bots from both directories dynamically — a newly added example is covered automatically
- [ ] `bpsai-pair arch check tests/test_pool_bot_liveness.py` passes
- [ ] Full test suite stays green

**Depends on:** none

---

### T73.3 — Balance regression harness (win-rate matrix) | Cx: 15 | P0

**Description:** Extend `agentgrounds/wars/cli/cmd_sim.py` (which already runs batch matches with placements) with a `--balance-report` mode: run N seeded matches over the shipped pool, emit a JSON report of per-bot win rate, per-stat-archetype win rate (using `engine.archetype.classify_archetype`), and kill-cause distribution (combat vs storm vs disconnect vs tiebreaker). Add `scripts/check_balance.py` that compares a fresh report against a checked-in baseline (`data/balance_baseline.json`) and fails when any bot's win rate moves more than a configurable threshold (default ±15pp) — making "a balance patch made one build win 77%" a CI failure, not a discovery. Keep cmd_sim under the 400-LOC source limit; extract a `sim_balance.py` helper module if needed.

**AC:**
- [ ] `killswitch sim --balance-report --matches N --seed S` writes a JSON report with per-bot win rate, per-archetype win rate, and kill-cause distribution
- [ ] Report is deterministic for a fixed seed and match count
- [ ] `data/balance_baseline.json` checked in, generated from ≥30 seeds
- [ ] `scripts/check_balance.py` exits non-zero when any bot deviates from baseline beyond threshold; threshold configurable via flag
- [ ] `tests/test_balance_report.py` covers report shape, determinism, and the threshold check (both pass and fail paths)
- [ ] `bpsai-pair arch check` passes on all touched files; `cmd_sim.py` stays under 400 LOC
- [ ] Full test suite stays green

**Depends on:** none

---

### Phase 2: Meta-Breaker Fixes

### T73.4 — Wire the dead equipment bonuses | Cx: 18 | P0

**Description:** Make the five placebo bonus fields real. `initiative_bonus`: add `equipment_bonuses.initiative` into the to-hit modifier (`attacker.initiative // 10` term) in `engine/combat_rolls.py` callers and into the attack-resolution sort key in `engine/rounds_combat.py`. `dodge_bonus`: add to defender dodge chance passed into `_resolve_hit`. `crit_chance_bonus`: lower the effective crit threshold in `roll_attack`/`calculate_hit_probability`. `energy_regen_bonus` and `rest_energy_bonus`: add to the rest restore in `engine/rounds.py::apply_energy_and_rest`. Update `calculate_hit_probability` so the state-dict numbers reflect the same wiring (coordinates with T73.8). Flip the corresponding T73.1 xfails to hard assertions. This changes balance — regenerate `data/balance_baseline.json` afterward and note the deltas in the task summary (boots_of_speed/charm_of_evasion stop being dead items, which affects Shadow Dancer and Knight).

**AC:**
- [ ] All five dead fields produce observable engine deltas; T73.1 xfails removed and assertions pass
- [ ] Equipment initiative affects both to-hit modifier and attack resolution order
- [ ] `apply_energy_and_rest` includes equipment regen and rest bonuses in the restore amount
- [ ] `calculate_hit_probability` and `roll_attack` agree on crit chance with equipment applied
- [ ] `engine/combat.py` stays ≤ 380 LOC (currently 366/400)
- [ ] `data/balance_baseline.json` regenerated; per-bot win-rate deltas recorded in task summary
- [ ] `bpsai-pair arch check` passes on all touched files; full suite green

**Depends on:** T73.1, T73.3

---

### T73.5 — Locked-action graceful degrade | Cx: 12 | P0

**Description:** A well-formed action that is merely locked should not kill the bot. In `engine/sandbox.py::validate_action`, distinguish three outcomes: valid, malformed (returns None — still counts toward `MAX_CONSECUTIVE_FAILURES`), and well-formed-but-locked (new). In `engine/rounds_decisions.py::resolve_decisions`, a locked action degrades to `("rest",)`, emits a `locked_action` event naming the attempted action, and does NOT increment `consecutive_failures`. Stop baiting bots toward locked actions: in `engine/combat.py::to_self_dict`, omit `trap_cooldown`/`traps` when `trap` is not unlocked and report `ability.ready = False` when `use_ability` is not unlocked. Flip the T73.2 xfails — Trapper, Viper, and Mage must survive 20 rounds. Keep `combat.py` within its LOC ceiling (gate logic is small; extract if it isn't).

**AC:**
- [ ] `validate_action` (or a thin wrapper) distinguishes malformed from locked; malformed still counts toward disconnect
- [ ] Locked actions degrade to rest, emit a `locked_action` event with the attempted action name, and do not increment `consecutive_failures`
- [ ] `to_self_dict` no longer exposes `trap_cooldown: 0` / ready abilities to bots that cannot use them
- [ ] T73.2 xfails for Trapper/Viper/Mage removed; all three survive the liveness test
- [ ] `tests/test_sandbox.py` / `tests/test_action_unlock.py` updated for the new contract
- [ ] `engine/combat.py` ≤ 380 LOC, `rounds_decisions.py` ≤ 200 LOC after change
- [ ] `data/balance_baseline.json` regenerated (three bots rejoin the pool); deltas recorded in summary
- [ ] `bpsai-pair arch check` passes on all touched files; full suite green

**Depends on:** T73.2, T73.3

---

### T73.6 — Versatility bonus retune | Cx: 15 | P1

**Description:** 25/25/25/25 currently gets +75 HP and +20 flat damage from the versatility bonus (`engine/stats.py`), making it strictly dominant — 145 HP vs TankBot's 90, and more damage than the power builds. Retune `_VERSATILITY_HP_MAX`, `_VERSATILITY_DMG_BONUS`, and/or `_VERSATILITY_VARIANCE_CAP` so specialist archetypes land in a 40–60% win-rate band against balanced builds, measured with the T73.3 harness using head-to-head archetype duels (balanced vs tank, glass-cannon, speed, mage at ≥30 seeds each). This is tuning-by-measurement: the AC is the measured band, not specific constant values. Document the chosen constants and the measured matrix in `docs/` so the next balance pass has a baseline. Update `tests/test_stats.py` expectations.

**AC:**
- [ ] Archetype duel sweep (≥30 seeds per pairing) shows every specialist archetype within 40–60% vs balanced
- [ ] No archetype's pool win rate exceeds 2× uniform share in the full-pool balance report
- [ ] `tests/test_stats.py` updated for new derived values; new test pins the duel-band result with a fixed seed set
- [ ] Constants and measured matrix documented in `docs/balance-versatility-s73.md`
- [ ] `data/balance_baseline.json` regenerated; deltas recorded in summary
- [ ] `bpsai-pair arch check engine/stats.py` passes; full suite green

**Depends on:** T73.3, T73.4, T73.5

---

### T73.7 — Endgame forced-combat fix | Cx: 10 | P0

**Description:** Once `get_storm_border` (`engine/grid.py`) exceeds grid/2 the safe zone is empty and the winner is whoever spams `rest` at center — a strategy contest collapsing into a bookkeeping race (observed: ChaosBot winning by random rests). Fix in two parts: (1) clamp the border in `get_storm_border` so the safe zone never shrinks below a 2×2 box, forcing the last bots adjacent where combat resolves the match; (2) disable rest HP-healing for bots standing inside the storm (`engine/rounds.py::apply_energy_and_rest` already takes terrain — add a storm check) so deep-storm camping cannot out-regen the zone. Replays must remain schema-compatible. Verify with the T73.3 kill-cause distribution: storm-cause eliminations in rounds ≥ 35 should drop substantially in favor of combat kills, and no match in a 30-seed sweep should end via the all-dead-spared path more than rarely.

**AC:**
- [ ] `get_storm_border` clamps so the safe zone is never smaller than 2×2 on any grid size
- [ ] Rest inside the storm restores energy but not HP; rest in the safe zone unchanged
- [ ] `tests/test_grid.py` (or new) covers the clamp across grid sizes 10–30; rest-in-storm covered in rounds tests
- [ ] 30-seed sweep: combat kills decide a clear majority of endgames (kill-cause report attached to summary)
- [ ] Existing replay/viewer schema unchanged (`storm_border` stays an int)
- [ ] `data/balance_baseline.json` regenerated; deltas recorded in summary
- [ ] `bpsai-pair arch check` passes on touched files; full suite green

**Depends on:** T73.3

---

### Phase 3: Bot-Author Loop

### T73.8 — Equipment-aware hit_chance_vs / incoming_threat | Cx: 8 | P1

**Description:** `engine/state.py::build_state` calls `calculate_hit_probability(bot.derived, enemy.derived)` with no equipment, so the EV calculator handed to every bot is wrong by ~15% for equipped bots — punishing exactly the authors who play by the math. Extend `calculate_hit_probability` with optional equipment parameters (to_hit, min/max damage, crit_mult, defender dr, armor_pierce — mirroring `roll_attack`'s signature) and pass both sides' `equipment_bonuses` from `build_state` for `hit_chance_vs` and `incoming_threat`. Backward-compatible defaults keep existing callers green. Add a test asserting the state-dict expected_damage for an equipped bot matches a brute-force Monte Carlo of `roll_attack` within tolerance.

**AC:**
- [ ] `calculate_hit_probability` accepts equipment args with defaults preserving current behavior for bare calls
- [ ] `build_state` passes attacker and defender equipment for both `hit_chance_vs` and `incoming_threat`
- [ ] Monte Carlo agreement test: state-dict expected_damage within 5% of simulated `roll_attack` mean for an equipped pairing
- [ ] `engine/state.py` stays ≤ 100 LOC
- [ ] `bpsai-pair arch check` passes on touched files; full suite green

**Depends on:** T73.4

---

### T73.9 — `killswitch doctor` command | Cx: 15 | P2

**Description:** New `agentgrounds/wars/cli/cmd_doctor.py`: `killswitch doctor <bot.py>` runs the bot against the shipped pool for N seeded matches and prints a diagnostic report — locked/invalid action attempts (using the T73.5 `locked_action` events), plague rounds accrued, forced-rest (energy-starvation) rounds, storm damage taken and storm deaths, and per-match placement. Converts engine knowledge from "read the source" into feedback for bot authors — the friction every agent in the agents-developing-agents loop will hit. Reuse `run_sim`/`run_match` internals; no new engine behavior. Register in the killswitch CLI alongside the existing 13 cmd_* modules and document in the README bot-authoring section.

**AC:**
- [ ] `killswitch doctor bots/<file>.py --matches N --seed S` prints locked-action attempts, plague rounds, forced-rest rounds, storm damage/deaths, and placements
- [ ] Exit code non-zero when the bot disconnects or attempts locked actions (CI-friendly)
- [ ] `tests/test_cmd_doctor.py` covers a healthy bot, a locked-action bot, and a plague-prone bot (fixtures)
- [ ] Command registered and listed in `killswitch --help`; README section added
- [ ] `bpsai-pair arch check agentgrounds/wars/cli/cmd_doctor.py` passes (< 400 LOC)
- [ ] Full suite green

**Depends on:** T73.5

---

### T73.10 — Scanner trailing-comment semicolon false positive | Cx: 5 | P1

**Description:** `engine/bot_scanner.py::_check_semicolons` strips string literals and skips lines *starting* with `#`, but a trailing comment containing a semicolon (`return x  # floors to 0; beats resting`) is flagged as semicolon chaining — hit in practice on the first bot authored this sprint. After `_STRING_RE` removes string literals, truncate each line at the first remaining `#` before checking for `;`. Add regression tests: trailing comment with semicolon (clean), real chaining after a trailing comment (violation), semicolon inside a string (clean — existing behavior preserved).

**AC:**
- [ ] Trailing comments containing semicolons no longer flagged
- [ ] Real semicolon chaining still detected, including on lines that also have trailing comments
- [ ] Semicolons inside string literals remain unflagged
- [ ] Regression cases added to `tests/test_bot_scanner.py`
- [ ] `bpsai-pair arch check engine/bot_scanner.py` passes; full suite green

**Depends on:** none

---

## Delivery Summary

| Task | Title | Cx | Priority | Depends on |
|------|-------|----|----------|------------|
| T73.1 | Equipment wiring audit test | 12 | P0 | — |
| T73.2 | Pool-bot liveness test | 8 | P0 | — |
| T73.3 | Balance regression harness | 15 | P0 | — |
| T73.4 | Wire dead equipment bonuses | 18 | P0 | T73.1, T73.3 |
| T73.5 | Locked-action graceful degrade | 12 | P0 | T73.2, T73.3 |
| T73.6 | Versatility bonus retune | 15 | P1 | T73.3, T73.4, T73.5 |
| T73.7 | Endgame forced-combat fix | 10 | P0 | T73.3 |
| T73.8 | Equipment-aware hit_chance_vs | 8 | P1 | T73.4 |
| T73.9 | killswitch doctor command | 15 | P2 | T73.5 |
| T73.10 | Scanner semicolon false positive | 5 | P1 | — |

**Total: ~118 Cx**

## Priority Order

1. T73.1, T73.2, T73.3, T73.10 — harness wave, fully parallel (Phase 1 + quick lint fix)
2. T73.4, T73.5, T73.7 — meta-breaker fixes, parallel after their harness deps
3. T73.6 — versatility retune (needs the fixed pool: dead items wired, three bots un-bricked)
4. T73.8 — equipment-aware state EVs (after equipment wiring settles)
5. T73.9 — doctor command (cut-list candidate if budget overflows)

**Cut-list if over budget:** T73.9 first, then T73.8. T73.6 must not be cut — it is the core meta fix; without it the stat screen has one correct answer.
