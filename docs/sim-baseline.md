# Simulation Baseline Report

> **1000 matches** | seed=100 | builtin bots | sequential mode
> Generated: 2026-03-17

## Match Length

| Metric | Value |
|--------|-------|
| Average | 34.0 rounds |
| Median | 35.5 rounds |
| Min | 12 rounds |
| Max | 44 rounds |

## Winner Distribution

| Emoji | Name | Wins | Win Rate |
|-------|------|------|----------|
| --- | (draw/timeout) | 91 | 9.1% |
| :shield: | TankBot | 415 | 41.5% |
| :dart: | KiteBot | 210 | 21.0% |
| :robot: | AggroBot | 123 | 12.3% |
| :game_die: | ChaosBot | 76 | 7.6% |
| :star2: | Starter | 44 | 4.4% |
| :brain: | Cognify | 41 | 4.1% |

## Timing

| Metric | Value |
|--------|-------|
| Total wall time | 1518.8s (25.3 min) |
| Avg per match | 1.50s |
| Min per match | 0.53s |
| Max per match | 3.55s |
| Throughput | 0.66 matches/sec |

## Balance Verdicts

| Metric | Target | Actual | Verdict |
|--------|--------|--------|---------|
| Match length | 20-28 rounds | 34.0 avg | **WARN** |
| Win rate spread | No bot >60% | 41.5% max (TankBot) | **PASS** |

## Anomalies

1. **Match length WARN** -- Average of 34 rounds exceeds the 20-28 target range. Matches tend to run long (median 35.5). This suggests bots are too passive or defensive in the mid-game. The storm mechanic may not be aggressive enough to force engagements.

2. **TankBot dominance** -- TankBot wins 41.5% of matches, nearly double the next-best bot (KiteBot at 21.0%). While under the 60% FAIL threshold, this is worth monitoring. TankBot's defensive strategy clearly outperforms aggression and chaos in the current meta.

3. **9.1% draw/timeout rate** -- Nearly 1 in 10 matches end without a clear winner. This is relatively high and contributes to the long average match length.

4. **Cognify and Starter underperform** -- Both win under 5% of matches. Cognify (brain-based strategy) and Starter (template bot) are significantly weaker than the rest of the field.

## Output Files

- `docs/sim-baseline/sim_summary.json` -- Full summary with timing, placements, alive curves
- `docs/sim-baseline/analysis/analysis_report.json` -- Balance verdicts
- `docs/sim-baseline/analysis/heatmaps.json` -- Kill/death/balance grids (12x12)
- `docs/sim-baseline/analysis/energy_curves.json` -- Energy by placement tier
