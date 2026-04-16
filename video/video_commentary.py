"""Burn commentary text into video frames as a bottom ticker overlay."""

from PIL import Image, ImageDraw

from video.colors import _FONT

# Drama-tier color coding: white=calm, yellow=heating, orange=intense,
# red=hype, magenta=chaos.
DRAMA_COLORS: dict[str, tuple[int, int, int]] = {
    "calm": (255, 255, 255),
    "heating": (255, 255, 0),
    "intense": (255, 165, 0),
    "hype": (255, 50, 50),
    "chaos": (255, 0, 255),
}

BANNER_HEIGHT = 28
BANNER_BG = (10, 10, 18, 200)  # semi-transparent dark
BANNER_PADDING = 6


def render_commentary_overlay(
    frame: Image.Image,
    text: str,
    tone: str,
) -> Image.Image:
    """Render commentary text as a bottom ticker on *frame*.

    Args:
        frame: Base PIL Image to overlay on (not mutated).
        text: Commentary line to display.
        tone: Drama tier — determines text color.

    Returns:
        New PIL Image with commentary banner burned in.
    """
    result = frame.copy().convert("RGBA")
    w, h = result.size

    # Draw semi-transparent banner at the bottom
    banner = Image.new("RGBA", (w, BANNER_HEIGHT), BANNER_BG)
    result.paste(banner, (0, h - BANNER_HEIGHT), banner)

    if text:
        color = DRAMA_COLORS.get(tone, DRAMA_COLORS["calm"])
        draw = ImageDraw.Draw(result)
        text_y = h - BANNER_HEIGHT + BANNER_PADDING
        draw.text((BANNER_PADDING, text_y), text, fill=color, font=_FONT)

    return result.convert("RGB")
