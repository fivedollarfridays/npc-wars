"""WAV sample generators for each stinger event type."""

import math
from typing import Callable

from audio.waveforms import (
    SAMPLE_RATE,
    apply_decay,
    noise_samples,
    sine_samples,
    square_samples,
)


def gen_hit() -> list[int]:
    """Short punch: square wave burst, 0.3s."""
    return apply_decay(square_samples(220, 0.3), 0.1)


def gen_critical_hit() -> list[int]:
    """Heavier impact: low square wave, 0.5s."""
    return apply_decay(square_samples(110, 0.5), 0.2)


def gen_kill() -> list[int]:
    """Explosion: noise burst with decay, 0.8s."""
    return apply_decay(noise_samples(0.8), 0.1)


def gen_kill_streak() -> list[int]:
    """Air horn: rising sine, 1.0s."""
    n = int(SAMPLE_RATE * 1.0)
    samples: list[int] = []
    for i in range(n):
        t = i / SAMPLE_RATE
        freq = 300 + 400 * (t / 1.0)
        val = 128 + int(100 * math.sin(2 * math.pi * freq * t))
        samples.append(max(0, min(255, val)))
    return samples


def gen_bump() -> list[int]:
    """Pinball ding: high sine ping, 0.2s."""
    return apply_decay(sine_samples(1200, 0.2, 180), 0.05)


def gen_chain_bump() -> list[int]:
    """Cascading dings: descending sine pings, 0.5s."""
    samples: list[int] = []
    for j in range(4):
        freq = 1200 - j * 200
        ping = apply_decay(sine_samples(freq, 0.12, 160), 0.1)
        samples.extend(ping)
    return samples[:int(SAMPLE_RATE * 0.5)]


def gen_wall_splat() -> list[int]:
    """Thud: low noise burst, 0.4s."""
    return apply_decay(noise_samples(0.4, 150), 0.15)


def gen_storm_damage() -> list[int]:
    """Electric zap: rapid frequency sweep, 0.3s."""
    n = int(SAMPLE_RATE * 0.3)
    samples: list[int] = []
    for i in range(n):
        t = i / SAMPLE_RATE
        freq = 200 + 2000 * abs(math.sin(20 * math.pi * t))
        val = 128 + int(90 * math.sin(2 * math.pi * freq * t))
        samples.append(max(0, min(255, val)))
    return samples


def gen_rest_heal() -> list[int]:
    """Gentle chime: high sine fade, 0.3s."""
    return apply_decay(sine_samples(880, 0.3, 120), 0.2)


def gen_near_death() -> list[int]:
    """Tension sting: low sustained tone, 0.5s."""
    return sine_samples(80, 0.5, 160)


def gen_watcher_spawn() -> list[int]:
    """Ominous chord: low sine with harmonics, 1.5s."""
    n = int(SAMPLE_RATE * 1.5)
    samples: list[int] = []
    for i in range(n):
        t = i / SAMPLE_RATE
        v = (
            math.sin(2 * math.pi * 55 * t)
            + 0.5 * math.sin(2 * math.pi * 82 * t)
            + 0.3 * math.sin(2 * math.pi * 110 * t)
        )
        val = 128 + int(50 * v)
        samples.append(max(0, min(255, val)))
    return apply_decay(samples, 0.6)


def gen_human_enter() -> list[int]:
    """Record scratch: noise sweep, 1.0s."""
    n = int(SAMPLE_RATE * 1.0)
    seed = 99
    samples: list[int] = []
    for i in range(n):
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        fade = 1.0 - i / n
        val = 128 + int((seed % 201 - 100) * fade)
        samples.append(max(0, min(255, val)))
    return samples


def gen_match_end() -> list[int]:
    """Victory fanfare: rising chord, 2.0s."""
    n = int(SAMPLE_RATE * 2.0)
    samples: list[int] = []
    for i in range(n):
        t = i / SAMPLE_RATE
        base = 220 + 110 * (t / 2.0)
        v = (
            math.sin(2 * math.pi * base * t)
            + 0.7 * math.sin(2 * math.pi * base * 1.25 * t)
            + 0.5 * math.sin(2 * math.pi * base * 1.5 * t)
        )
        val = 128 + int(40 * v)
        samples.append(max(0, min(255, val)))
    return samples


GENERATORS: dict[str, Callable[[], list[int]]] = {
    "hit": gen_hit,
    "critical_hit": gen_critical_hit,
    "kill": gen_kill,
    "kill_streak": gen_kill_streak,
    "bump": gen_bump,
    "chain_bump": gen_chain_bump,
    "wall_splat": gen_wall_splat,
    "storm_damage": gen_storm_damage,
    "rest_heal": gen_rest_heal,
    "near_death": gen_near_death,
    "watcher_spawn": gen_watcher_spawn,
    "human_enter": gen_human_enter,
    "match_end": gen_match_end,
}
