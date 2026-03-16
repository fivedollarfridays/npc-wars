"""Tests for diff color coding and delta formatting in viewer/match.html."""

import pathlib

import pytest

VIEWER_HTML = pathlib.Path(__file__).parent.parent / "viewer" / "match.html"


@pytest.fixture(scope="module")
def html_content() -> str:
    """Load viewer/match.html content once for all tests."""
    return VIEWER_HTML.read_text()


class TestDiffRowCSS:
    """Verify CSS classes for improved/regressed/neutral row backgrounds."""

    def test_diff_row_improved_exists(self, html_content: str) -> None:
        assert ".diff-row-improved" in html_content

    def test_diff_row_improved_background(self, html_content: str) -> None:
        idx = html_content.index(".diff-row-improved")
        block = html_content[idx : idx + 120]
        assert "#0d4d0d" in block

    def test_diff_row_regressed_exists(self, html_content: str) -> None:
        assert ".diff-row-regressed" in html_content

    def test_diff_row_regressed_background(self, html_content: str) -> None:
        idx = html_content.index(".diff-row-regressed")
        block = html_content[idx : idx + 120]
        assert "#4d0d0d" in block

    def test_diff_row_neutral_exists(self, html_content: str) -> None:
        assert ".diff-row-neutral" in html_content


class TestDiffDeltaCSS:
    """Verify CSS classes for delta value coloring."""

    def test_diff_delta_positive_exists(self, html_content: str) -> None:
        assert ".diff-delta-positive" in html_content

    def test_diff_delta_positive_uses_heal_color(self, html_content: str) -> None:
        idx = html_content.index(".diff-delta-positive")
        block = html_content[idx : idx + 120]
        assert "var(--heal)" in block

    def test_diff_delta_negative_exists(self, html_content: str) -> None:
        assert ".diff-delta-negative" in html_content

    def test_diff_delta_negative_uses_kill_color(self, html_content: str) -> None:
        idx = html_content.index(".diff-delta-negative")
        block = html_content[idx : idx + 120]
        assert "var(--kill)" in block

    def test_diff_delta_neutral_exists(self, html_content: str) -> None:
        assert ".diff-delta-neutral" in html_content

    def test_diff_delta_neutral_uses_muted_color(self, html_content: str) -> None:
        idx = html_content.index(".diff-delta-neutral")
        block = html_content[idx : idx + 120]
        assert "var(--muted)" in block


class TestDiffOverlaySortAndClassification:
    """Verify showDiffOverlay sorts by delta magnitude and applies classes."""

    def test_entries_sorted_by_abs_delta(self, html_content: str) -> None:
        fn_idx = html_content.index("function showDiffOverlay()")
        fn_block = html_content[fn_idx : fn_idx + 2500]
        assert ".sort(" in fn_block

    def test_sort_uses_abs_delta(self, html_content: str) -> None:
        fn_idx = html_content.index("function showDiffOverlay()")
        fn_block = html_content[fn_idx : fn_idx + 2500]
        assert "Math.abs" in fn_block

    def test_classification_applied_to_row(self, html_content: str) -> None:
        fn_idx = html_content.index("function showDiffOverlay()")
        fn_block = html_content[fn_idx : fn_idx + 2500]
        assert "diff-row-" in fn_block
        assert "classification" in fn_block

    def test_delta_class_applied(self, html_content: str) -> None:
        fn_idx = html_content.index("function showDiffOverlay()")
        fn_block = html_content[fn_idx : fn_idx + 2500]
        assert "diff-delta-positive" in fn_block
        assert "diff-delta-negative" in fn_block
        assert "diff-delta-neutral" in fn_block

    def test_percentage_formatting_with_toFixed(self, html_content: str) -> None:
        fn_idx = html_content.index("function showDiffOverlay()")
        fn_block = html_content[fn_idx : fn_idx + 2500]
        assert "toFixed(1)" in fn_block

    def test_signed_percentage_format(self, html_content: str) -> None:
        fn_idx = html_content.index("function showDiffOverlay()")
        fn_block = html_content[fn_idx : fn_idx + 3000]
        # Should format with + prefix for positive percentages
        assert "percentage" in fn_block
        assert "'+'" in fn_block or "'+" in fn_block or '"+' in fn_block or "'+'" in fn_block
