"""Audio mixing pipeline -- stinger timeline and hype volume curves."""

from typing import Any

from audio.stingers import get_stinger_path

__all__ = ["build_audio_timeline", "build_hype_volume_curve", "TIER_VOLUMES"]

TIER_VOLUMES: dict[str, float] = {
    "calm": 0.1,
    "heating": 0.3,
    "intense": 0.5,
    "hype": 0.8,
    "chaos": 1.0,
}


def build_audio_timeline(
    match_data: dict[str, Any],
    round_duration_ms: int = 500,
) -> list[tuple[int, str]]:
    """Build stinger timeline from match data.

    Returns sorted list of (timestamp_ms, audio_file_path) tuples.
    """
    timeline: list[tuple[int, str]] = []
    for round_data in match_data.get("rounds", []):
        round_num = round_data.get("round", 0)
        timestamp = round_num * round_duration_ms
        for event in round_data.get("events", []):
            event_type = event.get("type", "")
            path = get_stinger_path(event_type)
            if path is not None:
                timeline.append((timestamp, str(path)))
    timeline.sort(key=lambda t: t[0])
    return timeline


def build_hype_volume_curve(
    match_data: dict[str, Any],
    round_duration_ms: int = 500,
) -> list[tuple[int, float]]:
    """Build hype track volume keyframes from spectacle tiers.

    Returns list of (timestamp_ms, volume_float) tuples.
    """
    curve: list[tuple[int, float]] = []
    for round_data in match_data.get("rounds", []):
        round_num = round_data.get("round", 0)
        timestamp = round_num * round_duration_ms
        spectacle = round_data.get("spectacle", {})
        tier = spectacle.get("tier", "calm")
        volume = TIER_VOLUMES.get(tier, 0.1)
        curve.append((timestamp, volume))
    return curve
