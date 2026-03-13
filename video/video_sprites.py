"""Render bot sprites (labels, HP bars) onto a grid image."""

from PIL import Image, ImageDraw
from typing import Any

from video.colors import hp_color, _FONT

HP_BG = (40, 40, 40)       # bar background
DEAD_FILL = (60, 60, 60)   # grey fill for dead bots
DEAD_X_COLOR = (150, 150, 150)  # cross lines on dead bot
LABEL_COLOR = (220, 220, 220)


def _draw_hp_bar(
    draw: ImageDraw.ImageDraw,
    x0: int,
    y0: int,
    cell_size: int,
    hp: int,
) -> None:
    """Draw HP bar at bottom of cell."""
    bar_h = max(4, cell_size // 12)
    bar_y = y0 + cell_size - bar_h - 2
    bar_w = cell_size - 4
    # Background
    draw.rectangle(
        [x0 + 2, bar_y, x0 + 2 + bar_w, bar_y + bar_h],
        fill=HP_BG,
    )
    # Filled portion
    fill_w = int(bar_w * max(0, hp) / 100)
    if fill_w > 0:
        draw.rectangle(
            [x0 + 2, bar_y, x0 + 2 + fill_w, bar_y + bar_h],
            fill=hp_color(hp),
        )


def _draw_label(
    draw: ImageDraw.ImageDraw,
    x0: int,
    y0: int,
    cell_size: int,
    text: str,
) -> None:
    """Draw emoji/name label centered in cell."""
    tx = x0 + cell_size // 2
    ty = y0 + cell_size // 3
    draw.text((tx, ty), text, fill=LABEL_COLOR, font=_FONT, anchor="mm")


def _draw_dead(
    draw: ImageDraw.ImageDraw,
    x0: int,
    y0: int,
    cell_size: int,
) -> None:
    """Draw grey fill and X cross for dead bot cell."""
    draw.rectangle(
        [x0 + 1, y0 + 1, x0 + cell_size - 2, y0 + cell_size - 2],
        fill=DEAD_FILL,
    )
    draw.line(
        [x0 + 4, y0 + 4, x0 + cell_size - 4, y0 + cell_size - 4],
        fill=DEAD_X_COLOR,
        width=2,
    )
    draw.line(
        [x0 + cell_size - 4, y0 + 4, x0 + 4, y0 + cell_size - 4],
        fill=DEAD_X_COLOR,
        width=2,
    )


def render_bots(
    img: Image.Image,
    bots: list[dict[str, Any]],
    cell_size: int = 48,
) -> Image.Image:
    """Draw all bots onto the grid image.

    Args:
        img: PIL Image (modified in place).
        bots: List of bot state dicts with keys: name, emoji, x, y, hp.
        cell_size: Pixel size of each grid cell.

    Returns:
        The same image with bots drawn on it.
    """
    draw = ImageDraw.Draw(img)
    for bot in bots:
        x0 = bot["x"] * cell_size
        y0 = bot["y"] * cell_size
        hp = bot.get("hp", 0)
        label = bot.get("emoji") or bot["name"][:2]

        if hp <= 0:
            _draw_dead(draw, x0, y0, cell_size)
        else:
            _draw_label(draw, x0, y0, cell_size, label)
            _draw_hp_bar(draw, x0, y0, cell_size, hp)

    return img
