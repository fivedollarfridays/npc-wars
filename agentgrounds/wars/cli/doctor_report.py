"""Diagnostic signal extraction + formatting for ``killswitch doctor``.

Pure helpers over already-produced ``match_data`` dicts — adds NO engine
behavior. Each match's per-bot signals are read straight from
``round["events"]``, ``round["positions"]``, and ``eliminations``.

Signals (all keyed by the target bot's emoji):
  * locked-action attempts -- events ``type=="locked_action"``, ``player==emoji``
  * plague rounds          -- events ``type=="plague"``, ``emoji==emoji``
  * storm damage           -- events ``type=="storm_damage"``, ``target==emoji``
  * storm deaths           -- eliminations ``cause=="storm"`` and ``emoji==emoji``
  * disconnects            -- a position with ``action=="disconnected"``
  * forced-rest rounds     -- a "rest" position whose *prior* round energy was
                              below the move cost (the engine forces a rest when
                              a bot cannot afford any action).
"""
from __future__ import annotations

from typing import Any

__all__ = ["analyze_match", "aggregate_runs", "format_report"]

_MOVE_COST = 5  # engine MOVE_COST: a bot with energy < this is forced to rest


def _placement(match_data: dict[str, Any], emoji: str) -> int:
    """Return the target bot's placement (1 == winner / last standing)."""
    elims = match_data.get("eliminations", [])
    players = [p["emoji"] for p in match_data.get("players", [])]
    n = len(players)
    for rank_from_bottom, elim in enumerate(elims):
        if elim["emoji"] == emoji:
            return n - rank_from_bottom
    return 1  # survivor / winner


def _forced_rest_rounds(match_data: dict[str, Any], emoji: str) -> int:
    """Count rounds where the bot was forced to rest (prior energy < move cost)."""
    forced = 0
    prev_energy: float | None = None
    for rnd in match_data.get("rounds", []):
        pos = _find_pos(rnd, emoji)
        if pos is None:
            continue
        if prev_energy is not None and prev_energy < _MOVE_COST and pos.get("action") == "rest":
            forced += 1
        prev_energy = pos.get("energy")
    return forced


def _find_pos(rnd: dict[str, Any], emoji: str) -> dict[str, Any] | None:
    for p in rnd.get("positions", []):
        if p.get("emoji") == emoji:
            return p
    return None


def _disconnected(match_data: dict[str, Any], emoji: str) -> bool:
    for rnd in match_data.get("rounds", []):
        pos = _find_pos(rnd, emoji)
        if pos is not None and pos.get("action") == "disconnected":
            return True
    return False


def _storm_deaths(match_data: dict[str, Any], emoji: str) -> int:
    return sum(
        1
        for e in match_data.get("eliminations", [])
        if e.get("emoji") == emoji and e.get("cause") == "storm"
    )


def _event_signals(match_data: dict[str, Any], emoji: str) -> tuple[int, int, float]:
    """Return (locked_action_attempts, plague_rounds, storm_damage) from events."""
    locked = 0
    plague = 0
    storm_dmg = 0.0
    for rnd in match_data.get("rounds", []):
        for ev in rnd.get("events", []):
            etype = ev.get("type")
            if etype == "locked_action" and ev.get("player") == emoji:
                locked += 1
            elif etype == "plague" and ev.get("emoji") == emoji:
                plague += 1
            elif etype == "storm_damage" and ev.get("target") == emoji:
                storm_dmg += ev.get("damage", 0)
    return locked, plague, round(storm_dmg, 1)


def analyze_match(match_data: dict[str, Any], emoji: str) -> dict[str, Any]:
    """Extract one match's diagnostic signals for the target bot."""
    locked, plague, storm_dmg = _event_signals(match_data, emoji)
    return {
        "match_id": match_data.get("match_id"),
        "placement": _placement(match_data, emoji),
        "locked_action_attempts": locked,
        "plague_rounds": plague,
        "forced_rest_rounds": _forced_rest_rounds(match_data, emoji),
        "storm_damage": storm_dmg,
        "storm_deaths": _storm_deaths(match_data, emoji),
        "disconnects": 1 if _disconnected(match_data, emoji) else 0,
    }


_SUM_KEYS = (
    "locked_action_attempts",
    "plague_rounds",
    "forced_rest_rounds",
    "storm_damage",
    "storm_deaths",
    "disconnects",
)


def aggregate_runs(runs: list[dict[str, Any]]) -> dict[str, Any]:
    """Sum per-match signals into an aggregate report block."""
    agg: dict[str, Any] = {k: 0 for k in _SUM_KEYS}
    placements: dict[str, int] = {}
    for run in runs:
        for k in _SUM_KEYS:
            agg[k] += run.get(k, 0)
        rank = str(run.get("placement", "?"))
        placements[rank] = placements.get(rank, 0) + 1
    agg["storm_damage"] = round(agg["storm_damage"], 1)
    agg["placement_distribution"] = placements
    return agg


def _format_per_run(runs: list[dict[str, Any]]) -> list[str]:
    lines = ["Per-match:"]
    header = (
        f"  {'match':>6}  {'place':>5}  {'locked':>6}  "
        f"{'plague':>6}  {'rest':>4}  {'stormDmg':>8}  {'death':>5}  {'disc':>4}"
    )
    lines.append(header)
    for r in runs:
        lines.append(
            f"  {str(r.get('match_id', '?')):>6}  {r['placement']:>5}  "
            f"{r['locked_action_attempts']:>6}  {r['plague_rounds']:>6}  "
            f"{r['forced_rest_rounds']:>4}  {r['storm_damage']:>8.1f}  "
            f"{r['storm_deaths']:>5}  {r['disconnects']:>4}"
        )
    return lines


def _format_aggregate(agg: dict[str, Any]) -> list[str]:
    placements = ", ".join(
        f"#{k}x{v}" for k, v in sorted(agg["placement_distribution"].items())
    )
    return [
        "Aggregate:",
        f"  locked-action attempts : {agg['locked_action_attempts']}",
        f"  plague rounds          : {agg['plague_rounds']}",
        f"  forced-rest rounds     : {agg['forced_rest_rounds']}",
        f"  storm damage taken     : {agg['storm_damage']:.1f}",
        f"  storm deaths           : {agg['storm_deaths']}",
        f"  disconnects            : {agg['disconnects']}",
        f"  placements             : {placements or '(none)'}",
    ]


def format_report(report: dict[str, Any]) -> str:
    """Render a human-readable diagnostic report for bot authors."""
    bar = "=" * 56
    head = [
        bar,
        f"Doctor report for {report['name']} {report['emoji']}",
        f"{report['matches']} matches  seed={report['seed']}  pool={report['pool_dir']}",
        bar,
    ]
    body = _format_per_run(report["runs"]) + [""] + _format_aggregate(report["aggregate"])
    verdict = "HEALTHY" if report["healthy"] else "ISSUES FOUND"
    foot = [bar, f"Verdict: {verdict}", bar]
    return "\n".join(head + [""] + body + [""] + foot)
