"""Tests for audio/renderer.py — ffmpeg audio muxing."""

from unittest.mock import patch, MagicMock

import pytest

from audio.renderer import has_audio_stream, mux_audio_into_video


class TestMuxAudioIntoVideo:
    """mux_audio_into_video calls ffmpeg correctly."""

    @patch("audio.renderer.subprocess.run")
    def test_returns_output_path_on_success(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        result = mux_audio_into_video("/tmp/in.mp4", "/tmp/out.mp4")
        assert result == "/tmp/out.mp4"

    @patch("audio.renderer.subprocess.run")
    def test_raises_on_ffmpeg_failure(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=1, stderr="codec error")
        with pytest.raises(RuntimeError, match="ffmpeg mux failed"):
            mux_audio_into_video("/tmp/in.mp4", "/tmp/out.mp4")

    @patch("audio.renderer.subprocess.run")
    def test_calls_ffmpeg_with_correct_args(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        mux_audio_into_video("/tmp/in.mp4", "/tmp/out.mp4")
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "ffmpeg"
        assert "/tmp/in.mp4" in cmd
        assert "/tmp/out.mp4" in cmd
        assert "-shortest" in cmd


class TestHasAudioStream:
    """has_audio_stream uses ffprobe to detect audio."""

    @patch("audio.renderer.subprocess.run")
    def test_returns_true_when_audio_present(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="audio\n")
        assert has_audio_stream("/tmp/test.mp4") is True

    @patch("audio.renderer.subprocess.run")
    def test_returns_false_when_no_audio(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="")
        assert has_audio_stream("/tmp/test.mp4") is False

    @patch("audio.renderer.subprocess.run")
    def test_calls_ffprobe(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="")
        has_audio_stream("/tmp/test.mp4")
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "ffprobe"
        assert "/tmp/test.mp4" in cmd
