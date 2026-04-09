"""Code Circuit commentary — generate commentary from race replay and events.

Produces platform CommentaryLine objects from Code Circuit race data,
conforming to the shared commentary contract.
"""

from __future__ import annotations

from typing import Any

from engine.platform_commentary import CommentaryLine

__all__ = ["generate_circuit_commentary"]

_EVENT_TONES: dict[str, str] = {
    "OVERTAKE": "intense",
    "BATTLE": "hype",
    "SPIN": "heating",
    "SAFETY_CAR": "chaos",
    "PIT_STOP": "calm",
    "FASTEST_LAP": "heating",
}

_EVENT_TEMPLATES: dict[str, str] = {
    "OVERTAKE": "{a} overtakes {b} for position!",
    "BATTLE": "{a} and {b} locked in a fierce battle!",
    "SPIN": "{a} spins!",
    "SAFETY_CAR": "Safety car deployed!",
    "PIT_STOP": "{a} dives into the pits.",
    "FASTEST_LAP": "{a} sets the fastest lap!",
}


def generate_circuit_commentary(
    replay: dict[str, Any],
    race_events: list[Any],
) -> list[CommentaryLine]:
    """Generate commentary for a Code Circuit race.

    Returns a list of CommentaryLine ordered by timestamp.
    """
    tps = replay.get("ticks_per_sec", 30)
    lines: list[CommentaryLine] = []

    for evt in race_events:
        etype = evt.type
        if etype not in _EVENT_TONES:
            continue
        ts = round(evt.tick / tps, 2)
        cars = list(evt.cars)
        tone = _EVENT_TONES[etype]
        text = _EVENT_TEMPLATES[etype].format(
            a=cars[0] if cars else "?",
            b=cars[1] if len(cars) > 1 else "?",
        )
        lines.append(CommentaryLine(
            timestamp=ts, text=text, tone=tone, line_type="play_by_play",
        ))

    # Results summary as analysis line
    results = replay.get("results", [])
    if results:
        winner = results[0].get("car", "?")
        lines.append(CommentaryLine(
            timestamp=float(len(lines)),
            text=f"{winner} takes the chequered flag!",
            tone="hype",
            line_type="analysis",
        ))

    return lines
