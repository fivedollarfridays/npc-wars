"""Render combat effects (hit flash, death marker, damage numbers) on a grid frame."""

from PIL import Image, ImageDraw
from typing import Any

from video.colors import _FONT

HIT_FLASH_OUTLINE = (255, 255, 180)     # pale yellow outline for hit/storm flash
DEATH_COLOR = (255, 50, 50)             # bright red X
DAMAGE_COLOR = (255, 220, 50)           # yellow damage text


def _cell_rect(col: int, row: int, cell_size: int) -> tuple[int, int, int, int]:
    """Return (x0, y0, x1, y1) for a cell."""
    x0 = col * cell_size
    y0 = row * cell_size
    return x0, y0, x0 + cell_size - 1, y0 + cell_size - 1


def _draw_hit_flash(
    draw: ImageDraw.ImageDraw, col: int, row: int, cell_size: int,
) -> None:
    """Draw a bright outline on the hit cell."""
    x0, y0, x1, y1 = _cell_rect(col, row, cell_size)
    draw.rectangle([x0 + 2, y0 + 2, x1 - 2, y1 - 2], outline=HIT_FLASH_OUTLINE, width=2)


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


def _handle_flash_and_damage(
    draw: ImageDraw.ImageDraw,
    identifier: str,
    damage: int,
    bot_positions: dict[str, tuple[int, int]],
    cell_size: int,
) -> None:
    """Draw hit flash + optional damage number at the bot's cell."""
    if identifier in bot_positions:
        col, row = bot_positions[identifier]
        _draw_hit_flash(draw, col, row, cell_size)
        if damage > 0:
            _draw_damage_number(draw, col, row, cell_size, damage)


def _handle_attack(
    draw: ImageDraw.ImageDraw,
    event: dict[str, Any],
    bot_positions: dict[str, tuple[int, int]],
    cell_size: int,
) -> None:
    """Process an attack event: hit flash + damage number on target."""
    _handle_flash_and_damage(
        draw, event.get("target", ""), event.get("damage", 0), bot_positions, cell_size,
    )


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
    """Process a storm_damage event: hit flash + damage number."""
    _handle_flash_and_damage(
        draw, event.get("emoji", ""), event.get("damage", 0), bot_positions, cell_size,
    )
