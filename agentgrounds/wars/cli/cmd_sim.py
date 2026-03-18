"""agentgrounds wars sim -- batch match runner with aggregate stats."""
from __future__ import annotations

import argparse
import json
import os
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import cpu_count
from pathlib import Path
from typing import Any

__all__ = ["register", "run_sim"]


def register(subparser: argparse._SubParsersAction) -> None:
    """Register the sim subcommand."""
    p = subparser.add_parser("sim", help="Run batch simulation matches")
    p.add_argument("--matches", type=int, default=10, help="Number of matches (default: 10)")
    p.add_argument("--output", type=str, default=None, help="Output directory (default: sim_results)")
    p.add_argument("--seed", type=int, default=None, help="Base random seed for reproducibility")
    p.add_argument("--bots-dir", type=str, default=None, help="Directory containing bots")
    p.add_argument("--parallel", action="store_true", help="Run matches in parallel")
    p.add_argument("--quiet", action="store_true", help="Suppress progress output")
    p.set_defaults(func=_run_cli)


def _run_cli(args: argparse.Namespace) -> None:
    """CLI entry point — resolves config then delegates to run_sim."""
    from agentgrounds.wars.config import CONFIG_FILENAME, load_config

    config = load_config(Path(CONFIG_FILENAME))
    bots_dir = args.bots_dir or config["bots_dir"]
    output_dir = args.output or "sim_results"
    seed = args.seed if args.seed is not None else config.get("seed")

    run_sim(
        bots_dir=bots_dir,
        matches=args.matches,
        output_dir=output_dir,
        seed=seed,
        parallel=args.parallel,
        quiet=args.quiet,
    )


def _run_single_match(params: tuple[str, int, int | None]) -> dict[str, Any]:
    """Run one match. Accepts (bots_dir, match_index, seed) for pool.map compatibility."""
    bots_dir, match_index, seed = params
    from engine.game import run_match
    from engine.loader import load_bots

    bot_configs = load_bots(bots_dir)
    t0 = time.perf_counter()
    match_data = run_match(bot_configs, match_id=match_index, seed=seed)
    match_data["_wall_time_s"] = time.perf_counter() - t0
    return match_data


def _write_match_file(output_dir: str, match_index: int, match_data: dict[str, Any]) -> None:
    """Write a single match result to JSON."""
    filename = f"match_{match_index:04d}.json"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(match_data, f, indent=2)


def _compute_summary(
    match_results: list[dict[str, Any]],
    total_wall_time: float,
) -> dict[str, Any]:
    """Compute aggregate statistics from match results."""
    durations = [m["duration_rounds"] for m in match_results]
    winners = [m["winner"] for m in match_results]

    winner_dist: dict[str, int] = {}
    for w in winners:
        winner_dist[w] = winner_dist.get(w, 0) + 1

    placement_dist = _compute_placements(match_results)
    alive_by_round = _compute_avg_alive_by_round(match_results)

    match_times = [m.get("_wall_time_s", 0.0) for m in match_results]
    n = len(match_results)

    return {
        "total_matches": n,
        "avg_match_length": statistics.mean(durations),
        "median_match_length": statistics.median(durations),
        "min_match_length": min(durations),
        "max_match_length": max(durations),
        "winner_distribution": winner_dist,
        "placement_distribution": placement_dist,
        "avg_agents_alive_by_round": alive_by_round,
        "timing": {
            "total_duration_s": round(total_wall_time, 4),
            "match_durations_s": [round(t, 4) for t in match_times],
            "avg_match_duration_s": round(statistics.mean(match_times), 4) if match_times else 0.0,
            "min_match_duration_s": round(min(match_times), 4) if match_times else 0.0,
            "max_match_duration_s": round(max(match_times), 4) if match_times else 0.0,
            "matches_per_second": round(n / total_wall_time, 2) if total_wall_time > 0 else 0.0,
        },
    }


