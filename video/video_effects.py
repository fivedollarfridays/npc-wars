"""Render combat effects (hit flash, death marker, damage numbers) on a grid frame."""

from PIL import Image, ImageDraw, ImageFont
from typing import Any

HIT_FLASH_COLOR = (255, 255, 200, 120)   # pale yellow, semi-transparent
DEATH_COLOR = (255, 50, 50)              # bright red X
STORM_FLASH_COLOR = (180, 60, 60, 100)  # storm tint
DAMAGE_COLOR = (255, 220, 50)           # yellow damage text
MISS_COLOR = (150, 150, 150)            # grey miss text

_FONT = ImageFont.load_default()


def _cell_rect(col: int, row: int, cell_size: int) -> tuple[int, int, int, int]:
    """Return (x0, y0, x1, y1) for a cell."""
    x0 = col * cell_size
    y0 = row * cell_size
    return x0, y0, x0 + cell_size - 1, y0 + cell_size - 1


def _draw_hit_flash(
    draw: ImageDraw.ImageDraw, col: int, row: int, cell_size: int,
) -> None:
    """Draw a bright overlay on the hit cell."""
    x0, y0, x1, y1 = _cell_rect(col, row, cell_size)
    draw.rectangle([x0 + 2, y0 + 2, x1 - 2, y1 - 2], outline=(255, 255, 180), width=2)


def _draw_death_marker(
    draw: ImageDraw.ImageDraw, col: int, row: int, cell_size: int,
) -> None:
    """Draw a large red X on the death cell."""
    x0, y0, x1, y1 = _cell_rect(col, row, cell_size)
    pad = cell_size // 6
    draw.line([x0 + pad, y0 + pad, x1 - pad, y1 - pad], fill=DEATH_COLOR, width=3)
    draw.line([x1 - pad, y0 + pad, x0 + pad, y1 - pad], fill=DEATH_COLOR, width=3)


def _draw_damage_number(
    draw: ImageDraw.ImageDraw, col: int, row: int, cell_size: int, damage: int,
) -> None:
    """Draw damage number floating above the cell."""
    x = col * cell_size + cell_size // 2
    y = row * cell_size + cell_size // 4
    draw.text((x, y), f"-{damage}", fill=DAMAGE_COLOR, font=_FONT, anchor="mm")


def render_effects(
    img: Image.Image,
    events: list[dict[str, Any]],
    bot_positions: dict[str, tuple[int, int]],
    cell_size: int = 48,
) -> Image.Image:
    """Draw combat effects for this round's events onto the grid image.

    Args:
        img: PIL Image to draw on (modified in place).
        events: List of round event dicts (attack, death, storm_damage).
        bot_positions: Maps emoji -> (col, row).
        cell_size: Pixel size per cell.

    Returns:
        The same image with effects drawn.
    """
    draw = ImageDraw.Draw(img)
    for event in events:
        etype = event.get("type", "")
        if etype == "attack":
            _handle_attack(draw, event, bot_positions, cell_size)
        elif etype == "death":
            _handle_death(draw, event, bot_positions, cell_size)
        elif etype == "storm_damage":
            _handle_storm(draw, event, bot_positions, cell_size)
    return img


def _handle_attack(
    draw: ImageDraw.ImageDraw,
    event: dict[str, Any],
    bot_positions: dict[str, tuple[int, int]],
    cell_size: int,
) -> None:
    """Process an attack event: hit flash + damage number."""
    target = event.get("target", "")
    damage = event.get("damage", 0)
    if target in bot_positions:
        col, row = bot_positions[target]
        _draw_hit_flash(draw, col, row, cell_size)
        if damage > 0:
            _draw_damage_number(draw, col, row, cell_size, damage)


def _handle_death(
    draw: ImageDraw.ImageDraw,
    event: dict[str, Any],
    bot_positions: dict[str, tuple[int, int]],
    cell_size: int,
) -> None:
    """Process a death event: red X marker."""
    emoji = event.get("emoji", "")
    if emoji in bot_positions:
        col, row = bot_positions[emoji]
        _draw_death_marker(draw, col, row, cell_size)


def _handle_storm(
    draw: ImageDraw.ImageDraw,
    event: dict[str, Any],
    bot_positions: dict[str, tuple[int, int]],
    cell_size: int,
) -> None:
    """Process a storm_damage event: flash + damage number."""
    emoji = event.get("emoji", "")
    damage = event.get("damage", 0)
    if emoji in bot_positions:
        col, row = bot_positions[emoji]
        _draw_hit_flash(draw, col, row, cell_size)
        if damage > 0:
            _draw_damage_number(draw, col, row, cell_size, damage)
