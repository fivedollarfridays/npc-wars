# Kill Switch Meta Follow-ups — Sprint 74

> The three follow-ups surfaced during S73 (logged in state.md). Closes the blind
> spot in the S73 balance guard (it only watches a 6-bot, no-equipment pool),
> finishes T73.7's endgame so the final two bots resolve by combat instead of the
> round cap, and gives the `mind` stat combat value so mage can reach the balance
> band. Source: S73 "What Was Just Done" follow-ups in `.paircoder/context/state.md`.
>
> **Type:** bugfix
> **Estimated Cx:** ~38
> **Tasks:** 3

---

### Phase 1: Close the guard blind spot

### T74.1 — Balance harness uses the real (equipped) pool | Cx: 13 | P0

**Description:** The S73 balance regression guard (`killswitch sim --balance-report` / `scripts/check_balance.py` / `data/balance_baseline.json`) runs on `builtin_bots` — 6 bots, no equipment, no locked-action bots — so it cannot catch equipment- or locked-action-related balance regressions, which is exactly what S73 introduced. Switch the harness default pool to the `bots/` pool (14 bots incl. equipment loadouts, Trapper/Viper/Mage, fable_strategist), or add an explicit `--pool` selector defaulting to `bots/`. Regenerate `data/balance_baseline.json` from the new pool (≥30 seeds, deterministic) and record the new per-bot/per-archetype rates. Update `test_balance_report.py` for the new pool. This must land before T74.2/T74.3 so their baseline regenerations use the meaningful pool.

**AC:**
- [ ] Balance report default pool is the `bots/` pool (or `--pool` selector defaulting to it); documented in `--help`
- [ ] `data/balance_baseline.json` regenerated from the new pool, ≥30 seeds, byte-deterministic across two runs
- [ ] `check_balance.py` passes against a fresh report from the new pool
- [ ] `test_balance_report.py` updated for the new pool shape; determinism test still holds
- [ ] New per-bot + per-archetype rates recorded in the task summary
- [ ] `bpsai-pair arch check` rc=0 on touched files; relevant suite green

**Depends on:** none

---

### Phase 2: Finish the endgame + mind balance

### T74.2 — Endgame forced resolution (refine T73.7) | Cx: 13 | P1

**Description:** T73.7 clamped the storm to a 2×2 safe-zone floor, which created a permanent sanctuary: two bots can rest-camp it to the 200-round cap (resolves only via tiebreaker — observed in S73 as a match hitting max=200). A 2×2 zone (4 tiles) doesn't force adjacency, and rest still HP-heals inside it. Make the clamp-induced safe zone hostile in the deep endgame so the final bots resolve by combat: disable rest HP-healing once the safe zone exists only because of the clamp (i.e., the unclamped `get_storm_border` would have closed it), so campers can't out-heal each other. Keep the mid-game 2×2 floor (the anti-premature-all-storm intent) intact, and preserve `storm_border` as an int in replays. Verify with the T74.1 kill-cause distribution that round-cap finishes drop to ~0 over a 30-seed sweep and combat decides the endgame.

**AC:**
- [ ] Rest no longer HP-heals when the safe zone is clamp-induced (unclamped border would have closed it); normal-phase rest unchanged
- [ ] 30-seed sweep: no match reaches the round cap via a 2-bot safe-zone stalemate (kill-cause/length report attached to summary)
- [ ] Mid-game 2×2 floor behavior preserved; `storm_border` stays an int; replay schema unchanged
- [ ] `test_grid.py` / `test_rounds.py` cover the clamp-induced-zone rest gate; `test_s28_integration` median/mean bounds still hold (tighten the mean ceiling if cap finishes are gone)
- [ ] `data/balance_baseline.json` regenerated; deltas recorded
- [ ] `bpsai-pair arch check` rc=0 on touched files; relevant suite green

**Depends on:** T74.1

---

### T74.3 — Give `mind` combat value (mage balance) | Cx: 12 | P2

**Description:** In S73's versatility retune, every specialist reached the 40–60% duel band vs balanced except mage (15/20/20/45), which stayed at ~87% loss because `mind` only buys energy/regen — dead weight in a stats-only fight (mage derived: HP 66 / dmg 9–21). Give `mind` a modest combat contribution so a mind-heavy build is viable without making it dominant: candidate levers (pick by measurement) — a small flat damage or to-hit contribution from mind, or mind feeding ability potency/cooldown such that it matters in the duel harness. Tune so mage lands in the 40–60% band vs balanced while the other archetypes stay in band and no archetype exceeds 2× uniform share in the T74.1 pool report. Document the chosen mechanic and the before/after duel matrix.

**AC:**
- [ ] Mage archetype within 40–60% win rate vs balanced (≥30 seeds), and all other specialists remain in band
- [ ] No archetype exceeds 2× uniform share in the T74.1 full-pool balance report
- [ ] `mind`'s new combat contribution documented in `docs/balance-mind-s74.md` with before/after duel matrix
- [ ] `test_stats.py` / `test_versatility_balance.py` updated for new derived values + mage band pinned with a fixed seed set
- [ ] `data/balance_baseline.json` regenerated; deltas recorded
- [ ] `bpsai-pair arch check engine/stats.py` rc=0; relevant suite green

**Depends on:** T74.1

---

## Delivery Summary

| Task | Title | Cx | Priority | Depends on |
|------|-------|----|----------|------------|
| T74.1 | Balance harness uses the real (equipped) pool | 13 | P0 | — |
| T74.2 | Endgame forced resolution (refine T73.7) | 13 | P1 | T74.1 |
| T74.3 | Give `mind` combat value (mage balance) | 12 | P2 | T74.1 |

**Total: ~38 Cx**

## Priority Order

1. T74.1 — close the guard blind spot first (so T74.2/T74.3 regenerate against the meaningful pool)
2. T74.2 + T74.3 — parallel after T74.1 (disjoint files: `grid.py`/`rounds.py` vs `stats.py`; only one regenerates the baseline at a time — serialize the baseline write)

**Cut-list if over budget:** T74.3 (mage balance is the least urgent; the band miss is documented). T74.1 must not be cut — it closes a blind spot in a guard that's now in CI.
