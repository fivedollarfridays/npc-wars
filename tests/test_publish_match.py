"""Tests for scripts/publish_match.py — render + upload pipeline CLI."""

import json
import os
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SAMPLE_MATCH = {
    "match_id": 7,
    "winner": "🦆",
    "duration_rounds": 50,
    "seed": 42,
    "players": [
        {"name": "DuckBot", "emoji": "🦆", "bio": "quack", "author": "alice"},
        {"name": "GooseBot", "emoji": "🪿", "bio": "honk", "author": "bob"},
    ],
    "eliminations": [
        {"round": 50, "emoji": "🪿", "killed_by": "🦆", "cause": "attack"},
    ],
    "rounds": [{"round": i, "bots": []} for i in range(1, 51)],
}


def _write_match(path: str, data: dict = SAMPLE_MATCH) -> None:
    with open(path, "w") as f:
        json.dump(data, f)


# ---------------------------------------------------------------------------
# _parse_args
# ---------------------------------------------------------------------------


class TestParseArgs:
    def test_positional_match_json(self):
        from scripts.publish_match import _parse_args

        args = _parse_args(["match.json"])
        assert args.match_json == "match.json"

    def test_default_privacy_is_unlisted(self):
        from scripts.publish_match import _parse_args

        args = _parse_args(["match.json"])
        assert args.privacy == "unlisted"

    def test_custom_privacy(self):
        from scripts.publish_match import _parse_args

        args = _parse_args(["match.json", "--privacy", "public"])
        assert args.privacy == "public"

    def test_keep_flag_defaults_false(self):
        from scripts.publish_match import _parse_args

        args = _parse_args(["match.json"])
        assert args.keep is False

    def test_keep_flag_true_when_passed(self):
        from scripts.publish_match import _parse_args

        args = _parse_args(["match.json", "--keep"])
        assert args.keep is True


# ---------------------------------------------------------------------------
# _main — success path
# ---------------------------------------------------------------------------


class TestMainSuccess:
    def _run(self, tmp_path, privacy="unlisted", extra_args=None):
        """Helper: write a match file and run _main with all external I/O mocked."""
        from scripts.publish_match import _main

        match_path = str(tmp_path / "match_007.json")
        _write_match(match_path)

        mock_service = MagicMock()
        args = [match_path]
        if extra_args:
            args += extra_args

        with (
            patch("scripts.publish_match.render_match_video") as mock_render,
            patch("scripts.publish_match.authenticate", return_value=MagicMock()) as mock_auth,
            patch("scripts.publish_match.get_youtube_service", return_value=mock_service),
            patch("scripts.publish_match.upload_video", return_value="vid_XYZ") as mock_upload,
        ):
            rc = _main(args)

        return rc, mock_render, mock_auth, mock_upload

    def test_returns_exit_0_on_success(self, tmp_path):
        rc, *_ = self._run(tmp_path)
        assert rc == 0

    def test_calls_render_match_video(self, tmp_path):
        _, mock_render, _, _ = self._run(tmp_path)
        assert mock_render.called

    def test_render_receives_match_data(self, tmp_path):
        _, mock_render, _, _ = self._run(tmp_path)
        call_args = mock_render.call_args[0]
        assert call_args[0]["match_id"] == 7

    def test_calls_upload_video(self, tmp_path):
        _, _, _, mock_upload = self._run(tmp_path)
        assert mock_upload.called

    def test_upload_receives_privacy(self, tmp_path):
        _, _, _, mock_upload = self._run(tmp_path, extra_args=["--privacy", "public"])
        _, kwargs = mock_upload.call_args
        assert kwargs.get("privacy") == "public"

    def test_upload_default_privacy_unlisted(self, tmp_path):
        _, _, _, mock_upload = self._run(tmp_path)
        _, kwargs = mock_upload.call_args
        assert kwargs.get("privacy") == "unlisted"

    def test_prints_youtube_url(self, tmp_path, capsys):
        self._run(tmp_path)
        out = capsys.readouterr().out
        assert "vid_XYZ" in out

    def test_temp_video_deleted_by_default(self, tmp_path):
        """After a successful upload the temp MP4 should be removed."""
        from scripts.publish_match import _main

        match_path = str(tmp_path / "match_007.json")
        _write_match(match_path)

        captured_video_path = {}

        def fake_render(match_data, output_path, **kwargs):
            captured_video_path["path"] = output_path
            # Create the file so deletion logic can find it
            with open(output_path, "wb") as f:
                f.write(b"\x00" * 4)

        with (
            patch("scripts.publish_match.render_match_video", side_effect=fake_render),
            patch("scripts.publish_match.authenticate", return_value=MagicMock()),
            patch("scripts.publish_match.get_youtube_service", return_value=MagicMock()),
            patch("scripts.publish_match.upload_video", return_value="vid_ABC"),
        ):
            _main([match_path])

        assert not os.path.exists(captured_video_path["path"])

    def test_keep_flag_preserves_temp_video(self, tmp_path):
        """With --keep the temp MP4 should survive after upload."""
        from scripts.publish_match import _main

        match_path = str(tmp_path / "match_007.json")
        _write_match(match_path)

        captured_video_path = {}

        def fake_render(match_data, output_path, **kwargs):
            captured_video_path["path"] = output_path
            with open(output_path, "wb") as f:
                f.write(b"\x00" * 4)

        with (
            patch("scripts.publish_match.render_match_video", side_effect=fake_render),
            patch("scripts.publish_match.authenticate", return_value=MagicMock()),
            patch("scripts.publish_match.get_youtube_service", return_value=MagicMock()),
            patch("scripts.publish_match.upload_video", return_value="vid_ABC"),
        ):
            _main([match_path, "--keep"])

        assert os.path.exists(captured_video_path["path"])


# ---------------------------------------------------------------------------
# _main — error paths
# ---------------------------------------------------------------------------


class TestMainErrors:
    def test_missing_json_exits_1(self, tmp_path):
        from scripts.publish_match import _main

        rc = _main([str(tmp_path / "nonexistent.json")])
        assert rc == 1

    def test_invalid_json_exits_1(self, tmp_path):
        from scripts.publish_match import _main

        bad = tmp_path / "bad.json"
        bad.write_text("not-json{{{")
        rc = _main([str(bad)])
        assert rc == 1

    def test_render_failure_exits_1(self, tmp_path):
        from scripts.publish_match import _main

        match_path = str(tmp_path / "match.json")
        _write_match(match_path)

        with patch("scripts.publish_match.render_match_video", side_effect=RuntimeError("ffmpeg died")):
            rc = _main([match_path])

        assert rc == 1

    def test_upload_failure_exits_1(self, tmp_path):
        from scripts.publish_match import _main

        match_path = str(tmp_path / "match.json")
        _write_match(match_path)

        with (
            patch("scripts.publish_match.render_match_video"),
            patch("scripts.publish_match.authenticate", return_value=MagicMock()),
            patch("scripts.publish_match.get_youtube_service", return_value=MagicMock()),
            patch("scripts.publish_match.upload_video", side_effect=Exception("API quota exceeded")),
        ):
            rc = _main([match_path])

        assert rc == 1

    def test_auth_failure_exits_1(self, tmp_path):
        from scripts.publish_match import _main

        match_path = str(tmp_path / "match.json")
        _write_match(match_path)

        with (
            patch("scripts.publish_match.render_match_video"),
            patch("scripts.publish_match.authenticate", side_effect=Exception("OAuth failed")),
        ):
            rc = _main([match_path])

        assert rc == 1
