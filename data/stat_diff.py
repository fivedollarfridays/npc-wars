"""Stat diff computation and injection into match data.

compute_diff() is pure (no I/O). inject_diff_data() reads historical match
files to compute lifetime averages before diffing.
"""

__all__ = ["compute_diff", "inject_diff_data"]

_LOWER_IS_BETTER = frozenset({"damage_taken"})


def compute_diff(
    lifetime_avg: dict[str, float] | None,
    current_stats: dict[str, float],
) -> dict[str, dict]:
    """Compare current match stats against lifetime averages.

    Args:
        lifetime_avg: Stat name -> average value (may be None or empty).
        current_stats: Stat name -> current match value.

    Returns:
        Dict keyed by stat name. Each value contains:
        - classification: "improved" | "regressed" | "neutral"
        - delta: raw numeric difference (current - lifetime)
        - percentage: percent change relative to lifetime average
        If lifetime_avg is None or empty, returns first-match sentinel.
    """
    if not lifetime_avg:
        return _first_match_result(current_stats)

    all_keys = set(lifetime_avg) | set(current_stats)
    return {
        key: _diff_single(
            lifetime_avg.get(key, 0.0),
            current_stats.get(key, 0.0),
            lower_is_better=key in _LOWER_IS_BETTER,
        )
        for key in all_keys
    }


def _first_match_result(current_stats: dict[str, float]) -> dict:
    """Build result for a player's first match (no lifetime data)."""
    result: dict = {"first_match": True}
    for key, value in current_stats.items():
        result[key] = {
            "classification": "improved",
            "delta": None,
            "percentage": None,
            "current": value,
        }
    return result


def _diff_single(
    lifetime: float, current: float, *, lower_is_better: bool = False,
) -> dict[str, object]:
    """Compute diff for a single stat."""
    delta = current - lifetime
    percentage = (delta / lifetime * 100.0) if lifetime != 0.0 else None
    return {
        "classification": _classify(-delta if lower_is_better else delta),
        "delta": delta,
        "percentage": percentage,
        "lifetime_avg": lifetime,
        "current": current,
    }


def inject_diff_data(match_data: dict, results_dir: str) -> dict:
    """Compute and inject per-player stat diffs into match_data.

    Loads historical matches once and aggregates stats in a single pass,
    then computes diffs per player from the shared aggregate.

    Args:
        match_data: The match dict (must have a "stats" key).
        results_dir: Path to directory containing historical match JSON files.

    Returns:
        The same match_data dict with a "diff" key added.
    """
    from data.lifetime_stats import get_all_lifetime_stats

    stats = match_data.get("stats", {})
    all_lifetimes = get_all_lifetime_stats(results_dir)
    diffs: dict[str, dict] = {}
    for emoji, current_stats in stats.items():
        lifetime_avg = all_lifetimes.get(emoji, {})
        diffs[emoji] = compute_diff(lifetime_avg, current_stats)
    match_data["diff"] = diffs
    return match_data


def _classify(delta: float) -> str:
    """Classify a delta as improved, regressed, or neutral."""
    if delta > 0:
        return "improved"
    if delta < 0:
        return "regressed"
    return "neutral"
