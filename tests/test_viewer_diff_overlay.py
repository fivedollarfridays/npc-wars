"""Tests for the diff overlay HTML component in viewer."""

import pytest

from conftest import read_viewer_content


@pytest.fixture(scope="module")
def html_content() -> str:
    """Load all viewer files (index.html + js/*.js) once for all tests."""
    return read_viewer_content()


class TestDiffOverlayCSS:
    """Verify diff overlay CSS classes exist."""

    def test_diff_overlay_class(self, html_content: str) -> None:
        assert ".diff-overlay " in html_content or ".diff-overlay{" in html_content

    def test_diff_overlay_visible_class(self, html_content: str) -> None:
        assert ".diff-overlay.visible" in html_content

    def test_diff_title_class(self, html_content: str) -> None:
        assert ".diff-title" in html_content

    def test_diff_table_class(self, html_content: str) -> None:
        assert ".diff-table " in html_content or ".diff-table{" in html_content

    def test_diff_continue_class(self, html_content: str) -> None:
        assert ".diff-continue" in html_content

    def test_overlay_height_40vh(self, html_content: str) -> None:
        assert "40vh" in html_content

    def test_overlay_slide_transform(self, html_content: str) -> None:
        assert "translateY(100%)" in html_content


class TestDiffOverlayHTML:
    """Verify diff overlay HTML elements exist."""

    def test_diff_overlay_element(self, html_content: str) -> None:
        assert 'id="diff-overlay"' in html_content

    def test_diff_table_element(self, html_content: str) -> None:
        assert 'id="diff-table"' in html_content

    def test_diff_tbody_element(self, html_content: str) -> None:
        assert 'id="diff-tbody"' in html_content

    def test_continue_button(self, html_content: str) -> None:
        assert "dismissDiff()" in html_content

    def test_match_stats_title(self, html_content: str) -> None:
        assert "MATCH STATS" in html_content

    def test_table_headers(self, html_content: str) -> None:
        assert "<th>Stat</th>" in html_content
        assert "<th>Lifetime Avg</th>" in html_content
        assert "<th>This Match</th>" in html_content
        assert "<th>Delta</th>" in html_content


class TestDiffOverlayJavaScript:
    """Verify diff overlay JS functions exist."""

    def test_show_diff_overlay_function(self, html_content: str) -> None:
        assert "function showDiffOverlay()" in html_content

    def test_dismiss_diff_function(self, html_content: str) -> None:
        assert "function dismissDiff()" in html_content

    def test_reads_match_data_diff(self, html_content: str) -> None:
        assert "matchData.diff" in html_content

    def test_sanitize_used_for_stat_names(self, html_content: str) -> None:
        assert "sanitize(statName)" in html_content

    def test_show_winner_calls_show_diff(self, html_content: str) -> None:
        assert "showDiffOverlay()" in html_content
        # Verify it's called within or after showWinner
        winner_idx = html_content.index("function showWinner()")
        diff_call_idx = html_content.index(
            "showDiffOverlay()", winner_idx
        )
        # The call should be reasonably close (within ~500 chars)
        assert diff_call_idx - winner_idx < 500


class TestFirstMatchDisplay:
    """Verify first-match handling in the diff overlay."""

    def test_first_match_banner_text(self, html_content: str) -> None:
        """The JS must render 'FIRST MATCH!' text for first-match players."""
        assert "FIRST MATCH!" in html_content

    def test_first_match_checks_flag(self, html_content: str) -> None:
        """JS checks playerDiff.first_match to detect first-match players."""
        assert "playerDiff.first_match" in html_content

    def test_first_match_renders_stat_rows(self, html_content: str) -> None:
        """First-match branch must iterate over stats to show current values.

        The block between 'if (playerDiff.first_match)' and the next closing
        brace should contain a for loop that renders stat rows, NOT just
        'continue' to skip them entirely.
        """
        fm_idx = html_content.index("if (playerDiff.first_match)")
        # Extract the first-match block (up to ~1200 chars should cover it)
        fm_block = html_content[fm_idx:fm_idx + 1200]
        # Must contain a loop over entries to render stat rows
        assert "Object.entries" in fm_block
        # Must reference .current to display the current value
        assert ".current" in fm_block

    def test_first_match_no_delta_arrows(self, html_content: str) -> None:
        """First-match stat rows show dash for delta (no numeric delta)."""
        fm_idx = html_content.index("if (playerDiff.first_match)")
        fm_block = html_content[fm_idx:fm_idx + 1200]
        # Should use em-dash (escaped as \\u2014 in JS source) for missing delta/lifetime
        assert "\\u2014" in fm_block
