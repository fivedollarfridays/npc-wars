"""Balance report helpers for the sim runner (T73.3).

Pure aggregation over match results — no I/O. Builds a win-rate matrix
keyed by bot and by stat-archetype, plus a kill-cause distribution, so a
balance patch that swings one build's win rate is caught by CI rather
than discovered in production.
"""
from __future__ import annotations

from typing import Any

__all__ = [
    "classify_kill_cause",
    "archetype_map",
    "build_balance_report",
]

# Win rates are rounded to this many decimals so reports are byte-stable
# across runs with a fixed seed (avoids float repr drift in JSON).
_RATE_PRECISION = 6
_KILL_CAUSES = ("combat", "storm", "disconnect", "tiebreaker")


def _was_disconnect(match_data: dict[str, Any], emoji: str, round_num: Any) -> bool:
    """True if the bot's recorded action in its death round was a disconnect."""
    for rnd in match_data.get("rounds", []):
        if rnd.get("round") != round_num:
            continue
        for pos in rnd.get("positions", []):
            if pos.get("emoji") == emoji:
                return str(pos.get("action", "")).startswith("disconnected")
    return False


def classify_kill_cause(match_data: dict[str, Any], elim: dict[str, Any]) -> str:
    """Classify one elimination as combat / storm / disconnect / tiebreaker.

    The engine only records ``cause`` as combat/storm/tiebreaker; a bot that
    fails to act is killed with ``cause="combat"`` and ``killed_by="unknown"``.
    We recover the disconnect case from the round's recorded action.
    """
    cause = elim.get("cause", "combat")
    if cause in ("storm", "tiebreaker"):
        return cause
    if _was_disconnect(match_data, elim.get("emoji", ""), elim.get("round")):
        return "disconnect"
    return "combat"


def archetype_map(bots: list[dict[str, Any]]) -> dict[str, str]:
    """Map each bot emoji to its stat archetype via classify_archetype."""
    from engine.archetype import classify_archetype

    return {b["emoji"]: classify_archetype(b["stat_allocation"]) for b in bots}


def _count_wins(
    match_results: list[dict[str, Any]],
    emojis: list[str],
    arch: dict[str, str],
) -> tuple[dict[str, int], dict[str, int]]:
    """Tally per-bot and per-archetype win counts."""
    win_counts: dict[str, int] = {e: 0 for e in emojis}
    arch_wins: dict[str, int] = {}
    for m in match_results:
        winner = m.get("winner")
        if winner in win_counts:
            win_counts[winner] += 1
        a = arch.get(winner)
        if a is not None:
            arch_wins[a] = arch_wins.get(a, 0) + 1
    return win_counts, arch_wins


def _count_kill_causes(match_results: list[dict[str, Any]]) -> dict[str, int]:
    """Tally kill-cause distribution across every elimination."""
    dist: dict[str, int] = {c: 0 for c in _KILL_CAUSES}
    for m in match_results:
        for elim in m.get("eliminations", []):
            cause = classify_kill_cause(m, elim)
            dist[cause] = dist.get(cause, 0) + 1
    return dist


def build_balance_report(
    match_results: list[dict[str, Any]],
    bots: list[dict[str, Any]],
    *,
    matches: int,
    seed: int | None,
) -> dict[str, Any]:
    """Build the balance report dict from raw match results + bot configs.

    Win rate is ``wins / matches`` (per-bot and per-archetype share of the
    pool's total wins). Deterministic for a fixed seed and match count.
    """
    arch = archetype_map(bots)
    emojis = [b["emoji"] for b in bots]
    win_counts, arch_wins = _count_wins(match_results, emojis, arch)
    n = len(match_results)

    def rate(count: int) -> float:
        return round(count / n, _RATE_PRECISION) if n else 0.0

    per_bot = {e: rate(win_counts[e]) for e in emojis}
    per_arch = {a: rate(arch_wins.get(a, 0)) for a in sorted(set(arch.values()))}

    return {
        "matches": matches,
        "seed": seed,
        "bots": emojis,
        "per_bot_win_rate": per_bot,
        "per_archetype_win_rate": per_arch,
        "kill_cause_distribution": _count_kill_causes(match_results),
    }
