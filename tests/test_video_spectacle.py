"""Tests for render_spectacle_effects in video/video_effects.py."""

import numpy as np
from PIL import Image

IMG_SIZE = (200, 200)
BG_COLOR = (30, 35, 40)


def _make_image() -> Image.Image:
    """Create a small baseline image for testing."""
    return Image.new("RGB", IMG_SIZE, BG_COLOR)


def _avg_red(img: Image.Image) -> float:
    """Return the average red channel value across all pixels."""
    arr = np.array(img)
    return float(arr[:, :, 0].mean())


# ---------------------------------------------------------------------------
# 1. Calm tier returns image unchanged
# ---------------------------------------------------------------------------


def test_calm_tier_unchanged() -> None:
    """render_spectacle_effects with calm tier returns image with same pixels."""
    from video.video_effects import render_spectacle_effects

    img = _make_image()
    baseline = img.tobytes()

    spectacle = {"drama_score": 10, "tier": "calm", "triggers": [], "effects": []}
    result, slow_mo = render_spectacle_effects(img, spectacle, round_num=1)

    assert result.tobytes() == baseline
    assert slow_mo is False


# ---------------------------------------------------------------------------
# 2. Screen shake shifts image pixels
# ---------------------------------------------------------------------------


def test_screen_shake_shifts_pixels() -> None:
    """Intense tier with kill trigger shifts image pixels (not identical to original)."""
    from video.video_effects import render_spectacle_effects

    img = _make_image()
    # Draw something non-uniform so a shift is detectable
    from PIL import ImageDraw

    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 50, 100, 100], fill=(255, 255, 255))

    baseline = img.tobytes()
    spectacle = {
        "drama_score": 70,
        "tier": "intense",
        "triggers": ["kill"],
        "effects": [],
    }
    result, _ = render_spectacle_effects(img, spectacle, round_num=3)

    assert result.tobytes() != baseline, "Screen shake should shift pixels"


# ---------------------------------------------------------------------------
# 3. Fire border adds colored pixels along edges
# ---------------------------------------------------------------------------


def test_fire_border_adds_edge_pixels() -> None:
    """Hype tier adds colored pixels along the frame edges."""
    from video.video_effects import render_spectacle_effects

    img = _make_image()
    baseline_edges = _edge_pixels(img)

    spectacle = {
        "drama_score": 90,
        "tier": "hype",
        "triggers": [],
        "effects": [],
    }
    result, _ = render_spectacle_effects(img, spectacle, round_num=1)

    after_edges = _edge_pixels(result)
    assert after_edges != baseline_edges, "Fire border should change edge pixels"


def _edge_pixels(img: Image.Image) -> list[tuple[int, ...]]:
    """Collect pixels along the top and left edges."""
    w, h = img.size
    pixels = []
    for x in range(w):
        pixels.append(img.getpixel((x, 0)))
    for y in range(h):
        pixels.append(img.getpixel((0, y)))
    return pixels


# ---------------------------------------------------------------------------
# 4. Damage flash increases red channel average
# ---------------------------------------------------------------------------


def test_damage_flash_increases_red() -> None:
    """Red overlay should increase the average red channel value."""
    from video.video_effects import render_spectacle_effects

    img = _make_image()
    baseline_red = _avg_red(img)

    spectacle = {
        "drama_score": 50,
        "tier": "heating",
        "triggers": [],
        "effects": [],
    }
    result, _ = render_spectacle_effects(img, spectacle, round_num=1)

    assert _avg_red(result) > baseline_red, "Damage flash should increase red average"


# ---------------------------------------------------------------------------
# 5. Effect intensity scales: heating has lower opacity than chaos
# ---------------------------------------------------------------------------


def test_intensity_scales_with_tier() -> None:
    """Chaos tier produces a higher red average than heating tier."""
    from video.video_effects import render_spectacle_effects

    img_heating = _make_image()
    spectacle_heating = {"drama_score": 40, "tier": "heating", "triggers": [], "effects": []}
    result_heating, _ = render_spectacle_effects(img_heating, spectacle_heating, round_num=1)

    img_chaos = _make_image()
    spectacle_chaos = {"drama_score": 100, "tier": "chaos", "triggers": [], "effects": []}
    result_chaos, _ = render_spectacle_effects(img_chaos, spectacle_chaos, round_num=1)

    assert _avg_red(result_chaos) > _avg_red(result_heating), (
        "Chaos tier should have stronger red flash than heating"
    )


# ---------------------------------------------------------------------------
# 6. No spectacle data (None) returns image unchanged
# ---------------------------------------------------------------------------


def test_none_spectacle_unchanged() -> None:
    """render_spectacle_effects with None spectacle returns image unchanged."""
    from video.video_effects import render_spectacle_effects

    img = _make_image()
    baseline = img.tobytes()

    result, slow_mo = render_spectacle_effects(img, None, round_num=1)

    assert result.tobytes() == baseline
    assert slow_mo is False


# ---------------------------------------------------------------------------
# 7. Slow-mo flag when near_death in triggers
# ---------------------------------------------------------------------------


def test_slow_mo_flag_near_death() -> None:
    """Returns slow_mo=True when near_death is in triggers."""
    from video.video_effects import render_spectacle_effects

    img = _make_image()
    spectacle = {
        "drama_score": 80,
        "tier": "intense",
        "triggers": ["near_death", "kill"],
        "effects": [],
    }
    _, slow_mo = render_spectacle_effects(img, spectacle, round_num=1)

    assert slow_mo is True


def test_no_slow_mo_without_near_death() -> None:
    """Returns slow_mo=False when near_death is NOT in triggers."""
    from video.video_effects import render_spectacle_effects

    img = _make_image()
    spectacle = {
        "drama_score": 80,
        "tier": "intense",
        "triggers": ["kill"],
        "effects": [],
    }
    _, slow_mo = render_spectacle_effects(img, spectacle, round_num=1)

    assert slow_mo is False