def _compute_placements(match_results: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    """Compute placement distribution: emoji -> {rank -> count}."""
    placements: dict[str, dict[str, int]] = {}
    for m in match_results:
        elims = m.get("eliminations", [])
        players = [p["emoji"] for p in m["players"]]
        n = len(players)
        # Eliminated bots get placement based on elimination order (first out = last place)
        placed: dict[str, int] = {}
        for rank_from_bottom, elim in enumerate(elims):
            placed[elim["emoji"]] = n - rank_from_bottom
        # Winner (or survivors) get rank 1
        for emoji in players:
            if emoji not in placed:
                placed[emoji] = 1

        for emoji, rank in placed.items():
            if emoji not in placements:
                placements[emoji] = {}
            rank_str = str(rank)
            placements[emoji][rank_str] = placements[emoji].get(rank_str, 0) + 1

    return placements


def _compute_avg_alive_by_round(match_results: list[dict[str, Any]]) -> list[float]:
    """Compute average agents alive at each round across all matches."""
    if not match_results:
        return []
    max_rounds = max(len(m.get("rounds", [])) for m in match_results)
    alive_sums = [0.0] * max_rounds
    counts = [0] * max_rounds

    for m in match_results:
        rounds = m.get("rounds", [])
        for i, rnd in enumerate(rounds):
            positions = rnd.get("positions", [])
            alive_count = sum(1 for p in positions if p.get("alive", True))
            alive_sums[i] += alive_count
            counts[i] += 1

    return [alive_sums[i] / counts[i] if counts[i] > 0 else 0.0 for i in range(max_rounds)]


def _print_summary_table(summary: dict[str, Any]) -> None:
    """Print a human-readable summary table to stdout."""
    print(f"\n{'=' * 50}")
    print("Simulation Summary")
    print(f"{'=' * 50}")
    print(f"Total matches:  {summary['total_matches']}")
    print(f"Match length:   avg={summary['avg_match_length']:.1f}  "
          f"med={summary['median_match_length']:.1f}  "
          f"min={summary['min_match_length']}  "
          f"max={summary['max_match_length']}")
    timing = summary.get("timing", {})
    if timing:
        print("\nTiming:")
        print(f"  Total:     {timing['total_duration_s']:.2f}s")
        print(f"  Per match: avg={timing['avg_match_duration_s']:.3f}s  "
              f"min={timing['min_match_duration_s']:.3f}s  "
              f"max={timing['max_match_duration_s']:.3f}s")
        print(f"  Throughput: {timing['matches_per_second']:.1f} matches/sec")
    print("\nWinner distribution:")
    for emoji, count in sorted(summary["winner_distribution"].items(), key=lambda x: -x[1]):
        pct = count / summary["total_matches"] * 100
        print(f"  {emoji}: {count} wins ({pct:.1f}%)")
    print(f"{'=' * 50}")


def run_sim(
    bots_dir: str,
    matches: int = 10,
    output_dir: str = "sim_results",
    seed: int | None = None,
    parallel: bool = False,
    quiet: bool = False,
) -> dict[str, Any]:
    """Run N matches and write per-match results + aggregate stats.

    Returns the summary dict.
    """
    bots_path = Path(bots_dir)
    if not bots_path.is_dir():
        raise FileNotFoundError(f"Bots directory not found: {bots_dir}")

    os.makedirs(output_dir, exist_ok=True)

    # Build params: (bots_dir, match_index, seed_for_match)
    params = [
        (bots_dir, i, (seed + i) if seed is not None else None)
        for i in range(1, matches + 1)
    ]

    t_start = time.perf_counter()
    if parallel:
        match_results = _run_parallel(params, matches, quiet)
    else:
        match_results = _run_sequential(params, matches, output_dir, quiet)
    total_wall_time = time.perf_counter() - t_start

    # For parallel mode, write files after (sequential writes during)
    if parallel:
        for i, result in enumerate(match_results, start=1):
            _write_match_file(output_dir, i, result)

    summary = _compute_summary(match_results, total_wall_time)
    summary_path = os.path.join(output_dir, "sim_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    if not quiet:
        _print_summary_table(summary)

    return summary


def _run_sequential(
    params: list[tuple[str, int, int | None]],
    matches: int,
    output_dir: str,
    quiet: bool,
) -> list[dict[str, Any]]:
    """Run matches sequentially, writing each file as we go."""
    results: list[dict[str, Any]] = []
    for idx, p in enumerate(params, start=1):
        result = _run_single_match(p)
        _write_match_file(output_dir, idx, result)
        results.append(result)
        if not quiet:
            print(f"\r{idx}/{matches} matches complete", end="", flush=True)
    if not quiet:
        print()
    return results


def _run_parallel(
    params: list[tuple[str, int, int | None]],
    matches: int,
    quiet: bool,
) -> list[dict[str, Any]]:
    """Run matches using ThreadPoolExecutor (threads, not processes).

    We use threads because the engine sandbox spawns child processes
    internally, and daemonic pool workers cannot spawn children.
    """
    pool_size = min(cpu_count() or 4, 8)
    if not quiet:
        print(f"Running {matches} matches with {pool_size} workers...")
    with ThreadPoolExecutor(max_workers=pool_size) as executor:
        results = list(executor.map(_run_single_match, params))
    if not quiet:
        print(f"{matches}/{matches} matches complete")
    return results
