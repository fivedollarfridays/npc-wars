"""Hype track escalation — background music that follows drama tier."""

import math
from pathlib import Path
from typing import Any, Callable

from audio.waveforms import SAMPLE_RATE, sine_samples, square_samples, write_wav

__all__ = [
    "HYPE_TRACKS",
    "INTENSITY_VOLUMES",
    "select_hype_track",
    "build_hype_timeline",
]

_ASSETS_DIR = Path(__file__).parent / "assets"

HYPE_TRACKS: dict[str, str] = {
    "ambient": "hype_ambient.wav",
    "mid": "hype_mid.wav",
    "peak": "hype_peak.wav",
}

INTENSITY_VOLUMES: dict[str, float] = {
    "ambient": 0.15,
    "mid": 0.4,
    "peak": 0.8,
}

_TIER_TO_INTENSITY: dict[str, str] = {
    "calm": "ambient",
    "heating": "ambient",
    "intense": "mid",
    "hype": "peak",
    "chaos": "peak",
}

CROSSFADE_MS = 500


def select_hype_track(tier: str) -> dict[str, Any]:
    """Select the appropriate hype track for a drama tier."""
    intensity = _TIER_TO_INTENSITY.get(tier, "ambient")
    return {
        "track": str(_ASSETS_DIR / HYPE_TRACKS[intensity]),
        "volume": INTENSITY_VOLUMES[intensity],
        "intensity": intensity,
    }


def build_hype_timeline(
    match_data: dict[str, Any],
    round_duration_ms: int = 500,
) -> list[dict[str, Any]]:
    """Build hype track timeline with crossfade events on tier changes."""
    timeline: list[dict[str, Any]] = []
    prev_intensity: str | None = None

    for round_data in match_data.get("rounds", []):
        round_num = round_data.get("round", 0)
        timestamp = round_num * round_duration_ms
        spectacle = round_data.get("spectacle", {})
        tier = spectacle.get("tier", "calm")

        intensity = _TIER_TO_INTENSITY.get(tier, "ambient")

        if intensity != prev_intensity:
            timeline.append({
                "timestamp_ms": timestamp,
                "track": str(_ASSETS_DIR / HYPE_TRACKS[intensity]),
                "volume": INTENSITY_VOLUMES[intensity],
                "crossfade_ms": CROSSFADE_MS if prev_intensity is not None else 0,
            })
            prev_intensity = intensity

    return timeline


def _gen_hype_ambient() -> list[int]:
    """Gentle sine waves at low frequency, ~5 seconds."""
    n = int(SAMPLE_RATE * 5.0)
    samples: list[int] = []
    for i in range(n):
        t = i / SAMPLE_RATE
        v = (
            math.sin(2 * math.pi * 110 * t)
            + 0.4 * math.sin(2 * math.pi * 165 * t)
            + 0.2 * math.sin(2 * math.pi * 55 * t)
        )
        val = 128 + int(30 * v)
        samples.append(max(0, min(255, val)))
    return samples


def _gen_hype_mid() -> list[int]:
    """Mid-energy square/sine mix, ~5 seconds."""
    sine = sine_samples(220, 5.0, 120)
    sq = square_samples(110, 5.0, 80)
    samples: list[int] = []
    for s_val, q_val in zip(sine, sq):
        mixed = 128 + ((s_val - 128) + (q_val - 128)) // 2
        samples.append(max(0, min(255, mixed)))
    return samples


def _gen_hype_peak() -> list[int]:
    """Intense rapid square waves, ~5 seconds."""
    n = int(SAMPLE_RATE * 5.0)
    samples: list[int] = []
    for i in range(n):
        t = i / SAMPLE_RATE
        freq = 330 + 110 * math.sin(2 * math.pi * 4 * t)
        phase = (t * freq) % 1.0
        val = 128 + (90 if phase < 0.5 else -90)
        samples.append(max(0, min(255, val)))
    return samples


_HYPE_GENERATORS: dict[str, Callable[[], list[int]]] = {
    "ambient": _gen_hype_ambient,
    "mid": _gen_hype_mid,
    "peak": _gen_hype_peak,
}


def _generate_hype_assets() -> None:
    """Generate hype track WAV files if missing."""
    _ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    for intensity, filename in HYPE_TRACKS.items():
        path = _ASSETS_DIR / filename
        if not path.exists():
            gen_fn = _HYPE_GENERATORS[intensity]
            write_wav(path, gen_fn())


# Auto-generate hype assets on import if any are missing
if not all((_ASSETS_DIR / fn).exists() for fn in HYPE_TRACKS.values()):
    _generate_hype_assets()
