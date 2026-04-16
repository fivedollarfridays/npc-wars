"""Highlight extractor — scans match rounds for high-drama moments."""

from __future__ import annotations

from typing import Any

from engine.spectacle import TIER_RANGES, SpectacleEngine

__all__ = ["extract_highlights"]

_CONTEXT_BEFORE = 2
_CONTEXT_AFTER = 1


def extract_highlights(
    match_data: dict[str, Any],
    threshold: str = "hype",
) -> list[dict[str, Any]]:
    """Extract highlights from match data. Each has round_range, trigger_type,
    participants, drama_score, commentary."""
    rounds = match_data.get("rounds", [])
    if not rounds:
        return []
    engine = SpectacleEngine()
    threshold_score = _tier_min_score(threshold)
    scored = _score_rounds(rounds, engine)
    triggers = [s for s in scored if s["drama_score"] >= threshold_score]
    if not triggers and _match_has_kill(rounds):
        triggers = _best_kill_trigger(scored)
    if not triggers:
        return []
    raw = _build_raw_highlights(triggers, scored)
    return _merge_highlights(raw)


def _tier_min_score(tier: str) -> int:
    for low, _high, name in TIER_RANGES:
        if name == tier:
            return low
    return 10


def _score_rounds(rounds: list[dict[str, Any]], engine: SpectacleEngine) -> list[dict[str, Any]]:
    scored = []
    for rnd in rounds:
        events = rnd.get("events", [])
        positions = rnd.get("positions", [])
        bots = [{"emoji": p.get("emoji", "?"), "hp": p.get("hp", 0),
                 "alive": p.get("alive", True)} for p in positions]
        sp = engine.score_round(events, bots)
        scored.append({
            "round_num": rnd.get("round", 0), "events": events,
            "positions": positions, "drama_score": sp.drama_score,
            "tier": sp.tier, "triggers": sp.triggers, "near_deaths": sp.near_deaths,
        })
    return scored


def _match_has_kill(rounds: list[dict[str, Any]]) -> bool:
    return any(e.get("type") == "kill" for r in rounds for e in r.get("events", []))


def _best_kill_trigger(scored: list[dict[str, Any]]) -> list[dict[str, Any]]:
    kill_rounds = [s for s in scored if any(e.get("type") == "kill" for e in s["events"])]
    if not kill_rounds:
        return []
    return [max(kill_rounds, key=lambda s: s["drama_score"])]


def _build_raw_highlights(
    triggers: list[dict[str, Any]], scored: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    round_nums = [s["round_num"] for s in scored]
    first_round, last_round = min(round_nums), max(round_nums)
    highlights = []
    for t in triggers:
        rnum = t["round_num"]
        start = max(first_round, rnum - _CONTEXT_BEFORE)
        end = min(last_round, rnum + _CONTEXT_AFTER)
        highlights.append({
            "round_range": (start, end),
            "trigger_type": _classify_trigger(t),
            "participants": _extract_participants(t),
            "drama_score": t["drama_score"],
            "commentary": _extract_commentary(t),
        })
    return highlights


def _classify_trigger(sr: dict[str, Any]) -> str:
    for evt in sr["events"]:
        if evt.get("type") == "kill":
            return "kill"
    if sr["near_deaths"]:
        return "near_death"
    for evt in sr["events"]:
        etype = evt.get("type", "")
        if etype == "chain_bump":
            return "chain_bump"
        if etype.startswith("watcher"):
            return "watcher_event"
    return "drama"


def _extract_participants(sr: dict[str, Any]) -> list[str]:
    participants: set[str] = set()
    for evt in sr["events"]:
        for key in ("attacker", "victim", "target"):
            val = evt.get(key)
            if val:
                participants.add(val)
    for nd in sr["near_deaths"]:
        participants.add(nd)
    for pos in sr["positions"]:
        if pos.get("alive") and pos.get("hp", 999) < 10:
            participants.add(pos.get("emoji", "?"))
    return sorted(participants)


def _extract_commentary(sr: dict[str, Any]) -> list[str]:
    snippets: list[str] = []
    for evt in sr["events"]:
        etype = evt.get("type", "")
        if etype == "kill":
            snippets.append(f"{evt.get('attacker', '?')} eliminates {evt.get('victim', '?')}")
        elif etype == "chain_bump":
            snippets.append("Chain bump chaos!")
        elif etype.startswith("watcher"):
            snippets.append(f"Watcher event: {etype}")
    for nd in sr["near_deaths"]:
        snippets.append(f"{nd} barely survives")
    return snippets


def _merge_highlights(highlights: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not highlights:
        return []
    sorted_hl = sorted(highlights, key=lambda h: h["round_range"][0])
    merged: list[dict[str, Any]] = [sorted_hl[0]]
    for hl in sorted_hl[1:]:
        prev = merged[-1]
        if hl["round_range"][0] <= prev["round_range"][1]:
            merged[-1] = _merge_two(prev, hl)
        else:
            merged.append(hl)
    return merged


def _merge_two(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    start = min(a["round_range"][0], b["round_range"][0])
    end = max(a["round_range"][1], b["round_range"][1])
    all_participants = sorted(set(a["participants"]) | set(b["participants"]))
    all_commentary = a["commentary"] + [c for c in b["commentary"] if c not in a["commentary"]]
    trigger = a["trigger_type"] if a["drama_score"] >= b["drama_score"] else b["trigger_type"]
    return {
        "round_range": (start, end), "trigger_type": trigger,
        "participants": all_participants,
        "drama_score": max(a["drama_score"], b["drama_score"]),
        "commentary": all_commentary,
    }
