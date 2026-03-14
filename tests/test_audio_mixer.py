"""Tests for audio.mixer — stinger timeline and hype volume curves."""

from typing import Any


def _make_match(rounds: list[dict[str, Any]]) -> dict[str, Any]:
    """Helper to build minimal match_data with given rounds."""
    return {"rounds": rounds}


def _make_round(
    round_num: int,
    events: list[dict[str, Any]] | None = None,
    spectacle: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Helper to build a round dict."""
    rd: dict[str, Any] = {"round": round_num}
    if events is not None:
        rd["events"] = events
    if spectacle is not None:
        rd["spectacle"] = spectacle
    return rd


class TestBuildAudioTimeline:
    """Tests for build_audio_timeline."""

    def test_returns_list_of_tuples(self) -> None:
        from audio.mixer import build_audio_timeline

        result = build_audio_timeline({"rounds": []})
        assert isinstance(result, list)

    def test_empty_match_returns_empty(self) -> None:
        from audio.mixer import build_audio_timeline

        result = build_audio_timeline({})
        assert result == []

    def test_round_1_kill_event_at_500ms(self) -> None:
        from audio.mixer import build_audio_timeline

        match_data = _make_match([
            _make_round(1, events=[{"type": "kill"}]),
        ])
        result = build_audio_timeline(match_data, round_duration_ms=500)
        assert len(result) == 1
        ts, path = result[0]
        assert ts == 500
        assert "kill.wav" in path

    def test_round_3_bump_event_at_1500ms(self) -> None:
        from audio.mixer import build_audio_timeline

        match_data = _make_match([
            _make_round(3, events=[{"type": "bump"}]),
        ])
        result = build_audio_timeline(match_data, round_duration_ms=500)
        assert len(result) == 1
        ts, path = result[0]
        assert ts == 1500
        assert "bump.wav" in path

    def test_no_matching_events_returns_empty(self) -> None:
        from audio.mixer import build_audio_timeline

        match_data = _make_match([
            _make_round(1, events=[{"type": "unknown_event_xyz"}]),
        ])
        result = build_audio_timeline(match_data)
        assert result == []

    def test_multiple_events_same_round(self) -> None:
        from audio.mixer import build_audio_timeline

        match_data = _make_match([
            _make_round(2, events=[{"type": "hit"}, {"type": "kill"}]),
        ])
        result = build_audio_timeline(match_data, round_duration_ms=500)
        assert len(result) == 2
        assert all(ts == 1000 for ts, _ in result)

    def test_timeline_sorted_by_timestamp(self) -> None:
        from audio.mixer import build_audio_timeline

        match_data = _make_match([
            _make_round(3, events=[{"type": "bump"}]),
            _make_round(1, events=[{"type": "kill"}]),
        ])
        result = build_audio_timeline(match_data, round_duration_ms=500)
        timestamps = [ts for ts, _ in result]
        assert timestamps == sorted(timestamps)


class TestBuildHypeVolumeCurve:
    """Tests for build_hype_volume_curve."""

    def test_returns_list_of_tuples(self) -> None:
        from audio.mixer import build_hype_volume_curve

        result = build_hype_volume_curve({"rounds": []})
        assert isinstance(result, list)

    def test_calm_tier_volume_01(self) -> None:
        from audio.mixer import build_hype_volume_curve

        match_data = _make_match([
            _make_round(1, spectacle={"tier": "calm"}),
        ])
        result = build_hype_volume_curve(match_data)
        assert len(result) == 1
        assert result[0][1] == 0.1

    def test_chaos_tier_volume_10(self) -> None:
        from audio.mixer import build_hype_volume_curve

        match_data = _make_match([
            _make_round(1, spectacle={"tier": "chaos"}),
        ])
        result = build_hype_volume_curve(match_data)
        assert len(result) == 1
        assert result[0][1] == 1.0

    def test_one_entry_per_round(self) -> None:
        from audio.mixer import build_hype_volume_curve

        match_data = _make_match([
            _make_round(1, spectacle={"tier": "calm"}),
            _make_round(2, spectacle={"tier": "intense"}),
            _make_round(3, spectacle={"tier": "chaos"}),
        ])
        result = build_hype_volume_curve(match_data, round_duration_ms=500)
        assert len(result) == 3
        assert result[0] == (500, 0.1)
        assert result[1] == (1000, 0.5)
        assert result[2] == (1500, 1.0)

    def test_missing_spectacle_defaults_calm(self) -> None:
        from audio.mixer import build_hype_volume_curve

        match_data = _make_match([_make_round(1)])
        result = build_hype_volume_curve(match_data)
        assert len(result) == 1
        assert result[0][1] == 0.1

    def test_empty_match_returns_empty(self) -> None:
        from audio.mixer import build_hype_volume_curve

        result = build_hype_volume_curve({})
        assert result == []


class TestTierVolumes:
    """Tests for TIER_VOLUMES constant."""

    def test_all_five_tiers_present(self) -> None:
        from audio.mixer import TIER_VOLUMES

        expected = {"calm", "heating", "intense", "hype", "chaos"}
        assert set(TIER_VOLUMES.keys()) == expected

    def test_volumes_increase_monotonically(self) -> None:
        from audio.mixer import TIER_VOLUMES

        order = ["calm", "heating", "intense", "hype", "chaos"]
        volumes = [TIER_VOLUMES[t] for t in order]
        assert volumes == sorted(volumes)
        assert all(0.0 <= v <= 1.0 for v in volumes)
