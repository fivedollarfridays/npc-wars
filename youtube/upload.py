"""YouTube upload pipeline — metadata generation, thumbnail extraction, video upload."""

import os
import subprocess
from pathlib import Path
from typing import Any

from googleapiclient.http import MediaFileUpload

YOUTUBE_CATEGORY_GAMING = "20"  # YouTube Data API category ID for Gaming


def _player_name(emoji: str, players: list[dict]) -> str:
    """Return the player name for a given emoji, or the emoji itself if not found."""
    for p in players:
        if p.get("emoji") == emoji:
            return p["name"]
    return emoji


def _format_elim_lines(eliminations: list[dict], players: list[dict]) -> str:
    lines = [
        f"  Round {e.get('round', '?')}: "
        f"{_player_name(e.get('emoji', '?'), players)} eliminated by "
        f"{_player_name(e.get('killed_by', '?'), players)} ({e.get('cause', '?')})"
        for e in eliminations
    ]
    return "\n".join(lines) if lines else "  (no eliminations)"


def build_metadata(match_data: dict) -> dict:
    """Build YouTube video metadata from match result data.

    Returns:
        Dict with title, description, tags, category_id.
    """
    match_id = match_data.get("match_id", "?")
    winner_emoji = match_data.get("winner", "?")
    duration = match_data.get("duration_rounds", 0)
    players = match_data.get("players", [])
    eliminations = match_data.get("eliminations", [])

    winner_name = _player_name(winner_emoji, players)
    title = f"NPC Wars Match #{match_id} — {winner_name} wins!"

    player_lines = "\n".join(
        f"  {p.get('emoji', '')} {p['name']} by {p.get('author', '?')} — {p.get('bio', '')}" for p in players
    )
    description = (
        f"Match #{match_id} — {duration} rounds\n\n"
        f"Winner: {winner_name} {winner_emoji}\n\n"
        f"Contestants:\n{player_lines}\n\n"
        f"Eliminations:\n{_format_elim_lines(eliminations, players)}\n\n"
        f"#NPCWars #BattleRoyale #AIBots"
    )
    tags = ["NPC Wars", "npc-wars", "Battle Royale", "AI Bots", "gaming"] + [p["name"] for p in players]
    return {"title": title, "description": description, "tags": tags, "category_id": YOUTUBE_CATEGORY_GAMING}


def _validate_path(path: str, base_dir: str) -> None:
    """Raise ValueError if resolved path escapes base_dir."""
    resolved = Path(path).resolve()
    base = Path(base_dir).resolve()
    if not str(resolved).startswith(str(base) + os.sep) and resolved != base:
        raise ValueError(f"Path traversal detected: {path} escapes {base_dir}")


def extract_thumbnail(
    video_path: str,
    output_path: str,
    timestamp: str = "00:00:05",
    base_dir: str | None = None,
) -> str:
    """Extract a single frame from a video as a JPEG thumbnail using ffmpeg.

    Args:
        video_path: Path to the input video file.
        output_path: Path where the thumbnail JPEG will be written.
        timestamp: Timecode of the frame to extract (default: 5 seconds in).
        base_dir: If provided, both paths are validated to stay within this
            directory (prevents path traversal attacks). None skips validation.

    Returns:
        output_path on success.

    Raises:
        ValueError: If a path escapes base_dir (path traversal).
        RuntimeError: If ffmpeg exits with a non-zero return code.
    """
    if base_dir is not None:
        _validate_path(video_path, base_dir)
        _validate_path(output_path, base_dir)
    cmd = ["ffmpeg", "-y", "-ss", timestamp, "-i", video_path, "-vframes", "1", output_path]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed (rc={result.returncode}): {result.stderr.decode(errors='replace')}")
    return output_path


def _set_thumbnail(service: Any, video_id: str, thumbnail_path: str) -> None:
    """Upload and set a thumbnail for an already-uploaded video."""
    thumb_media = MediaFileUpload(thumbnail_path, mimetype="image/jpeg")
    service.thumbnails().set(videoId=video_id, media_body=thumb_media).execute()


def upload_video(
    service: Any,
    video_path: str,
    match_data: dict,
    privacy: str = "unlisted",
    thumbnail_path: str | None = None,
) -> str:
    """Upload a video to YouTube and optionally set its thumbnail.

    Args:
        service: Authenticated YouTube Data API v3 service resource.
        video_path: Path to the MP4 file to upload.
        match_data: Match result dict passed to build_metadata().
        privacy: YouTube privacy status — "unlisted", "public", or "private".
        thumbnail_path: Optional path to a JPEG thumbnail image.

    Returns:
        The YouTube video ID of the uploaded video.
    """
    metadata = build_metadata(match_data)
    body = {
        "snippet": {
            "title": metadata["title"],
            "description": metadata["description"],
            "tags": metadata["tags"],
            "categoryId": metadata["category_id"],
        },
        "status": {"privacyStatus": privacy},
    }
    media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
    response = service.videos().insert(part="snippet,status", body=body, media_body=media).execute()
    video_id = response["id"]
    if thumbnail_path is not None:
        _set_thumbnail(service, video_id, thumbnail_path)
    return video_id
