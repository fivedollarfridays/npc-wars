"""Tests for video.video_grid — grid rendering with storm overlay."""

from PIL import Image

from video.video_grid import render_grid


class TestRenderGridBasics:
    """Basic rendering behavior."""

    def test_render_grid_returns_image(self) -> None:
        """render_grid returns a PIL.Image.Image."""
        result = render_grid(grid_size=10, storm_border=0)
        assert isinstance(result, Image.Image)

    def test_render_grid_correct_dimensions(self) -> None:
        """Image dimensions match grid_size * cell_size."""
        img = render_grid(grid_size=10, storm_border=0, cell_size=48)
        assert img.size == (480, 480)

    def test_render_grid_default_cell_size(self) -> None:
        """Default cell_size=48, 10x10 grid = 480x480."""
        img = render_grid(grid_size=10, storm_border=0)
        assert img.size == (480, 480)

    def test_render_grid_custom_cell_size(self) -> None:
        """cell_size=32, 8x8 grid = 256x256."""
        img = render_grid(grid_size=8, storm_border=0, cell_size=32)
        assert img.size == (256, 256)


class TestRenderGridStorm:
    """Storm overlay coloring."""

    def test_render_grid_storm_tiles_are_red(self) -> None:
        """With storm_border=2, corner pixel has red channel > green channel."""
        img = render_grid(grid_size=10, storm_border=2, cell_size=48)
        # Top-left corner is storm tile (row=0, col=0)
        # Sample pixel inside the cell (avoid border pixels)
        px = img.getpixel((5, 5))
        assert px[0] > px[1], f"Expected red > green in storm tile, got {px}"

    def test_render_grid_safe_tiles_not_red(self) -> None:
        """Center pixel of safe zone does not have red > green by large margin."""
        img = render_grid(grid_size=10, storm_border=2, cell_size=48)
        # Center tile (row=5, col=5) is safe
        cx = 5 * 48 + 24
        cy = 5 * 48 + 24
        px = img.getpixel((cx, cy))
        # Safe tile: red should NOT dominate green by a large margin
        assert px[0] <= px[1] + 10, f"Expected safe tile not red-dominated, got {px}"

    def test_render_grid_no_storm(self) -> None:
        """storm_border=0: entire grid is safe, no red-dominated pixels in center."""
        img = render_grid(grid_size=10, storm_border=0, cell_size=48)
        # Check center pixel
        cx = 5 * 48 + 24
        cy = 5 * 48 + 24
        px = img.getpixel((cx, cy))
        assert px[0] <= px[1] + 10, f"Expected no red dominance, got {px}"
        # Check corner pixel too
        px_corner = img.getpixel((5, 5))
        assert px_corner[0] <= px_corner[1] + 10, f"Corner should be safe, got {px_corner}"

    def test_render_grid_full_storm(self) -> None:
        """storm_border >= grid_size//2: entire grid covered in storm."""
        img = render_grid(grid_size=10, storm_border=5, cell_size=48)
        # Center tile (row=5, col=5): distance from edge = min(5, 4) = 4 < 5 => storm
        cx = 5 * 48 + 24
        cy = 5 * 48 + 24
        px = img.getpixel((cx, cy))
        assert px[0] > px[1], f"Expected storm in center with full storm, got {px}"
        # Corner too
        px_corner = img.getpixel((5, 5))
        assert px_corner[0] > px_corner[1], f"Expected storm in corner, got {px_corner}"
