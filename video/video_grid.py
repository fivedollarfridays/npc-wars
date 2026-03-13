"""Render the NPC Wars battle grid as a Pillow image."""

from PIL import Image, ImageDraw

from engine.grid import is_in_storm

# Color palette (dark theme)
COLOR_SAFE_BG = (30, 35, 40)        # dark blue-grey
COLOR_SAFE_LINE = (60, 70, 80)      # grid lines
COLOR_STORM_BG = (80, 20, 20)       # dark red — storm zone
COLOR_STORM_LINE = (120, 40, 40)    # storm grid lines
COLOR_BORDER = (200, 200, 200)      # outer border
BORDER_WIDTH = 2


def _draw_cells(
    draw: ImageDraw.ImageDraw,
    grid_size: int,
    storm_border: int,
    cell_size: int,
) -> None:
    """Draw cell backgrounds and grid lines for all tiles."""
    for row in range(grid_size):
        for col in range(grid_size):
            x0 = col * cell_size
            y0 = row * cell_size
            x1 = x0 + cell_size - 1
            y1 = y0 + cell_size - 1
            if is_in_storm(col, row, grid_size, storm_border):
                draw.rectangle(
                    [x0, y0, x1, y1], fill=COLOR_STORM_BG, outline=COLOR_STORM_LINE,
                )
            else:
                draw.rectangle([x0, y0, x1, y1], outline=COLOR_SAFE_LINE)


def render_grid(
    grid_size: int,
    storm_border: int,
    cell_size: int = 48,
) -> Image.Image:
    """Render the battle grid as a PIL Image.

    Args:
        grid_size: Number of cells per side.
        storm_border: Number of tile rows/cols consumed by storm from each edge.
        cell_size: Pixel size of each cell.

    Returns:
        PIL Image of size (grid_size * cell_size) x (grid_size * cell_size).
    """
    size = grid_size * cell_size
    img = Image.new("RGB", (size, size), COLOR_SAFE_BG)
    draw = ImageDraw.Draw(img)

    _draw_cells(draw, grid_size, storm_border, cell_size)

    # Draw outer border
    draw.rectangle(
        [0, 0, size - 1, size - 1],
        outline=COLOR_BORDER,
        width=BORDER_WIDTH,
    )

    return img
