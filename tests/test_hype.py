"""Tests for the hype track escalation system."""


class TestSelectHypeTrack:
    """Tests for select_hype_track function."""

    def test_calm_returns_ambient_intensity(self) -> None:
        from audio.hype import select_hype_track

        result = select_hype_track("calm")
        assert result["intensity"] == "ambient"
        assert result["volume"] == 0.15

    def test_heating_returns_ambient_intensity(self) -> None:
        from audio.hype import select_hype_track

        result = select_hype_track("heating")
        assert result["intensity"] == "ambient"

    def test_intense_returns_mid(self) -> None:
        from audio.hype import select_hype_track

        result = select_hype_track("intense")
        assert result["intensity"] == "mid"
        assert result["volume"] == 0.4

    def test_hype_returns_peak(self) -> None:
        from audio.hype import select_hype_track

        result = select_hype_track("hype")
        assert result["intensity"] == "peak"
        assert result["volume"] == 0.8

    def test_chaos_returns_peak(self) -> None:
        from audio.hype import select_hype_track

        result = select_hype_track("chaos")
        assert result["intensity"] == "peak"
        assert result["volume"] == 0.8

    def test_returns_dict_with_required_keys(self) -> None:
        from audio.hype import select_hype_track

        result = select_hype_track("calm")
        assert "track" in result
        assert "volume" in result
        assert "intensity" in result


class TestHypeTracks:
    """Tests for HYPE_TRACKS constant."""

    def test_has_exactly_3_entries(self) -> None:
        from audio.hype import HYPE_TRACKS

        assert len(HYPE_TRACKS) == 3

    def test_all_hype_track_files_exist(self) -> None:
        from audio.hype import HYPE_TRACKS, _ASSETS_DIR

        for intensity, filename in HYPE_TRACKS.items():
            path = _ASSETS_DIR / filename
            assert path.exists(), f"Missing hype asset: {path}"

    def test_all_hype_track_files_are_valid_wav(self) -> None:
        from audio.hype import HYPE_TRACKS, _ASSETS_DIR

        for intensity, filename in HYPE_TRACKS.items():
            path = _ASSETS_DIR / filename
            with open(path, "rb") as f:
                header = f.read(4)
            assert header == b"RIFF", f"{filename} missing RIFF header"


class TestBuildHypeTimeline:
    """Tests for build_hype_timeline function."""

    def test_returns_list_of_dicts_with_required_keys(self) -> None:
        from audio.hype import build_hype_timeline

        match_data = {
            "rounds": [
                {"round": 0, "spectacle": {"tier": "calm"}},
            ],
        }
        timeline = build_hype_timeline(match_data)
        assert len(timeline) >= 1
        entry = timeline[0]
        assert "timestamp_ms" in entry
        assert "track" in entry
        assert "volume" in entry
        assert "crossfade_ms" in entry

    def test_crossfade_on_tier_change(self) -> None:
        from audio.hype import build_hype_timeline

        match_data = {
            "rounds": [
                {"round": 0, "spectacle": {"tier": "calm"}},
                {"round": 1, "spectacle": {"tier": "intense"}},
            ],
        }
        timeline = build_hype_timeline(match_data)
        # First entry has no crossfade, second has crossfade
        assert timeline[0]["crossfade_ms"] == 0
        assert timeline[1]["crossfade_ms"] == 500

    def test_no_crossfade_when_same_tier(self) -> None:
        from audio.hype import build_hype_timeline

        match_data = {
            "rounds": [
                {"round": 0, "spectacle": {"tier": "calm"}},
                {"round": 1, "spectacle": {"tier": "calm"}},
                {"round": 2, "spectacle": {"tier": "heating"}},
            ],
        }
        timeline = build_hype_timeline(match_data)
        # calm and heating both map to ambient, so only 1 entry
        assert len(timeline) == 1

    def test_crossfade_ms_is_500_on_transition(self) -> None:
        from audio.hype import build_hype_timeline, CROSSFADE_MS

        assert CROSSFADE_MS == 500
        match_data = {
            "rounds": [
                {"round": 0, "spectacle": {"tier": "calm"}},
                {"round": 1, "spectacle": {"tier": "hype"}},
            ],
        }
        timeline = build_hype_timeline(match_data)
        assert timeline[1]["crossfade_ms"] == 500

    def test_empty_match_returns_empty_timeline(self) -> None:
        from audio.hype import build_hype_timeline

        assert build_hype_timeline({}) == []
        assert build_hype_timeline({"rounds": []}) == []
