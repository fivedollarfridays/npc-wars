"""Analysis engine for batch sim results — heatmaps, energy curves, balance."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


def load_matches(input_dir: Path) -> list[dict]:
    """Load all match_*.json files from a directory."""
    files = sorted(input_dir.glob("match_*.json"))
    return [json.loads(f.read_text()) for f in files]


def detect_grid_size(matches: list[dict]) -> int:
    """Detect grid size from match data (uses first match)."""
    if not matches:
        return 10
    return matches[0].get("grid_size", 10)


def _zero_grid(size: int) -> list[list[int]]:
    return [[0] * size for _ in range(size)]


def _find_position(positions: list[dict], emoji: str) -> tuple[int, int] | None:
    """Find x, y for an emoji in a round's positions list."""
    for p in positions:
        if p["emoji"] == emoji:
            return p["x"], p["y"]
    return None


def build_heatmaps(matches: list[dict], grid_size: int) -> dict[str, list[list[int]]]:
    """Build kill, death, and balance heatmaps from match data."""
    kill_grid = _zero_grid(grid_size)
    death_grid = _zero_grid(grid_size)

    for match in matches:
        for rnd in match.get("rounds", []):
            positions = rnd.get("positions", [])
            for event in rnd.get("events", []):
                if event["type"] == "kill":
                    attacker = event.get("attacker")
                    victim = event["victim"]
                    # Kill heatmap: where the attacker stood when they got the kill
                    if attacker and attacker != "storm":
                        attacker_pos = _find_position(positions, attacker)
                        if attacker_pos:
                            ax, ay = attacker_pos
                            if 0 <= ax < grid_size and 0 <= ay < grid_size:
                                kill_grid[ay][ax] += 1
                    # Death heatmap: where the victim was eliminated
                    victim_pos = _find_position(positions, victim)
                    if victim_pos:
                        vx, vy = victim_pos
                        if 0 <= vx < grid_size and 0 <= vy < grid_size:
                            death_grid[vy][vx] += 1

    balance_grid = _zero_grid(grid_size)
    for y in range(grid_size):
        for x in range(grid_size):
            balance_grid[y][x] = kill_grid[y][x] - death_grid[y][x]

    return {"kill": kill_grid, "death": death_grid, "balance": balance_grid}


def _get_placement(match: dict, emoji: str) -> int:
    """Determine placement (1=winner, then by elimination order)."""
    if match.get("winner") == emoji:
        return 1
    elims = match.get("eliminations", [])
    # Later elimination = better placement
    elim_order = [e["emoji"] for e in elims]
    if emoji in elim_order:
        idx = elim_order.index(emoji)
        num_players = len(match.get("players", []))
        return num_players - idx
    return len(match.get("players", []))


def _placement_tier(placement: int) -> str:
    """Map placement to tier key for energy curve grouping."""
    if placement == 1:
        return "placement_1"
    if placement <= 3:
        return "placement_2_3"
    if placement <= 6:
        return "placement_4_6"
    return "placement_7_plus"


def build_energy_curves(matches: list[dict]) -> dict[str, list[float]]:
    """Build avg energy per round for each placement tier."""
    tier_round_energy: dict[str, dict[int, list[int]]] = {}

    for match in matches:
        players = match.get("players", [])
        for player in players:
            emoji = player["emoji"]
            placement = _get_placement(match, emoji)
            tier = _placement_tier(placement)
            if tier not in tier_round_energy:
                tier_round_energy[tier] = {}
            for rnd in match.get("rounds", []):
                rnum = rnd["round"]
                for pos in rnd.get("positions", []):
                    if pos["emoji"] == emoji and pos.get("alive", False):
                        tier_round_energy[tier].setdefault(rnum, []).append(pos["energy"])

    result: dict[str, list[float]] = {}
    for tier, rounds_data in tier_round_energy.items():
        max_round = max(rounds_data.keys()) if rounds_data else 0
        avgs = []
        for r in range(1, max_round + 1):
            vals = rounds_data.get(r, [])
            avgs.append(sum(vals) / len(vals) if vals else 0.0)
        result[tier] = avgs

    return result


def render_ascii_heatmap(grid: list[list[int]], title: str) -> str:
    """Render a 2D grid as ASCII with intensity characters."""
    chars = "\u00b7\u2591\u2592\u2593\u2588"  # middle dot, light, medium, dark, full
    flat = [v for row in grid for v in row]
    max_val = max(flat) if flat and max(flat) > 0 else 1
    lines = [title]
    for row in grid:
        cells = []
        for v in row:
            idx = min(int(v / max_val * (len(chars) - 1)), len(chars) - 1) if max_val > 0 else 0
            cells.append(chars[idx])
        lines.append(" ".join(cells))
    return "\n".join(lines)


def build_balance_verdict(matches: list[dict]) -> dict[str, dict[str, Any]]:
    """Compute balance verdict: match length and win rate spread."""
    durations = [m.get("duration_rounds", 0) for m in matches]
    avg_duration = sum(durations) / len(durations) if durations else 0

    win_counts: Counter[str] = Counter()
    for m in matches:
        winner = m.get("winner")
        if winner:
            # Map emoji to name
            for p in m.get("players", []):
                if p["emoji"] == winner:
                    win_counts[p["name"]] += 1
                    break

    total = len(matches)
    max_rate = max(win_counts.values()) / total if total and win_counts else 0

    length_verdict = "PASS" if 20 <= avg_duration <= 28 else ("WARN" if 15 <= avg_duration <= 35 else "FAIL")
    rate_verdict = "PASS" if max_rate <= 0.6 else ("WARN" if max_rate <= 0.75 else "FAIL")

    return {
        "match_length": {
            "avg": avg_duration,
            "target": "20-28",
            "verdict": length_verdict,
        },
        "win_rate_spread": {
            "max_win_rate": round(max_rate, 3),
            "threshold": 0.6,
            "win_counts": dict(win_counts),
            "verdict": rate_verdict,
        },
    }


def run_analysis(
    input_dir: Path,
    output_dir: Path,
    fmt: str = "both",
) -> dict[str, Any]:
    """Run full analysis pipeline and write output files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    matches = load_matches(input_dir)
    grid_size = detect_grid_size(matches)

    heatmaps = build_heatmaps(matches, grid_size)
    energy = build_energy_curves(matches)
    verdict = build_balance_verdict(matches)

    report = {
        "match_count": len(matches),
        "grid_size": grid_size,
        "verdict": verdict,
    }

    if fmt in ("json", "both"):
        (output_dir / "heatmaps.json").write_text(json.dumps(heatmaps, indent=2))
        (output_dir / "energy_curves.json").write_text(json.dumps(energy, indent=2))
        (output_dir / "analysis_report.json").write_text(json.dumps(report, indent=2))

    ascii_output = ""
    if fmt in ("ascii", "both"):
        for name in ("kill", "death", "balance"):
            ascii_output += render_ascii_heatmap(heatmaps[name], title=name.upper()) + "\n\n"

    return {"report": report, "ascii": ascii_output}
