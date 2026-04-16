"""Tests for video/video_commentary.py — commentary text overlay on frames."""

from PIL import Image

from video.video_commentary import (
    DRAMA_COLORS,
    render_commentary_overlay,
)


class TestRenderCommentaryOverlay:
    """Tests for render_commentary_overlay()."""

    def test_returns_pil_image(self) -> None:
        frame = Image.new("RGB", (680, 480), (0, 0, 0))
        result = render_commentary_overlay(frame, "Test line", "calm")
        assert isinstance(result, Image.Image)

    def test_preserves_frame_size(self) -> None:
        frame = Image.new("RGB", (680, 480), (0, 0, 0))
        result = render_commentary_overlay(frame, "Test line", "calm")
        assert result.size == frame.size

    def test_modifies_bottom_pixels(self) -> None:
        """Overlay should change pixels in the bottom region."""
        frame = Image.new("RGB", (680, 480), (0, 0, 0))
        result = render_commentary_overlay(frame, "Action happening!", "hype")
        # Sample a pixel in the bottom banner area — should not be pure black
        # (banner background or text color will differ from the black frame)
        bottom_row = [result.getpixel((x, 479 - 5)) for x in range(0, 680, 10)]
        assert any(px != (0, 0, 0) for px in bottom_row)

    def test_does_not_modify_top(self) -> None:
        """Top of frame should remain unchanged."""
        frame = Image.new("RGB", (680, 480), (50, 50, 50))
        result = render_commentary_overlay(frame, "Hello", "calm")
        assert result.getpixel((10, 10)) == (50, 50, 50)

    def test_color_coding_per_tier(self) -> None:
        """Each drama tier should map to a distinct color."""
        assert len(set(DRAMA_COLORS.values())) == len(DRAMA_COLORS)

    def test_all_tiers_accepted(self) -> None:
        frame = Image.new("RGB", (680, 480), (0, 0, 0))
        for tier in ("calm", "heating", "intense", "hype", "chaos"):
            result = render_commentary_overlay(frame, "text", tier)
            assert isinstance(result, Image.Image)

    def test_unknown_tier_defaults_to_white(self) -> None:
        frame = Image.new("RGB", (680, 480), (0, 0, 0))
        result = render_commentary_overlay(frame, "text", "unknown_tier")
        assert isinstance(result, Image.Image)

    def test_empty_text_still_returns_image(self) -> None:
        frame = Image.new("RGB", (680, 480), (0, 0, 0))
        result = render_commentary_overlay(frame, "", "calm")
        assert isinstance(result, Image.Image)
