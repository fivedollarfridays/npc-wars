"""Compose match frames and encode to MP4 via ffmpeg."""

import subprocess
from typing import Any

from PIL import Image

from video.video_effects import render_effects
from video.video_grid import render_grid
from video.video_overlay import render_overlay
from video.video_sprites import render_bots

CELL_SIZE = 48
DEFAULT_FPS = 4
GRID_SIZE = 10


def _bot_positions(bots: list[dict[str, Any]]) -> dict[str, tuple[int, int]]:
    """Build emoji -> (col, row) lookup from bot state list."""
    return {b["emoji"]: (b["x"], b["y"]) for b in bots}


def _round_kills(
    eliminations: list[dict[str, Any]], up_to_round: int,
) -> list[dict[str, Any]]:
    """Return kills up to this round, newest first (for kill feed)."""
    kills = [
        {"killer": e.get("killed_by", "?"), "victim": e["emoji"], "round": e["round"]}
        for e in eliminations
        if e["round"] <= up_to_round
    ]
    return list(reversed(kills))


def render_frame(
    round_data: dict[str, Any],
    eliminations: list[dict[str, Any]],
    grid_size: int = GRID_SIZE,
    cell_size: int = CELL_SIZE,
) -> Image.Image:
    """Render a single round as a PIL Image frame."""
    storm_border = round_data.get("storm_border", 0)
    # "bots" is the current schema; "positions" is the legacy key from early matches.
    bots = round_data.get("bots") or round_data.get("positions", [])
    events = round_data.get("events", [])
    round_num = round_data.get("round", 0)

    img = render_grid(grid_size, storm_border, cell_size)
    render_bots(img, bots, cell_size)
    render_effects(img, events, _bot_positions(bots), cell_size)
    kills = _round_kills(eliminations, round_num)
    return render_overlay(img, round_num, bots, kills)


def frames_from_match(
    match_data: dict[str, Any], cell_size: int = CELL_SIZE,
) -> list[Image.Image]:
    """Generate one PIL Image per round from match data."""
    rounds = match_data.get("rounds", [])
    eliminations = match_data.get("eliminations", [])
    grid_size = match_data.get("grid_size", GRID_SIZE)
    return [render_frame(r, eliminations, grid_size, cell_size) for r in rounds]


def _pad_even(value: int) -> int:
    """Pad value to the next even number (H.264 requires even dims)."""
    return value + (value % 2)


def encode_frames(
    frames: list[Image.Image], output_path: str, fps: int = DEFAULT_FPS,
) -> str:
    """Encode a list of PIL Images to MP4 via ffmpeg stdin pipe.

    Returns the output_path.
    Raises RuntimeError if ffmpeg fails, ValueError if no frames.
    """
    if not frames:
        raise ValueError("No frames to encode")

    w, h = frames[0].size
    padded_w = _pad_even(w)
    padded_h = _pad_even(h)

    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{padded_w}x{padded_h}",
        "-pix_fmt", "rgb24",
        "-r", str(fps),
        "-i", "pipe:0",
        "-vcodec", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "fast",
        output_path,
    ]
    # Stream frames one at a time — avoids buffering all raw pixel data in memory.
    # stdout is not piped so only stderr needs draining (no deadlock risk).
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    for frame in frames:
        if frame.size != (padded_w, padded_h):
            padded = Image.new("RGB", (padded_w, padded_h), (0, 0, 0))
            padded.paste(frame, (0, 0))
            frame = padded
        proc.stdin.write(frame.tobytes())  # type: ignore[union-attr]
    proc.stdin.close()  # type: ignore[union-attr]
    stderr_data = proc.stderr.read()  # type: ignore[union-attr]
    proc.wait()

    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {stderr_data.decode()}")

    return output_path


def render_match_video(
    match_data: dict[str, Any],
    output_path: str,
    fps: int = DEFAULT_FPS,
    cell_size: int = CELL_SIZE,
) -> str:
    """Full pipeline: match_data -> MP4 file.

    Returns the output_path.
    """
    frames = frames_from_match(match_data, cell_size)
    return encode_frames(frames, output_path, fps)
