#!/usr/bin/env python3
"""CLI: render a match JSON to an MP4 video.

Usage:
    python scripts/render_video.py results/match_001.json
    python scripts/render_video.py results/match_001.json --output match.mp4 --fps 8
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Render NPC Wars match to MP4")
    parser.add_argument("match_json", help="Path to match JSON file")
    parser.add_argument("--output", "-o", help="Output MP4 path (default: <match>.mp4)")
    parser.add_argument("--fps", type=int, default=4, help="Frames per second (default: 4)")
    return parser.parse_args(argv)


def _default_output(input_path: str) -> str:
    """Derive output MP4 path from input JSON path."""
    base = os.path.splitext(input_path)[0]
    return base + ".mp4"


def _main(argv: list[str] | None = None) -> int:
    """Entry point. Returns exit code."""
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

    output_path = args.output or _default_output(args.match_json)

    rounds = len(match_data.get("rounds", []))
    print(f"Rendering {rounds} frames at {args.fps} FPS -> {output_path}")

    try:
        from video.video_render import render_match_video

        render_match_video(match_data, output_path, fps=args.fps)
        print(f"Done: {output_path}")
        return 0
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(_main())
