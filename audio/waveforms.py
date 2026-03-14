"""Low-level waveform primitive generators for 8-bit audio."""

import math
import struct
import wave
from pathlib import Path

SAMPLE_RATE = 8000


def sine_samples(freq: float, duration: float, volume: int = 200) -> list[int]:
    """Generate sine wave samples (8-bit unsigned, 128 = center)."""
    n = int(SAMPLE_RATE * duration)
    samples: list[int] = []
    for i in range(n):
        t = i / SAMPLE_RATE
        val = 128 + int(volume / 2 * math.sin(2 * math.pi * freq * t))
        samples.append(max(0, min(255, val)))
    return samples


def square_samples(freq: float, duration: float, volume: int = 200) -> list[int]:
    """Generate square wave samples (8-bit unsigned)."""
    n = int(SAMPLE_RATE * duration)
    half = volume // 2
    samples: list[int] = []
    for i in range(n):
        t = i / SAMPLE_RATE
        phase = (t * freq) % 1.0
        val = 128 + (half if phase < 0.5 else -half)
        samples.append(max(0, min(255, val)))
    return samples


def noise_samples(duration: float, volume: int = 200) -> list[int]:
    """Generate pseudo-random noise (deterministic via simple LCG)."""
    n = int(SAMPLE_RATE * duration)
    half = volume // 2
    seed = 42
    samples: list[int] = []
    for _ in range(n):
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        val = 128 + int((seed % (volume + 1)) - half)
        samples.append(max(0, min(255, val)))
    return samples


def apply_decay(samples: list[int], decay_start: float = 0.3) -> list[int]:
    """Apply linear decay envelope starting at decay_start fraction."""
    n = len(samples)
    start_idx = int(n * decay_start)
    out: list[int] = []
    for i, s in enumerate(samples):
        if i >= start_idx and start_idx < n:
            fade = 1.0 - (i - start_idx) / max(1, n - start_idx)
            s = 128 + int((s - 128) * fade)
        out.append(max(0, min(255, s)))
    return out


def write_wav(path: Path, samples: list[int]) -> None:
    """Write 8-bit mono WAV file from sample list."""
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(1)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(struct.pack(f"{len(samples)}B", *samples))
