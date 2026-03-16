"""Tests for viewer layout — maximize battlefield (T15.7)."""

from __future__ import annotations

import re
from pathlib import Path

MATCH_HTML = Path(__file__).resolve().parent.parent / "viewer" / "match.html"


def _read_html() -> str:
    return MATCH_HTML.read_text()


def _extract_css(html: str) -> str:
    """Return the contents of all <style> blocks concatenated."""
    blocks = re.findall(r"<style[^>]*>(.*?)</style>", html, re.DOTALL)
    return "\n".join(blocks)


# --- Arena / Main layout ---


def test_main_max_width_is_100_percent() -> None:
    """Main container should use max-width: 100%, not a fixed pixel cap."""
    css = _extract_css(_read_html())
    main_block = re.search(r"\.main\s*\{([^}]+)\}", css)
    assert main_block, ".main CSS rule not found"
    assert "max-width: 100%" in main_block.group(1) or "max-width:100%" in main_block.group(1)


def test_arena_wrap_flex_grow() -> None:
    """Arena-wrap should grow to fill available space (flex: 1 or flex-grow)."""
    css = _extract_css(_read_html())
    arena_block = re.search(r"\.arena-wrap\s*\{([^}]+)\}", css)
    assert arena_block, ".arena-wrap CSS rule not found"
    body = arena_block.group(1)
    has_flex = "flex: 1" in body or "flex-grow" in body
    assert has_flex, f".arena-wrap should have flex: 1 or flex-grow, got: {body}"


# --- Sidebar ---


def test_sidebar_max_width_250() -> None:
    """Sidebar max-width should be 250px (compact)."""
    css = _extract_css(_read_html())
    sidebar_block = re.search(r"\.sidebar\s*\{([^}]+)\}", css)
    assert sidebar_block, ".sidebar CSS rule not found"
    body = sidebar_block.group(1)
    assert "max-width: 250px" in body or "max-width:250px" in body


def test_sidebar_flex_shrink_zero() -> None:
    """Sidebar should not shrink (flex-shrink: 0)."""
    css = _extract_css(_read_html())
    sidebar_block = re.search(r"\.sidebar\s*\{([^}]+)\}", css)
    assert sidebar_block, ".sidebar CSS rule not found"
    body = sidebar_block.group(1)
    assert "flex-shrink: 0" in body or "flex-shrink:0" in body


# --- Media query ---


def test_media_query_1024_exists() -> None:
    """A media query for min-width: 1024px should exist."""
    css = _extract_css(_read_html())
    assert re.search(r"@media\s*\(\s*min-width\s*:\s*1024px\s*\)", css)


def test_media_query_arena_70_percent() -> None:
    """Media query should ensure arena gets >= 70% width."""
    css = _extract_css(_read_html())
    mq = re.search(
        r"@media\s*\(\s*min-width\s*:\s*1024px\s*\)\s*\{(.*?)\n\s*\}",
        css,
        re.DOTALL,
    )
    assert mq, "1024px media query not found"
    body = mq.group(1)
    assert "70%" in body or "min-width" in body


# --- Scrollable containers ---


def test_kill_feed_overflow_auto() -> None:
    """Kill feed should have overflow-y: auto."""
    css = _extract_css(_read_html())
    kf_block = re.search(r"\.kill-feed\s*\{([^}]+)\}", css)
    assert kf_block, ".kill-feed CSS rule not found"
    assert "overflow-y: auto" in kf_block.group(1) or "overflow-y:auto" in kf_block.group(1)


def test_bot_list_overflow_auto() -> None:
    """Bot list panel (#bot-list) should have overflow-y: auto and max-height."""
    css = _extract_css(_read_html())
    bl_block = re.search(r"#bot-list\s*\{([^}]+)\}", css)
    assert bl_block, "#bot-list CSS rule not found"
    body = bl_block.group(1)
    assert "overflow-y: auto" in body or "overflow-y:auto" in body
    assert "max-height" in body
