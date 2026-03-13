"""Tests for video.video_overlay — scoreboard sidebar overlay."""

from PIL import Image

from video.video_overlay import SIDEBAR_BG, SIDEBAR_WIDTH, render_overlay

ROUND_DATA = {
    "round": 5,
    "bots": [
        {"name": "DuckBot", "emoji": "\U0001f986", "hp": 80},
        {"name": "GooseBot", "emoji": "\U0001fabf", "hp": 0},
    ],
    "kills": [
        {"killer": "\U0001f986", "victim": "\U0001fabf", "round": 4},
    ],
}


def _make_grid(width: int = 480, height: int = 480) -> Image.Image:
    """Create a dummy grid image filled with a known color."""
    return Image.new("RGB", (width, height), (30, 35, 40))


class TestOverlayDimensions:
    """Sidebar widens the frame without changing height."""

    def test_render_overlay_returns_wider_image(self) -> None:
        grid = _make_grid()
        result = render_overlay(grid, round_num=5, bots=[], kills=[])
        assert result.size[0] > grid.size[0]

    def test_render_overlay_correct_width(self) -> None:
        grid = _make_grid()
        result = render_overlay(grid, round_num=5, bots=[], kills=[])
        assert result.size[0] == grid.size[0] + SIDEBAR_WIDTH

    def test_render_overlay_same_height(self) -> None:
        grid = _make_grid()
        result = render_overlay(grid, round_num=5, bots=[], kills=[])
        assert result.size[1] == grid.size[1]


class TestOverlayContent:
    """Round counter, alive count, kill feed render non-background pixels."""

    def test_round_counter_renders(self) -> None:
        """Pixel area where round text should be is non-background."""
        grid = _make_grid()
        result = render_overlay(
            grid, round_num=5, bots=ROUND_DATA["bots"], kills=[]
        )
        # Round text is near the top of the sidebar (y ~8-26)
        sx = grid.size[0]
        has_text = False
        for x in range(sx + 4, sx + 100):
            for y in range(8, 26):
                if result.getpixel((x, y)) != SIDEBAR_BG:
                    has_text = True
                    break
            if has_text:
                break
        assert has_text, "Round counter text area should have non-background pixels"

    def test_alive_count_renders(self) -> None:
        """Alive bot count area has non-background pixels."""
        grid = _make_grid()
        result = render_overlay(
            grid, round_num=5, bots=ROUND_DATA["bots"], kills=[]
        )
        sx = grid.size[0]
        # Alive count is drawn just below round counter (y ~26-44)
        has_text = False
        for x in range(sx + 4, sx + 100):
            for y in range(26, 44):
                if result.getpixel((x, y)) != SIDEBAR_BG:
                    has_text = True
                    break
            if has_text:
                break
        assert has_text, "Alive count area should have non-background pixels"

    def test_kill_feed_renders(self) -> None:
        """Kill feed area has non-background pixels when kills exist."""
        grid = _make_grid()
        result = render_overlay(
            grid,
            round_num=5,
            bots=ROUND_DATA["bots"],
            kills=ROUND_DATA["kills"],
        )
        sx = grid.size[0]
        # Kill feed is in the lower portion of the sidebar
        # Scan a wide vertical band for any non-background pixel
        has_text = False
        for x in range(sx + 4, sx + SIDEBAR_WIDTH - 4):
            for y in range(100, grid.size[1]):
                if result.getpixel((x, y)) != SIDEBAR_BG:
                    has_text = True
                    break
            if has_text:
                break
        assert has_text, "Kill feed area should have non-background pixels"

    def test_kill_feed_empty(self) -> None:
        """Empty kills list renders without error."""
        grid = _make_grid()
        result = render_overlay(
            grid, round_num=1, bots=ROUND_DATA["bots"], kills=[]
        )
        assert result.size[0] == grid.size[0] + SIDEBAR_WIDTH


class TestOverlayPreservation:
    """Grid pixels are preserved in the composite frame."""

    def test_render_overlay_preserves_grid(self) -> None:
        """Left portion (grid) pixels unchanged."""
        grid = _make_grid()
        # Set a few known pixels
        grid.putpixel((10, 10), (255, 0, 0))
        grid.putpixel((100, 200), (0, 255, 0))
        result = render_overlay(
            grid, round_num=5, bots=ROUND_DATA["bots"], kills=[]
        )
        assert result.getpixel((10, 10)) == (255, 0, 0)
        assert result.getpixel((100, 200)) == (0, 255, 0)
