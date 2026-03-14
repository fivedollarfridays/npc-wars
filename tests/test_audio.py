"""Tests for the stinger audio asset library."""

from pathlib import Path

import pytest


EXPECTED_EVENTS = [
    "hit",
    "critical_hit",
    "kill",
    "kill_streak",
    "bump",
    "chain_bump",
    "wall_splat",
    "storm_damage",
    "rest_heal",
    "near_death",
    "watcher_spawn",
    "human_enter",
    "match_end",
]


class TestStingerMap:
    """Tests for STINGER_MAP structure."""

    def test_stinger_map_has_13_entries(self) -> None:
        from audio import STINGER_MAP

        assert len(STINGER_MAP) == 13

    @pytest.mark.parametrize("event_type", EXPECTED_EVENTS)
    def test_event_type_present(self, event_type: str) -> None:
        from audio import STINGER_MAP

        assert event_type in STINGER_MAP

    def test_all_values_are_wav_filenames(self) -> None:
        from audio import STINGER_MAP

        for key, filename in STINGER_MAP.items():
            assert filename.endswith(".wav"), f"{key} -> {filename} not .wav"


class TestGetStingerPath:
    """Tests for get_stinger_path helper."""

    def test_known_event_returns_path(self) -> None:
        from audio import get_stinger_path

        result = get_stinger_path("hit")
        assert isinstance(result, Path)

    def test_unknown_event_returns_none(self) -> None:
        from audio import get_stinger_path

        result = get_stinger_path("nonexistent_event")
        assert result is None

    @pytest.mark.parametrize("event_type", EXPECTED_EVENTS)
    def test_all_stinger_paths_exist(self, event_type: str) -> None:
        from audio import get_stinger_path

        path = get_stinger_path(event_type)
        assert path is not None
        assert path.exists(), f"Missing asset: {path}"


class TestAudioAssets:
    """Tests for WAV file validity and constraints."""

    @pytest.mark.parametrize("event_type", EXPECTED_EVENTS)
    def test_asset_file_nonzero_size(self, event_type: str) -> None:
        from audio import get_stinger_path

        path = get_stinger_path(event_type)
        assert path is not None
        assert path.stat().st_size > 0, f"Empty file: {path}"

    def test_total_asset_size_under_5mb(self) -> None:
        from audio import STINGER_MAP, get_stinger_path

        total = sum(
            get_stinger_path(evt).stat().st_size  # type: ignore[union-attr]
            for evt in STINGER_MAP
        )
        five_mb = 5 * 1024 * 1024
        assert total < five_mb, f"Total {total} bytes exceeds 5MB"

    @pytest.mark.parametrize("event_type", EXPECTED_EVENTS)
    def test_valid_wav_riff_header(self, event_type: str) -> None:
        from audio import get_stinger_path

        path = get_stinger_path(event_type)
        assert path is not None
        with open(path, "rb") as f:
            header = f.read(4)
        assert header == b"RIFF", f"{path.name} missing RIFF header"
