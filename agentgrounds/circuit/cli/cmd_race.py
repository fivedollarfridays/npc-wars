"""agentgrounds circuit race -- run a Code Circuit race."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

__all__ = ["register", "run"]


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the race subcommand."""
    p = subparsers.add_parser(
        "race", help="Run a Code Circuit race",
    )
    p.add_argument(
        "--cars-dir", type=str, default="cars",
        help="Cars directory (default: cars)",
    )
    p.add_argument(
        "--laps", type=int, default=5,
        help="Number of laps (default: 5)",
    )
    p.add_argument(
        "--seed", type=int, default=None,
        help="Random seed for deterministic races",
    )
    p.add_argument(
        "--no-tv", action="store_true",
        help="Skip TV generation (commentary, highlights)",
    )
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> None:
    """Execute the race command."""
    car_configs = _load_cars(args.cars_dir)

    from engine.circuit import run_race

    race_data = run_race(car_configs=car_configs, laps=args.laps, seed=args.seed)

    if not args.no_tv:
        from engine.circuit_tv import enrich_circuit_tv

        enrich_circuit_tv(race_data)

    race_data.setdefault("match_id", int(time.time()))

    from engine.broadcast_inbox import write_to_inbox

    write_to_inbox(race_data, "circuit")

    _print_results(race_data)


def _load_cars(cars_dir: str) -> list[dict]:
    """Load car configs from directory, or use builtins."""
    cars_path = Path(cars_dir)
    if cars_path.is_dir():
        configs = []
        for f in sorted(cars_path.glob("*.json")):
            with open(f) as fh:
                configs.append(json.load(fh))
        if configs:
            return configs

    # Fallback: builtin cars
    return [
        {"name": "Blaze", "emoji": "🔥", "strategy": "aggressive"},
        {"name": "Glacier", "emoji": "🧊", "strategy": "conservative"},
        {"name": "Phantom", "emoji": "👻", "strategy": "balanced"},
        {"name": "Volt", "emoji": "⚡", "strategy": "aggressive"},
    ]


def _print_results(race_data: dict) -> None:
    """Print race results summary."""
    print(f"\n  Code Circuit — {race_data['laps']} laps")
    print()
    for r in race_data["results"]:
        marker = " 🏆" if r["position"] == 1 else ""
        print(f"  P{r['position']}  {r['car']} {r['name']}  {r['time']}s{marker}")
    print()

    commentary = race_data.get("commentary", [])
    if commentary:
        print("  Highlights:")
        for line in commentary[:5]:
            print(f"    [{line['tone']}] {line['text']}")
        print()
