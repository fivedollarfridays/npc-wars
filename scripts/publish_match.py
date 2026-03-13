#!/usr/bin/env python3
"""CLI: render a match JSON to MP4 and upload it to YouTube.

Usage:
    python scripts/publish_match.py results/match_001.json
    python scripts/publish_match.py results/match_001.json --privacy public --keep
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from video.video_render import render_match_video
from youtube.auth import authenticate, get_youtube_service
from youtube.upload import upload_video

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DEFAULT_SECRETS = os.path.join(_PROJECT_ROOT, "youtube", "client_secrets.json")
_DEFAULT_TOKEN = os.path.join(_PROJECT_ROOT, "youtube", "token.json")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render NPC Wars match and upload to YouTube")
    parser.add_argument("match_json", help="Path to match JSON file")
    parser.add_argument(
        "--privacy",
        default="unlisted",
        choices=["unlisted", "public", "private"],
        help="YouTube privacy status (default: unlisted)",
    )
    parser.add_argument("--keep", action="store_true", help="Keep the rendered MP4 after upload")
    parser.add_argument("--secrets", default=_DEFAULT_SECRETS, help="Path to client_secrets.json")
    parser.add_argument("--token", default=_DEFAULT_TOKEN, help="Path to OAuth token file")
    return parser.parse_args(argv)


def _render(match_data: dict, output_path: str) -> None:
    rounds = len(match_data.get("rounds", []))
    print(f"Rendering {rounds} rounds -> {output_path}")
    render_match_video(match_data, output_path)


def _upload(match_data: dict, video_path: str, privacy: str, secrets: str, token: str) -> str:
    print("Authenticating with YouTube...")
    creds = authenticate(secrets, token)
    service = get_youtube_service(creds)
    print("Uploading video...")
    return upload_video(service, video_path, match_data, privacy=privacy)


def _main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    if not os.path.exists(args.match_json):
        print(f"Error: file not found: {args.match_json}", file=sys.stderr)
        return 1

    try:
        with open(args.match_json) as f:
            match_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON in {args.match_json}: {e}", file=sys.stderr)
        return 1

    base = os.path.splitext(args.match_json)[0]
    video_path = base + ".mp4"

    try:
        _render(match_data, video_path)
    except Exception as e:
        print(f"Error rendering video: {e}", file=sys.stderr)
        return 1

    try:
        video_id = _upload(match_data, video_path, args.privacy, args.secrets, args.token)
    except Exception as e:
        print(f"Error uploading video: {e}", file=sys.stderr)
        return 1
    finally:
        if not args.keep:
            try:
                os.remove(video_path)
            except FileNotFoundError:
                pass

    print(f"Uploaded: https://youtu.be/{video_id}")
    return 0


if __name__ == "__main__":
    sys.exit(_main())
