#!/usr/bin/env python3
"""Balance regression gate (T73.3).

Compare a fresh balance report against the checked-in baseline and fail
(exit non-zero) when any bot's win rate has moved more than the threshold
(default ±15 percentage points). This turns "a balance patch made one build
win 77%" into a CI failure rather than a production discovery.

Usage:
    python scripts/check_balance.py --report balance_report.json
    python scripts/check_balance.py --report fresh.json --threshold 0.10
"""
from __future__ import annotations

import argparse
import json
import sys

DEFAULT_BASELINE = "data/balance_baseline.json"
DEFAULT_THRESHOLD = 0.15  # 15 percentage points

# (emoji, baseline_rate, fresh_rate, delta)
Failure = tuple


def _load(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def compare(baseline: dict, report: dict, threshold: float) -> list[Failure]:
    """Return per-bot win-rate moves that exceed the threshold."""
    base_rates: dict = baseline.get("per_bot_win_rate", {})
    fresh_rates: dict = report.get("per_bot_win_rate", {})
    failures: list[Failure] = []
    for emoji in sorted(set(base_rates) | set(fresh_rates)):
        base = base_rates.get(emoji, 0.0)
        fresh = fresh_rates.get(emoji, 0.0)
        delta = fresh - base
        if abs(delta) > threshold:
            failures.append((emoji, base, fresh, delta))
    return failures


def _report_failures(failures: list[Failure], threshold: float) -> None:
    pp = threshold * 100
    print(f"BALANCE REGRESSION: {len(failures)} bot(s) moved more than ±{pp:.1f}pp")
    for emoji, base, fresh, delta in failures:
        print(f"  {emoji}: {base * 100:.1f}% -> {fresh * 100:.1f}% ({delta * 100:+.1f}pp)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Balance regression gate")
    parser.add_argument("--baseline", default=DEFAULT_BASELINE, help="Baseline report path")
    parser.add_argument("--report", required=True, help="Fresh balance report path")
    parser.add_argument(
        "--threshold", type=float, default=DEFAULT_THRESHOLD,
        help="Max allowed win-rate move as a fraction (default: 0.15 = 15pp)",
    )
    args = parser.parse_args(argv)

    baseline = _load(args.baseline)
    report = _load(args.report)
    failures = compare(baseline, report, args.threshold)

    if failures:
        _report_failures(failures, args.threshold)
        return 1
    print(f"OK: no bot moved more than ±{args.threshold * 100:.1f}pp from baseline")
    return 0


if __name__ == "__main__":
    sys.exit(main())
