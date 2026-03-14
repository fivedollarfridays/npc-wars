"""Render combat effects (hit flash, death marker, damage numbers) on a grid frame."""

from __future__ import annotations

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


# ---------------------------------------------------------------------------
# Spectacle visual effects (drama-tier driven)
# ---------------------------------------------------------------------------

_TIER_OPACITY: dict[str, int] = {
    "heating": 25,
    "intense": 50,
    "hype": 100,
    "chaos": 150,
}

_SHAKE_TIERS = frozenset(("intense", "hype", "chaos"))
_FIRE_TIERS = frozenset(("hype", "chaos"))
_SHAKE_TRIGGERS = frozenset(("kill", "kill_streak"))


def render_spectacle_effects(
    image: Image.Image,
    spectacle: dict[str, Any] | None,
    round_num: int = 0,
) -> tuple[Image.Image, bool]:
    """Apply spectacle visual effects based on drama tier.

    Returns (modified_image, slow_mo_flag).
    slow_mo_flag is True when near_death is in triggers.
    """
    if spectacle is None:
        return image, False

    tier: str = spectacle.get("tier", "calm")
    triggers: list[str] = spectacle.get("triggers", [])

    if tier == "calm":
        return image, False

    result = image.copy()

    if tier in _SHAKE_TIERS and _SHAKE_TRIGGERS & set(triggers):
        result = _apply_screen_shake(result, round_num)

    if tier in _FIRE_TIERS:
        result = _apply_fire_border(result)

    opacity = _TIER_OPACITY.get(tier, 0)
    if opacity > 0:
        result = _apply_damage_flash(result, opacity)

    slow_mo = "near_death" in triggers
    return result, slow_mo


def _apply_screen_shake(image: Image.Image, round_num: int) -> Image.Image:
    """Offset image by a few pixels, fill exposed edge with black."""
    dx = ((round_num * 7 + 3) % 5) - 2  # -2 to +2
    dy = ((round_num * 11 + 5) % 5) - 2
    shifted = Image.new("RGB", image.size, (0, 0, 0))
    shifted.paste(image, (dx, dy))
    return shifted


def _apply_fire_border(image: Image.Image) -> Image.Image:
    """Draw orange/red gradient rectangles along frame edges."""
    draw = ImageDraw.Draw(image)
    w, h = image.size
    border_w = max(4, w // 20)
    for i in range(border_w):
        c = (255, 80 + i * 3, 0)
        draw.rectangle([i, i, w - 1 - i, h - 1 - i], outline=c)
    return image


def _apply_damage_flash(image: Image.Image, opacity: int) -> Image.Image:
    """Composite semi-transparent red overlay."""
    overlay = Image.new("RGBA", image.size, (255, 0, 0, opacity))
    rgba = image.convert("RGBA") if image.mode != "RGBA" else image
    result = Image.alpha_composite(rgba, overlay)
    return result.convert("RGB")
