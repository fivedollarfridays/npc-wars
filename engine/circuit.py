"""Code Circuit race engine — simulate a lap-based race between cars.

Produces race data conforming to the platform contract: results, events,
rounds with positions, and player list for episode/TV compatibility.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

__all__ = ["run_race", "RaceEvent"]


@dataclass
class RaceEvent:
    """A single race event for commentary and highlights."""

    type: str
    tick: int
    cars: list[str]
    data: dict[str, Any] = field(default_factory=dict)


def run_race(
    car_configs: list[dict[str, Any]],
    laps: int = 5,
    seed: int | None = None,
) -> dict[str, Any]:
    """Simulate a Code Circuit race.

    Returns a dict with: game, cars, laps, results, events, rounds,
    players (episode compat), winner.
    """
    rng = random.Random(seed)
    cars = [_init_car(c, i) for i, c in enumerate(car_configs)]
    events: list[RaceEvent] = []
    rounds: list[dict[str, Any]] = []
    tick = 0

    for lap in range(1, laps + 1):
        tick += 1
        lap_events = _simulate_lap(cars, lap, tick, rng)
        events.extend(lap_events)
        rounds.append(_snapshot_round(cars, lap))

    cars.sort(key=lambda c: (-c.laps_done, c.total_time))
    results = [
        {"car": c.emoji, "name": c.name, "position": i + 1, "laps": c.laps_done, "time": round(c.total_time, 2)}
        for i, c in enumerate(cars)
    ]

    players = [{"emoji": c.emoji, "name": c.name} for c in cars]

    return {
        "game": "circuit",
        "cars": [c.emoji for c in cars],
        "laps": laps,
        "results": results,
        "events": events,
        "rounds": rounds,
        "players": players,
        "winner": results[0]["car"],
    }


@dataclass
class _Car:
    name: str
    emoji: str
    strategy: str
    speed: float
    consistency: float
    position: int
    laps_done: int = 0
    total_time: float = 0.0


def _init_car(config: dict[str, Any], index: int) -> _Car:
    strategy = config.get("strategy", "balanced")
    base_speed = {"aggressive": 1.15, "conservative": 0.95, "balanced": 1.05}.get(strategy, 1.0)
    consistency = {"aggressive": 0.7, "conservative": 0.95, "balanced": 0.85}.get(strategy, 0.85)
    return _Car(
        name=config.get("name", f"Car {index + 1}"),
        emoji=config.get("emoji", f"C{index}"),
        strategy=strategy,
        speed=base_speed,
        consistency=consistency,
        position=index + 1,
    )


def _simulate_lap(
    cars: list[_Car], lap: int, tick: int, rng: random.Random,
) -> list[RaceEvent]:
    """Simulate one lap. Update car times and positions, generate events."""
    events: list[RaceEvent] = []

    for car in cars:
        variance = rng.gauss(0, 1 - car.consistency)
        lap_time = 60.0 / car.speed + variance * 5
        car.total_time += max(lap_time, 40.0)
        car.laps_done += 1

    prev_positions = {c.emoji: c.position for c in cars}
    cars_sorted = sorted(cars, key=lambda c: c.total_time)
    for i, car in enumerate(cars_sorted):
        car.position = i + 1

    for car in cars_sorted:
        old_pos = prev_positions[car.emoji]
        if car.position < old_pos:
            overtaken = [c for c in cars if c.position == old_pos]
            defender = overtaken[0].emoji if overtaken else "?"
            events.append(RaceEvent(
                type="OVERTAKE", tick=tick,
                cars=[car.emoji, defender],
                data={"from": old_pos, "to": car.position},
            ))

    if rng.random() < 0.15:
        car = rng.choice(cars)
        events.append(RaceEvent(type="FASTEST_LAP", tick=tick, cars=[car.emoji]))

    if rng.random() < 0.08:
        car = rng.choice(cars)
        car.total_time += rng.uniform(2, 5)
        events.append(RaceEvent(type="SPIN", tick=tick, cars=[car.emoji]))

    return events


def _snapshot_round(cars: list[_Car], lap: int) -> dict[str, Any]:
    """Capture car positions for this lap."""
    positions = [
        {"emoji": c.emoji, "name": c.name, "position": c.position, "lap_time": round(c.total_time, 2)}
        for c in sorted(cars, key=lambda c: c.position)
    ]
    return {"round": lap, "positions": positions}
