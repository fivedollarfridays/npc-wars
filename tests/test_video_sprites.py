"""Tests for video.video_sprites -- bot sprite rendering with HP bars and labels."""

from PIL import Image

from video.video_sprites import render_bots

CELL_SIZE = 48
GRID_CELLS = 2


def _make_image() -> Image.Image:
    """Create a small 2x2 grid image for testing."""
    size = GRID_CELLS * CELL_SIZE
    return Image.new("RGB", (size, size), (30, 35, 40))


def _bot(
    name: str = "TestBot",
    emoji: str = "\U0001f916",
    x: int = 0,
    y: int = 0,
    hp: int = 100,
    energy: int = 80,
) -> dict:
    return {"name": name, "emoji": emoji, "x": x, "y": y, "hp": hp, "energy": energy}


class TestRenderBotsBasic:
    """Basic render_bots behavior."""

    def test_render_bots_returns_image(self) -> None:
        """render_bots() returns a PIL.Image."""
        img = _make_image()
        result = render_bots(img, [_bot()], cell_size=CELL_SIZE)
        assert isinstance(result, Image.Image)

    def test_render_bots_modifies_image_in_place(self) -> None:
        """render_bots() returns the same image object (in-place modification)."""
        img = _make_image()
        result = render_bots(img, [_bot()], cell_size=CELL_SIZE)
        assert result is img

    def test_bot_position_draws_in_correct_cell(self) -> None:
        """Bot at (col=0, row=0) draws pixels in top-left cell only."""
        img = _make_image()
        # Record a pixel in the bottom-right cell before rendering
        px_before = img.getpixel((1 * CELL_SIZE + 24, 1 * CELL_SIZE + 24))
        render_bots(img, [_bot(x=0, y=0)], cell_size=CELL_SIZE)
        # Top-left cell center should have changed
        # Bottom-right cell should be unchanged (no bot there)
        px_bottom_right = img.getpixel((1 * CELL_SIZE + 24, 1 * CELL_SIZE + 24))
        assert px_bottom_right == px_before
        # top-left cell HP bar should have been drawn
        px_hp_bar = img.getpixel((4, 42))
        bg = (30, 35, 40)
        assert px_hp_bar != bg, f"Top-left cell should have HP bar, got {px_hp_bar}"


class TestHPBar:
    """HP bar color tests."""

    def test_hp_bar_full_health_is_green(self) -> None:
        """hp=100: HP bar pixel is green-dominant."""
        img = _make_image()
        render_bots(img, [_bot(hp=100)], cell_size=CELL_SIZE)
        # HP bar is at bottom of cell: y0 + cell_size - bar_h - 2
        # bar_h = max(4, 48//12) = 4, so bar_y = 0 + 48 - 4 - 2 = 42
        # Sample a pixel inside the bar: x=4, y=42
        px = img.getpixel((4, 42))
        assert px[1] > px[0], f"Expected green > red for full HP, got {px}"

    def test_hp_bar_low_health_is_red(self) -> None:
        """hp=20: HP bar pixel is red-dominant."""
        img = _make_image()
        render_bots(img, [_bot(hp=20)], cell_size=CELL_SIZE)
        # fill_w = int(44 * 20 / 100) = 8, so bar fills x=2..10
        px = img.getpixel((4, 42))
        assert px[0] > px[1], f"Expected red > green for low HP, got {px}"

    def test_hp_bar_mid_health_is_yellow(self) -> None:
        """hp=50: HP bar pixel has r>0 and g>0 (yellow range)."""
        img = _make_image()
        render_bots(img, [_bot(hp=50)], cell_size=CELL_SIZE)
        px = img.getpixel((4, 42))
        assert px[0] > 50, f"Expected red > 50 for mid HP, got {px}"
        assert px[1] > 50, f"Expected green > 50 for mid HP, got {px}"


class TestDeadBot:
    """Dead bot rendering."""

    def test_dead_bot_renders_differently(self) -> None:
        """Bot with hp=0 renders differently than hp=100."""
        img_alive = _make_image()
        render_bots(img_alive, [_bot(hp=100)], cell_size=CELL_SIZE)

        img_dead = _make_image()
        render_bots(img_dead, [_bot(hp=0)], cell_size=CELL_SIZE)

        # Sample several pixels in cell center -- they should differ
        alive_px = img_alive.getpixel((24, 24))
        dead_px = img_dead.getpixel((24, 24))
        assert alive_px != dead_px, (
            f"Dead and alive bots should render differently at cell center, "
            f"alive={alive_px}, dead={dead_px}"
        )


class TestMultipleBots:
    """Multiple bots rendering."""

    def test_render_bots_multiple(self) -> None:
        """Two bots at different positions both render without error."""
        img = _make_image()
        bots = [_bot(x=0, y=0, hp=100), _bot(name="Bot2", x=1, y=1, hp=50)]
        result = render_bots(img, bots, cell_size=CELL_SIZE)
        assert isinstance(result, Image.Image)
        # Both cells should have been modified from bg color
        # Check HP bar area in each cell
        px_00 = img.getpixel((4, 42))          # cell (0,0) HP bar
        px_11 = img.getpixel((1 * CELL_SIZE + 4, 1 * CELL_SIZE + 42))  # cell (1,1) HP bar
        bg = (30, 35, 40)
        assert px_00 != bg, f"Cell (0,0) should have HP bar, got {px_00}"
        assert px_11 != bg, f"Cell (1,1) should have HP bar, got {px_11}"
