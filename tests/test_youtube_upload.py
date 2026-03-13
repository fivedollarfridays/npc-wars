"""Tests for youtube/upload.py — metadata generation and video upload pipeline."""

from unittest.mock import MagicMock, patch

SAMPLE_MATCH = {
    "match_id": 42,
    "winner": "🦆",
    "duration_rounds": 87,
    "seed": 1234,
    "players": [
        {"name": "DuckBot", "emoji": "🦆", "bio": "quack", "author": "alice"},
        {"name": "GooseBot", "emoji": "🪿", "bio": "honk", "author": "bob"},
        {"name": "FrogBot", "emoji": "🐸", "bio": "ribbit", "author": "carol"},
    ],
    "eliminations": [
        {"round": 30, "emoji": "🐸", "killed_by": "🦆", "cause": "attack"},
        {"round": 87, "emoji": "🪿", "killed_by": "🦆", "cause": "attack"},
    ],
}


# ---------------------------------------------------------------------------
# build_metadata
# ---------------------------------------------------------------------------


class TestBuildMetadata:
    def test_title_includes_match_id_and_winner(self):
        from youtube.upload import build_metadata

        meta = build_metadata(SAMPLE_MATCH)
        assert "42" in meta["title"]
        assert "DuckBot" in meta["title"] or "🦆" in meta["title"]

    def test_description_includes_round_count(self):
        from youtube.upload import build_metadata

        meta = build_metadata(SAMPLE_MATCH)
        assert "87" in meta["description"]

    def test_description_includes_all_players(self):
        from youtube.upload import build_metadata

        meta = build_metadata(SAMPLE_MATCH)
        for player in SAMPLE_MATCH["players"]:
            assert player["name"] in meta["description"]

    def test_description_includes_eliminations(self):
        from youtube.upload import build_metadata

        meta = build_metadata(SAMPLE_MATCH)
        # At least the winner's kills should appear
        assert "DuckBot" in meta["description"]

    def test_tags_is_list_of_strings(self):
        from youtube.upload import build_metadata

        meta = build_metadata(SAMPLE_MATCH)
        assert isinstance(meta["tags"], list)
        assert all(isinstance(t, str) for t in meta["tags"])

    def test_tags_include_npc_wars(self):
        from youtube.upload import build_metadata

        meta = build_metadata(SAMPLE_MATCH)
        tags_lower = [t.lower() for t in meta["tags"]]
        assert any("npc" in t or "wars" in t for t in tags_lower)

    def test_category_id_is_gaming(self):
        from youtube.upload import build_metadata

        meta = build_metadata(SAMPLE_MATCH)
        assert meta["category_id"] == "20"

    def test_no_players_no_crash(self):
        from youtube.upload import build_metadata

        meta = build_metadata({"match_id": 1, "winner": "?", "duration_rounds": 0, "players": [], "eliminations": []})
        assert "title" in meta
        assert "description" in meta


# ---------------------------------------------------------------------------
# extract_thumbnail
# ---------------------------------------------------------------------------


