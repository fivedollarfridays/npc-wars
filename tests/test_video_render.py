"""Tests for video/video_render.py — frame composition and MP4 encoding."""

import os
from typing import Any

from PIL import Image

MINIMAL_MATCH: dict[str, Any] = {
    "match_id": 1,
    "winner": "\U0001f986",
    "duration_rounds": 2,
    "seed": 42,
    "players": [
        {
            "name": "DuckBot",
            "emoji": "\U0001f986",
            "bio": "test",
            "author": "test",
            "x": 0,
            "y": 0,
        },
        {
            "name": "GooseBot",
            "emoji": "\U0001fabf",
            "bio": "test",
            "author": "test",
            "x": 1,
            "y": 1,
        },
    ],
    "rounds": [
        {
            "round": 1,
            "storm_border": 0,
            "bots": [
                {
                    "name": "DuckBot",
                    "emoji": "\U0001f986",
                    "x": 0,
                    "y": 0,
                    "hp": 100,
                    "energy": 100,
                },
                {
                    "name": "GooseBot",
                    "emoji": "\U0001fabf",
                    "x": 1,
                    "y": 1,
                    "hp": 80,
                    "energy": 90,
                },
            ],
            "events": [
                {
                    "type": "attack",
                    "attacker": "\U0001f986",
                    "target": "\U0001fabf",
                    "damage": 20,
                    "target_hp": 80,
                },
            ],
        },
        {
            "round": 2,
            "storm_border": 0,
            "bots": [
                {
                    "name": "DuckBot",
                    "emoji": "\U0001f986",
                    "x": 0,
                    "y": 0,
                    "hp": 100,
                    "energy": 100,
                },
                {
                    "name": "GooseBot",
                    "emoji": "\U0001fabf",
                    "x": 1,
                    "y": 1,
                    "hp": 0,
                    "energy": 0,
                },
            ],
            "events": [
                {
                    "type": "death",
                    "emoji": "\U0001fabf",
                    "killed_by": "\U0001f986",
                    "cause": "attack",
                },
            ],
        },
    ],
    "eliminations": [
        {
            "round": 2,
            "emoji": "\U0001fabf",
            "cause": "attack",
            "killed_by": "\U0001f986",
        },
    ],
}


# ---------------------------------------------------------------------------
# frames_from_match
# ---------------------------------------------------------------------------


class TestFramesFromMatch:
    """Tests for frames_from_match()."""

    def test_returns_list(self) -> None:
        from video.video_render import frames_from_match

        result = frames_from_match(MINIMAL_MATCH)
        assert isinstance(result, list)
        assert all(isinstance(f, Image.Image) for f in result)

    def test_count_matches_rounds(self) -> None:
        from video.video_render import frames_from_match

        frames = frames_from_match(MINIMAL_MATCH)
        assert len(frames) == len(MINIMAL_MATCH["rounds"])

    def test_frame_has_correct_dimensions(self) -> None:
        from video.video_render import frames_from_match, CELL_SIZE, GRID_SIZE
        from video.video_overlay import SIDEBAR_WIDTH

        frames = frames_from_match(MINIMAL_MATCH)
        expected_w = GRID_SIZE * CELL_SIZE + SIDEBAR_WIDTH
        expected_h = GRID_SIZE * CELL_SIZE
        for frame in frames:
            assert frame.size == (expected_w, expected_h)


# ---------------------------------------------------------------------------
# encode_frames
# ---------------------------------------------------------------------------


class TestEncodeFrames:
    """Tests for encode_frames()."""

    def test_creates_file(self, tmp_path: Any) -> None:
        from video.video_render import encode_frames

        # Create simple test frames with even dimensions
        frames = [Image.new("RGB", (480, 480), (r * 50, 0, 0)) for r in range(3)]
        out = str(tmp_path / "test.mp4")
        encode_frames(frames, out, fps=4)
        assert os.path.exists(out)

    def test_file_is_nonzero(self, tmp_path: Any) -> None:
        from video.video_render import encode_frames

        frames = [Image.new("RGB", (480, 480), (0, g * 50, 0)) for g in range(3)]
        out = str(tmp_path / "test.mp4")
        encode_frames(frames, out, fps=4)
        assert os.path.getsize(out) > 0


# ---------------------------------------------------------------------------
# render_match_video (end-to-end)
# ---------------------------------------------------------------------------


class TestRenderMatchVideo:
    """End-to-end test for render_match_video()."""

    def test_creates_mp4(self, tmp_path: Any) -> None:
        from video.video_render import render_match_video

        out = str(tmp_path / "match.mp4")
        render_match_video(MINIMAL_MATCH, out)
        assert os.path.exists(out)
        assert os.path.getsize(out) > 0
