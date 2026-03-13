"""Render scoreboard overlay sidebar for NPC Wars video frames."""

from PIL import Image, ImageDraw
from typing import Any

from video.colors import hp_color, _FONT

SIDEBAR_WIDTH = 200
SIDEBAR_BG = (20, 20, 28)
TEXT_COLOR = (220, 220, 220)
ACCENT_COLOR = (100, 160, 255)
DEAD_COLOR = (80, 80, 80)
KILL_COLOR = (255, 100, 100)
SECTION_HEIGHT = 18


def _draw_section_header(
    draw: ImageDraw.ImageDraw, x: int, y: int, text: str,
) -> int:
    """Draw a section header, return next y position."""
    draw.text((x + 4, y), text, fill=ACCENT_COLOR, font=_FONT)
    return y + SECTION_HEIGHT


def _draw_bot_row(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    bot: dict[str, Any],
    width: int,
) -> int:
    """Draw a single bot row with mini HP bar. Return next y."""
    hp = bot.get("hp", 0)
    label = f"{bot.get('emoji', '?')} {bot['name'][:8]}"
    color = DEAD_COLOR if hp <= 0 else TEXT_COLOR
    draw.text((x + 4, y), label, fill=color, font=_FONT)
    # Mini HP bar
    bar_w = width - 8
    bar_h = 3
    bar_y = y + SECTION_HEIGHT - 5
    draw.rectangle(
        [x + 4, bar_y, x + 4 + bar_w, bar_y + bar_h], fill=(40, 40, 40),
    )
    if hp > 0:
        fill = int(bar_w * hp / 100)
        draw.rectangle(
            [x + 4, bar_y, x + 4 + fill, bar_y + bar_h],
            fill=hp_color(hp),
        )
    return y + SECTION_HEIGHT


def _draw_kill_row(
    draw: ImageDraw.ImageDraw, x: int, y: int, kill: dict[str, Any],
) -> int:
    """Draw a kill feed entry. Return next y."""
    text = f"{kill['killer']}\u2192{kill['victim']}"
    draw.text((x + 4, y), text, fill=KILL_COLOR, font=_FONT)
    return y + SECTION_HEIGHT


def _draw_bot_roster(
    draw: ImageDraw.ImageDraw,
    sx: int,
    y: int,
    bots: list[dict[str, Any]],
    sidebar_width: int,
    max_y: int,
) -> int:
    """Draw the bot roster section. Return next y position."""
    y = _draw_section_header(draw, sx, y, "\u2500\u2500 Bots \u2500\u2500")
    sorted_bots = sorted(
        bots, key=lambda b: (b.get("hp", 0) <= 0, -b.get("hp", 0)),
    )
    for bot in sorted_bots:
        if y + SECTION_HEIGHT > max_y:
            break
        y = _draw_bot_row(draw, sx, y, bot, sidebar_width)
    return y


def _draw_kill_feed(
    draw: ImageDraw.ImageDraw,
    sx: int,
    y: int,
    kills: list[dict[str, Any]],
    max_y: int,
) -> int:
    """Draw the kill feed section. Return next y position."""
    if not kills or y + SECTION_HEIGHT >= max_y:
        return y
    y = _draw_section_header(draw, sx, y, "\u2500\u2500 Kills \u2500\u2500")
    for kill in kills[:5]:
        if y + SECTION_HEIGHT > max_y:
            break
        y = _draw_kill_row(draw, sx, y, kill)
    return y


def render_overlay(
    grid_img: Image.Image,
    round_num: int,
    bots: list[dict[str, Any]],
    kills: list[dict[str, Any]],
    sidebar_width: int = SIDEBAR_WIDTH,
) -> Image.Image:
    """Append a scoreboard sidebar to the right of the grid image.

    Args:
        grid_img: The rendered grid (with sprites/effects).
        round_num: Current round number.
        bots: All bots with name, emoji, hp fields.
        kills: Recent kills [{killer, victim, round}], newest first.
        sidebar_width: Width of the sidebar panel in pixels.

    Returns:
        New wider image: grid + sidebar.
    """
    gw, gh = grid_img.size
    frame = Image.new("RGB", (gw + sidebar_width, gh), SIDEBAR_BG)
    frame.paste(grid_img, (0, 0))

    draw = ImageDraw.Draw(frame)
    sx = gw  # sidebar x start
    y = 8

    # Round counter
    draw.text((sx + 4, y), f"Round {round_num}", fill=TEXT_COLOR, font=_FONT)
    y += SECTION_HEIGHT

    # Alive count
    alive = sum(1 for b in bots if b.get("hp", 0) > 0)
    draw.text((sx + 4, y), f"{alive} alive", fill=ACCENT_COLOR, font=_FONT)
    y += SECTION_HEIGHT + 4

    y = _draw_bot_roster(draw, sx, y, bots, sidebar_width, gh - 4)
    y += 4
    _draw_kill_feed(draw, sx, y, kills, gh - 4)

    return frame
