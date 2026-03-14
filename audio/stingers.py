"""Stinger sound effect library for NPC Wars spectacle system."""

from pathlib import Path

from audio.generators import GENERATORS
from audio.waveforms import write_wav

_ASSETS_DIR = Path(__file__).parent / "assets"

STINGER_MAP: dict[str, str] = {
    "hit": "hit.wav",
    "critical_hit": "critical_hit.wav",
    "kill": "kill.wav",
    "kill_streak": "kill_streak.wav",
    "bump": "bump.wav",
    "chain_bump": "chain_bump.wav",
    "wall_splat": "wall_splat.wav",
    "storm_damage": "storm_damage.wav",
    "rest_heal": "rest_heal.wav",
    "near_death": "near_death.wav",
    "watcher_spawn": "watcher_spawn.wav",
    "human_enter": "human_enter.wav",
    "match_end": "match_end.wav",
}

__all__ = ["STINGER_MAP", "get_stinger_path"]

def get_stinger_path(event_type: str) -> Path | None:
    """Return absolute path to stinger WAV for event_type, or None."""
    filename = STINGER_MAP.get(event_type)
    if filename is None:
        return None
    return _ASSETS_DIR / filename


def _generate_assets() -> None:
    """Generate all WAV stinger files if any are missing."""
    _ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    for event_type, filename in STINGER_MAP.items():
        path = _ASSETS_DIR / filename
        if not path.exists():
            gen_fn = GENERATORS[event_type]
            write_wav(path, gen_fn())


# Auto-generate assets on import if any are missing
if not all((_ASSETS_DIR / fn).exists() for fn in STINGER_MAP.values()):
    _generate_assets()
