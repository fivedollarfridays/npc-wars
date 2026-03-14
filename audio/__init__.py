"""Audio asset library for NPC Wars."""

from audio.mixer import TIER_VOLUMES, build_audio_timeline, build_hype_volume_curve
from audio.stingers import STINGER_MAP, get_stinger_path

__all__ = [
    "STINGER_MAP",
    "TIER_VOLUMES",
    "build_audio_timeline",
    "build_hype_volume_curve",
    "get_stinger_path",
]
