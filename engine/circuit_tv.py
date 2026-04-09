"""Code Circuit TV enrichment — add commentary and highlights to race data.

Mirrors engine.tv_pipeline.enrich_tv but for Code Circuit races.
"""

from __future__ import annotations

from typing import Any

from engine.circuit import RaceEvent
from engine.circuit_commentary import generate_circuit_commentary

__all__ = ["enrich_circuit_tv"]


def enrich_circuit_tv(race_data: dict[str, Any]) -> None:
    """Enrich race_data in-place with commentary and highlights."""
    events = race_data.get("events", [])
    replay = race_data

    commentary_lines = generate_circuit_commentary(replay, events)
    race_data["commentary"] = [
        {"timestamp": l.timestamp, "text": l.text, "tone": l.tone, "line_type": l.line_type}
        for l in commentary_lines
    ]

    race_data["highlights"] = _extract_highlights(events)


def _extract_highlights(events: list[RaceEvent]) -> list[dict[str, Any]]:
    """Extract high-drama events as highlights."""
    _DRAMA: dict[str, int] = {
        "OVERTAKE": 3, "BATTLE": 4, "SPIN": 3,
        "SAFETY_CAR": 5, "FASTEST_LAP": 2,
    }
    highlights: list[dict[str, Any]] = []
    for evt in events:
        weight = _DRAMA.get(evt.type, 0)
        if weight >= 3:
            highlights.append({
                "type": evt.type,
                "tick": evt.tick,
                "cars": evt.cars,
                "drama_weight": weight,
            })
    return highlights
