"""Tests for video/video_effects.py — combat effect overlays."""

from PIL import Image

CELL_SIZE = 48
GRID = 2  # 2x2 grid → 96×96 image
BG_COLOR = (30, 35, 40)


def _make_image() -> Image.Image:
    """Create a small baseline image for testing."""
    return Image.new("RGB", (GRID * CELL_SIZE, GRID * CELL_SIZE), BG_COLOR)


def _cell_pixels(img: Image.Image, col: int, row: int) -> list[tuple[int, ...]]:
    """Collect all pixel values within a cell."""
    pixels = []
    x0 = col * CELL_SIZE
    y0 = row * CELL_SIZE
    for y in range(y0, y0 + CELL_SIZE):
        for x in range(x0, x0 + CELL_SIZE):
            pixels.append(img.getpixel((x, y)))
    return pixels


def test_render_effects_returns_image() -> None:
    """render_effects returns a PIL Image."""
    from video.video_effects import render_effects

    img = _make_image()
    result = render_effects(img, [], {}, cell_size=CELL_SIZE)
    assert isinstance(result, Image.Image)


def test_hit_flash_brightens_cell() -> None:
    """Attack event draws something on the target cell."""
    from video.video_effects import render_effects

    img = _make_image()
    baseline = _cell_pixels(img, 0, 0)

    events = [{"type": "attack", "attacker": "A", "target": "B", "damage": 25}]
    positions = {"B": (0, 0)}
    render_effects(img, events, positions, cell_size=CELL_SIZE)

    after = _cell_pixels(img, 0, 0)
    assert after != baseline, "Hit flash should change pixels in target cell"


def test_death_marker_renders() -> None:
    """Death event draws something on the target cell."""
    from video.video_effects import render_effects

    img = _make_image()
    baseline = _cell_pixels(img, 1, 1)

    events = [{"type": "death", "emoji": "X", "killed_by": "A", "cause": "attack"}]
    positions = {"X": (1, 1)}
    render_effects(img, events, positions, cell_size=CELL_SIZE)

    after = _cell_pixels(img, 1, 1)
    assert after != baseline, "Death marker should change pixels in target cell"


def test_damage_number_renders() -> None:
    """Attack event with damage draws text in the cell area."""
    from video.video_effects import render_effects

    img = _make_image()
    baseline = _cell_pixels(img, 0, 1)

    events = [{"type": "attack", "attacker": "A", "target": "B", "damage": 25}]
    positions = {"B": (0, 1)}
    render_effects(img, events, positions, cell_size=CELL_SIZE)

    after = _cell_pixels(img, 0, 1)
    assert after != baseline, "Damage number should change pixels in target cell"


def test_no_events_unchanged() -> None:
    """Empty events list leaves the image unchanged."""
    from video.video_effects import render_effects

    img = _make_image()
    baseline = list(img.tobytes())

    render_effects(img, [], {}, cell_size=CELL_SIZE)

    after = list(img.tobytes())
    assert after == baseline, "No events should leave image unchanged"


def test_multiple_events_same_cell() -> None:
    """Two events on the same cell both render without error."""
    from video.video_effects import render_effects

    img = _make_image()
    baseline = _cell_pixels(img, 0, 0)

    events = [
        {"type": "attack", "attacker": "A", "target": "B", "damage": 10},
        {"type": "death", "emoji": "B", "killed_by": "A", "cause": "attack"},
    ]
    positions = {"B": (0, 0)}
    render_effects(img, events, positions, cell_size=CELL_SIZE)

    after = _cell_pixels(img, 0, 0)
    assert after != baseline, "Multiple events on same cell should change pixels"


def test_storm_damage_renders() -> None:
    """Storm damage event draws something on the affected cell."""
    from video.video_effects import render_effects

    img = _make_image()
    baseline = _cell_pixels(img, 1, 0)

    events = [{"type": "storm_damage", "emoji": "S", "damage": 10, "hp": 55}]
    positions = {"S": (1, 0)}
    render_effects(img, events, positions, cell_size=CELL_SIZE)

    after = _cell_pixels(img, 1, 0)
    assert after != baseline, "Storm damage should change pixels in affected cell"


def test_render_effects_modifies_in_place() -> None:
    """render_effects returns the same image object (modified in place)."""
    from video.video_effects import render_effects

    img = _make_image()
    result = render_effects(img, [], {}, cell_size=CELL_SIZE)
    assert result is img, "Should return the same image object"