class TestExtractThumbnail:
    def test_calls_ffmpeg_to_extract_frame(self, tmp_path):
        from youtube.upload import extract_thumbnail

        video = str(tmp_path / "match.mp4")
        thumb = str(tmp_path / "thumb.jpg")

        with patch("youtube.upload.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            extract_thumbnail(video, thumb)

        assert mock_run.called
        cmd = mock_run.call_args[0][0]
        assert "ffmpeg" in cmd
        assert video in cmd
        assert thumb in cmd

    def test_returns_output_path(self, tmp_path):
        from youtube.upload import extract_thumbnail

        video = str(tmp_path / "match.mp4")
        thumb = str(tmp_path / "thumb.jpg")

        with patch("youtube.upload.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = extract_thumbnail(video, thumb)

        assert result == thumb

    def test_raises_on_ffmpeg_failure(self, tmp_path):
        import pytest
        from youtube.upload import extract_thumbnail

        with patch("youtube.upload.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr=b"error")
            with pytest.raises(RuntimeError, match="ffmpeg"):
                extract_thumbnail("video.mp4", "thumb.jpg")


# ---------------------------------------------------------------------------
# upload_video
# ---------------------------------------------------------------------------


class TestUploadVideo:
    def _make_service(self, video_id="yt_abc123"):
        """Build a mock YouTube service that returns video_id on insert."""
        service = MagicMock()
        insert_request = MagicMock()
        insert_request.execute.return_value = {"id": video_id}
        service.videos.return_value.insert.return_value = insert_request
        return service

    def test_returns_video_id(self, tmp_path):
        from youtube.upload import upload_video

        service = self._make_service("vid_001")
        video_path = str(tmp_path / "match.mp4")
        # Create a dummy file so MediaFileUpload doesn't error
        with open(video_path, "wb") as f:
            f.write(b"\x00" * 10)

        with patch("youtube.upload.MediaFileUpload"):
            result = upload_video(service, video_path, SAMPLE_MATCH)

        assert result == "vid_001"

    def test_calls_videos_insert_with_correct_privacy(self, tmp_path):
        from youtube.upload import upload_video

        service = self._make_service()
        video_path = str(tmp_path / "match.mp4")
        with open(video_path, "wb") as f:
            f.write(b"\x00" * 10)

        with patch("youtube.upload.MediaFileUpload"):
            upload_video(service, video_path, SAMPLE_MATCH, privacy="public")

        call_kwargs = service.videos.return_value.insert.call_args[1]
        assert call_kwargs["body"]["status"]["privacyStatus"] == "public"

    def test_default_privacy_is_unlisted(self, tmp_path):
        from youtube.upload import upload_video

        service = self._make_service()
        video_path = str(tmp_path / "match.mp4")
        with open(video_path, "wb") as f:
            f.write(b"\x00" * 10)

        with patch("youtube.upload.MediaFileUpload"):
            upload_video(service, video_path, SAMPLE_MATCH)

        call_kwargs = service.videos.return_value.insert.call_args[1]
        assert call_kwargs["body"]["status"]["privacyStatus"] == "unlisted"

    def test_sets_thumbnail_when_provided(self, tmp_path):
        from youtube.upload import upload_video

        service = self._make_service("vid_002")
        video_path = str(tmp_path / "match.mp4")
        thumb_path = str(tmp_path / "thumb.jpg")
        with open(video_path, "wb") as f:
            f.write(b"\x00" * 10)
        with open(thumb_path, "wb") as f:
            f.write(b"\xff" * 10)

        thumbnail_request = MagicMock()
        thumbnail_request.execute.return_value = {}
        service.thumbnails.return_value.set.return_value = thumbnail_request

        with patch("youtube.upload.MediaFileUpload"):
            upload_video(service, video_path, SAMPLE_MATCH, thumbnail_path=thumb_path)

        service.thumbnails.return_value.set.assert_called_once()
        call_kwargs = service.thumbnails.return_value.set.call_args[1]
        assert call_kwargs["videoId"] == "vid_002"

    def test_skips_thumbnail_when_not_provided(self, tmp_path):
        from youtube.upload import upload_video

        service = self._make_service()
        video_path = str(tmp_path / "match.mp4")
        with open(video_path, "wb") as f:
            f.write(b"\x00" * 10)

        with patch("youtube.upload.MediaFileUpload"):
            upload_video(service, video_path, SAMPLE_MATCH)

        service.thumbnails.assert_not_called()

    def test_uses_resumable_upload(self, tmp_path):
        from youtube.upload import upload_video

        service = self._make_service()
        video_path = str(tmp_path / "match.mp4")
        with open(video_path, "wb") as f:
            f.write(b"\x00" * 10)

        with patch("youtube.upload.MediaFileUpload") as mock_media:
            upload_video(service, video_path, SAMPLE_MATCH)

        _, kwargs = mock_media.call_args
        assert kwargs.get("resumable") is True
