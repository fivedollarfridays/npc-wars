"""S45 Integration Gate — Spectacle system validation."""

from __future__ import annotations

from pathlib import Path


class TestKillCam:
    def test_effects_has_kill_cam(self) -> None:
        content = Path("viewer/js/effects.js").read_text()
        assert "triggerKillCam" in content

    def test_effects_has_death_animation(self) -> None:
        content = Path("viewer/js/effects.js").read_text()
        assert "playDeathAnimation" in content

    def test_effects_has_update_kill_cam(self) -> None:
        content = Path("viewer/js/effects.js").read_text()
        assert "updateKillCam" in content


class TestSynthAudio:
    def test_audio_has_play_synth(self) -> None:
        content = Path("viewer/js/audio.js").read_text()
        assert "playSynth" in content

    def test_audio_has_synth_tone(self) -> None:
        content = Path("viewer/js/audio.js").read_text()
        assert "_synthTone" in content

    def test_events_triggers_audio(self) -> None:
        content = Path("viewer/js/events.js").read_text()
        assert "playSynth" in content


class TestRoundTransitions:
    def test_effects_has_round_number(self) -> None:
        content = Path("viewer/js/effects.js").read_text()
        assert "showRoundNumber" in content

    def test_effects_has_winner_celebration(self) -> None:
        content = Path("viewer/js/effects.js").read_text()
        assert "showWinnerCelebration" in content

    def test_effects_has_match_intro(self) -> None:
        content = Path("viewer/js/effects.js").read_text()
        assert "showMatchIntro" in content


class TestSpectacleModules:
    def test_effects_file_exists(self) -> None:
        assert Path("viewer/js/effects.js").exists()

    def test_audio_file_exists(self) -> None:
        assert Path("viewer/js/audio.js").exists()

    def test_events_file_exists(self) -> None:
        assert Path("viewer/js/events.js").exists()
