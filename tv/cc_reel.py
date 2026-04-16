"""Code Circuit highlight reel renderer — commentary card frames to MP4."""

from __future__ import annotations

from typing import Any

from PIL import Image, ImageDraw, ImageFont

from video.video_render import encode_frames

__all__ = ["render_cc_highlight_reel"]

_CARD_W = 680
_CARD_H = 480
_FONT = ImageFont.load_default()

_TONE_COLORS: dict[str, tuple[int, int, int]] = {
    "calm": (255, 255, 255),
    "heating": (255, 255, 0),
    "intense": (255, 165, 0),
    "hype": (255, 50, 50),
    "chaos": (255, 0, 255),
}


def render_cc_highlight_reel(
    episode: dict[str, Any],
    commentary: list[dict[str, Any]],
    output_path: str,
) -> str:
    """Render Code Circuit highlight reel as commentary card frames."""
    frames: list[Image.Image] = []

    frames.append(_text_card("Agent Grounds \u2014 Code Circuit", "hype"))

    lines = commentary or episode.get("match_commentary", {}).get("lines", [])
    for line in lines:
        frames.append(_text_card(line.get("text", ""), line.get("tone", "calm")))

    winner = episode.get("metadata", {}).get("winner", "?")
    frames.append(_text_card(f"Winner: {winner}", "hype"))

    if not frames:
        frames.append(_text_card("No highlights available", "calm"))

    # Hold each card ~2s at 4fps
    expanded: list[Image.Image] = []
    for f in frames:
        expanded.extend([f] * 8)

    return encode_frames(expanded, output_path, fps=4)


def _text_card(text: str, tone: str) -> Image.Image:
    """Render a single text card frame."""
    img = Image.new("RGB", (_CARD_W, _CARD_H), (10, 10, 18))
    draw = ImageDraw.Draw(img)
    color = _TONE_COLORS.get(tone, (255, 255, 255))

    wrapped = _wrap_text(text, max_chars=50)
    y = _CARD_H // 2 - len(wrapped) * 10
    for line in wrapped:
        bbox = draw.textbbox((0, 0), line, font=_FONT)
        tw = bbox[2] - bbox[0]
        x = (_CARD_W - tw) // 2
        draw.text((x, y), line, fill=color, font=_FONT)
        y += 20

    return img


def _wrap_text(text: str, max_chars: int = 50) -> list[str]:
    """Simple word-wrap."""
    words = text.split()
    lines: list[str] = []
    current = ""
    for w in words:
        if current and len(current) + 1 + len(w) > max_chars:
            lines.append(current)
            current = w
        else:
            current = f"{current} {w}" if current else w
    if current:
        lines.append(current)
    return lines or [""]
