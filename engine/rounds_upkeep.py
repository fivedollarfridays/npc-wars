"""Kill-attribution helper extracted from ``engine.rounds``.

Pulled out so ``rounds.py`` stays under the 200-line size gate after the
T73.7 storm/rest changes (enforced by ``tests/test_s29_integration``).
Re-exported from ``engine.rounds`` for backward compatibility.
"""

from __future__ import annotations

from typing import Any

from engine.combat import Bot, KILL_BOUNTY_ENERGY
from engine.event_meta import TICK_DEATHS, position

__all__ = ["attribute_kills"]

_Event = dict[str, Any]

_HIT_TYPES = frozenset({"hit", "ranged_hit"})


def attribute_kills(
    round_elims: list[_Event], round_events: list[_Event],
    bots: list[Bot], round_num: int,
) -> None:
    """Find killing blow and attribute kills to attackers."""
    for elim in round_elims:
        killer_emoji: str | None = None
        for evt in round_events:
            if (evt.get("type") in _HIT_TYPES and evt.get("target") == elim["emoji"]
                    and evt.get("hp_before", 1) > 0
                    and evt["hp_before"] - evt["damage"] <= 0):
                killer_emoji = evt["attacker"]
                break
        if killer_emoji is None:
            for evt in round_events:
                if evt.get("type") in _HIT_TYPES and evt.get("target") == elim["emoji"]:
                    killer_emoji = evt["attacker"]
        if killer_emoji is None:
            for evt in round_events:
                if (evt.get("type") == "trap_trigger" and evt.get("victim") == elim["emoji"]
                        and evt.get("hp_before", 1) > 0
                        and evt["hp_before"] - evt["damage"] <= 0):
                    killer_emoji = evt["owner"]
                    break
        if killer_emoji is None:
            for evt in round_events:
                if evt.get("type") == "trap_trigger" and evt.get("victim") == elim["emoji"]:
                    killer_emoji = evt["owner"]
        if killer_emoji is None:
            for evt in round_events:
                if evt.get("type") == "storm_damage" and evt.get("target") == elim["emoji"]:
                    killer_emoji = "storm"
        elim["killed_by"] = killer_emoji or "unknown"
        elim["cause"] = "storm" if killer_emoji == "storm" else "combat"
        if killer_emoji and killer_emoji != "storm":
            for b in bots:
                if b.emoji == killer_emoji:
                    b.kills += 1
                    b.energy = min(b.energy + KILL_BOUNTY_ENERGY, b.derived.max_energy)
        victim_pos: dict[str, int] | None = None
        for b in bots:
            if b.emoji == elim["emoji"]:
                victim_pos = position(b)
                break
        round_events.append({
            "type": "kill", "attacker": killer_emoji or "unknown",
            "victim": elim["emoji"], "round": round_num,
            "tick_in_round": TICK_DEATHS, "position": victim_pos,
        })
