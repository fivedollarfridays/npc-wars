"""TV rendering pipeline — match JSON to MP4 + episode JSON.

Processes queued match JSONs (Kill Switch and Code Circuit) through
the TV enrichment pipeline, builds episode manifests, and renders
MP4 files with commentary overlay.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

from discord_bot.commands.submissions import validate_match_json
from engine.episode import build_episode
from engine.tv_pipeline import enrich_tv
from tv.cc_reel import render_cc_highlight_reel
from video.video_render import render_match_video

__all__ = ["process_match", "process_queue"]

log = logging.getLogger(__name__)

_DISCORD_MAX_BYTES = 25 * 1024 * 1024


def process_match(
    match_path: str,
    output_dir: str,
    *,
    results_dir: str = "results",
    patterns_dir: str = "data/rival_patterns",
) -> tuple[str, str]:
    """Process a single match JSON into MP4 + episode JSON.

    Returns (mp4_path, episode_json_path).
    Raises ValueError for corrupt or unrecognised JSON.
    """
    t0 = time.monotonic()
    path = Path(match_path)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    data = _load_and_validate(path)
    game = _detect_game(data, path.name)

    enrich_tv(data, results_dir=results_dir, patterns_dir=patterns_dir)
    episode, episode_path = _build_and_save_episode(data, out, path.stem)
    mp4_path = _render_video(game, data, episode, out, path.stem)

    _log_result(path.name, game, mp4_path, t0)
    return mp4_path, str(episode_path)


def process_queue(
    queue_dir: str,
    output_dir: str,
    *,
    results_dir: str = "results",
    patterns_dir: str = "data/rival_patterns",
) -> list[dict[str, Any]]:
    """Process all queued match JSONs sequentially.

    Returns list of result dicts. Corrupt entries are logged and skipped.
    """
    qdir = Path(queue_dir)
    if not qdir.exists():
        return []

    results: list[dict[str, Any]] = []
    for entry in sorted(qdir.glob("*.json")):
        try:
            mp4, ep = process_match(
                str(entry), output_dir,
                results_dir=results_dir, patterns_dir=patterns_dir,
            )
            results.append({"ok": True, "file": entry.name, "mp4": mp4, "episode": ep})
        except Exception:
            log.error("Failed to process %s", entry.name, exc_info=True)
            results.append({"ok": False, "file": entry.name, "error": entry.name})

    return results


def _load_and_validate(path: Path) -> dict[str, Any]:
    """Load and parse JSON from path. Raises ValueError on failure."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError(f"Invalid JSON in {path.name}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Corrupt match data in {path.name}: expected dict")
    return data


def _detect_game(data: dict[str, Any], filename: str) -> str:
    ok, game, err = validate_match_json(data)
    if not ok:
        raise ValueError(f"Unrecognised match schema in {filename}: {err}")
    return game  # type: ignore[return-value]


def _rivalries_to_list(rivalries: dict[str, Any] | list) -> list[dict[str, Any]]:
    if isinstance(rivalries, list):
        return rivalries
    result: list[dict[str, Any]] = []
    for key, stats in rivalries.items():
        parts = key.split(":")
        if len(parts) == 2:
            result.append({"emoji_a": parts[0], "emoji_b": parts[1], **stats})
    return result


def _build_and_save_episode(
    data: dict[str, Any], out: Path, stem: str,
) -> tuple[dict[str, Any], Path]:
    commentary = data.get("commentary", [])
    highlights = data.get("highlights", [])
    profiles = data.get("profiles", {})
    rivalries = _rivalries_to_list(data.get("rivalries", {}))

    episode = build_episode(data, commentary, highlights, profiles, rivalries, [])
    episode_path = out / f"{stem}_episode.json"
    episode_path.write_text(json.dumps(episode, default=str), encoding="utf-8")
    return episode, episode_path


def _render_video(
    game: str, data: dict[str, Any], episode: dict[str, Any],
    out: Path, stem: str,
) -> str:
    mp4_path = str(out / f"{stem}.mp4")
    if game == "kill_switch":
        render_match_video(data, mp4_path, audio=True)
    else:
        render_cc_highlight_reel(episode, data.get("commentary", []), mp4_path)
    return mp4_path


def _log_result(filename: str, game: str, mp4_path: str, t0: float) -> None:
    elapsed = time.monotonic() - t0
    size_mb = Path(mp4_path).stat().st_size / (1024 * 1024)
    log.info("Processed %s in %.1fs (%.1f MB, game=%s)", filename, elapsed, size_mb, game)
    if size_mb > 25:
        log.warning("Output %s exceeds 25 MB Discord limit (%.1f MB)", mp4_path, size_mb)
