"""Platform event contract — game-agnostic event type for highlights and episodes.

GameEvent is the seam that lets highlight extraction and episode generation
work across Kill Switch and Code Circuit without knowing which game produced
the data.

Drama weight rationale (0-6 scale):
  0 — routine (movement, defend)
  1 — minor tactical (pit stop, trap placed)
  2 — moderate (hit, ability, fastest lap)
  3 — notable (overtake, spin, storm kill)
  4 — dramatic (kill, near death, battle, watcher kill)
  5 — high drama (safety car, watcher spawn, last two alive)
  6 — peak (multi kill)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

__all__ = [
    "GameEvent",
    "EVENT_TYPES",
    "adapt_killswitch_events",
    "adapt_circuit_events",
]


@dataclass
class GameEvent:
    """Platform-level event produced by either game's adapter."""

    type: str
    timestamp: float
    participants: list[str]
    data: dict[str, Any] = field(default_factory=dict)
    drama_weight: int | float = 0


# -- Event type catalogue with drama weights and rationale --------------------

EVENT_TYPES: dict[str, dict[str, Any]] = {
    # Kill Switch events
    "kill":            {"weight": 4, "rationale": "Elimination is a decisive moment"},
    "hit":             {"weight": 2, "rationale": "Direct combat damage"},
    "ranged_hit":      {"weight": 2, "rationale": "Ranged combat damage"},
    "ability_damage":  {"weight": 2, "rationale": "Ability impact on target"},
    "ability_heal":    {"weight": 1, "rationale": "Recovery is tactically minor"},
    "near_death":      {"weight": 4, "rationale": "Survival at critical HP is gripping"},
    "trap_trigger":    {"weight": 2, "rationale": "Trap sprung — tactical payoff"},
    "watcher_spawn":   {"weight": 5, "rationale": "NPC threat entry changes the board"},
    "watcher_kill":    {"weight": 4, "rationale": "NPC elimination is dramatic"},
    "watcher_sync":    {"weight": 3, "rationale": "Sync milestone escalates tension"},
    "bump":            {"weight": 1, "rationale": "Collision is minor chaos"},
    "wall_splat":      {"weight": 1, "rationale": "Environmental damage"},
    "storm_damage":    {"weight": 1, "rationale": "Zone pressure"},
    # Code Circuit events
    "overtake":        {"weight": 3, "rationale": "Position change is core racing drama"},
    "battle":          {"weight": 4, "rationale": "Sustained close combat between cars"},
    "spin":            {"weight": 3, "rationale": "Loss of control is visually dramatic"},
    "safety_car":      {"weight": 5, "rationale": "Race-altering incident, field resets"},
    "pit_stop":        {"weight": 1, "rationale": "Strategic but low visual drama"},
    "fastest_lap":     {"weight": 2, "rationale": "Achievement marker, not narrative peak"},
}

# -- Kill Switch adapter ------------------------------------------------------

# Events worth surfacing (skip movement, defend, miss — too noisy)
_KS_MAPPED: dict[str, int] = {
    "kill": 4, "hit": 2, "ranged_hit": 2,
    "ability_damage": 2, "ability_heal": 1,
    "trap_trigger": 2, "bump": 1, "wall_splat": 1, "storm_damage": 1,
    "watcher_spawn": 5, "watcher_kill": 4, "watcher_sync": 3,
}

_NEAR_DEATH_HP = 5


def adapt_killswitch_events(match_data: dict[str, Any]) -> list[GameEvent]:
    """Map Kill Switch match_data → list[GameEvent]."""
    out: list[GameEvent] = []
    for rnd in match_data.get("rounds", []):
        rnum = rnd.get("round", 0)
        for evt in rnd.get("events", []):
            etype = evt.get("type", "")
            if etype not in _KS_MAPPED:
                continue
            out.append(GameEvent(
                type=etype,
                timestamp=rnum,
                participants=_ks_participants(evt),
                data={k: v for k, v in evt.items() if k != "type"},
                drama_weight=_KS_MAPPED[etype],
            ))
        # Synthesise near-death events from positions
        for pos in rnd.get("positions", []):
            hp = pos.get("hp", 999)
            if pos.get("alive") and 0 < hp < _NEAR_DEATH_HP:
                out.append(GameEvent(
                    type="near_death",
                    timestamp=rnum,
                    participants=[pos.get("emoji", "?")],
                    data={"hp": hp},
                    drama_weight=4,
                ))
    return out


def _ks_participants(evt: dict[str, Any]) -> list[str]:
    parts: list[str] = []
    for key in ("attacker", "victim", "target", "emoji", "pusher", "owner", "taunter"):
        val = evt.get(key)
        if val and val not in parts:
            parts.append(val)
    return parts


# -- Code Circuit adapter ----------------------------------------------------

_CC_WEIGHTS: dict[str, int] = {
    "OVERTAKE": 3, "BATTLE": 4, "SPIN": 3,
    "SAFETY_CAR": 5, "PIT_STOP": 1, "FASTEST_LAP": 2,
}


def adapt_circuit_events(
    replay: dict[str, Any],
    race_events: list[Any],
) -> list[GameEvent]:
    """Map Code Circuit RaceEvent list → list[GameEvent]."""
    tps = replay.get("ticks_per_sec", 30)
    out: list[GameEvent] = []
    for evt in race_events:
        etype = evt.type
        if etype not in _CC_WEIGHTS:
            continue
        out.append(GameEvent(
            type=etype.lower(),
            timestamp=round(evt.tick / tps, 2),
            participants=list(evt.cars),
            data=dict(evt.data),
            drama_weight=_CC_WEIGHTS[etype],
        ))
    return out
