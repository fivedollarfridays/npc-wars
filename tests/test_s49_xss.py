"""Tests for XSS sanitization across HTML pages (T49.2).

Verifies that all HTML pages with innerHTML usage sanitize user-controlled
fields to prevent stored XSS attacks.
"""

import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# HTML files that use innerHTML with user-controlled data
SANITIZE_REQUIRED = [
    "server/static/tournaments.html",
    "server/static/leaderboard.html",
    "server/static/profile.html",
]


def _read_html(relpath: str) -> str:
    """Read an HTML file and return its content."""
    return (PROJECT_ROOT / relpath).read_text()


def _extract_script(html: str) -> str:
    """Extract all <script> block contents from HTML."""
    blocks = re.findall(r"<script[^>]*>(.*?)</script>", html, re.DOTALL)
    return "\n".join(blocks)


class TestSanitizeFunctionPresent:
    """Each vulnerable HTML file must contain a sanitize() function."""

    @pytest.mark.parametrize("path", SANITIZE_REQUIRED)
    def test_sanitize_function_exists(self, path: str) -> None:
        script = _extract_script(_read_html(path))
        assert "function sanitize" in script, (
            f"{path} is missing the sanitize() helper function"
        )

    @pytest.mark.parametrize("path", SANITIZE_REQUIRED)
    def test_sanitize_uses_textcontent(self, path: str) -> None:
        """Sanitize must use the textContent/innerHTML pattern."""
        script = _extract_script(_read_html(path))
        assert "textContent" in script and "innerHTML" in script, (
            f"{path} sanitize() must use the textContent->innerHTML pattern"
        )


class TestTournamentsXSS:
    """tournaments.html must sanitize t.name and t.winner."""

    def setup_method(self) -> None:
        self.script = _extract_script(
            _read_html("server/static/tournaments.html")
        )

    def test_name_is_sanitized(self) -> None:
        assert "sanitize(t.name)" in self.script, (
            "t.name must be wrapped in sanitize()"
        )

    def test_winner_is_sanitized(self) -> None:
        assert "sanitize(t.winner)" in self.script, (
            "t.winner must be wrapped in sanitize()"
        )


class TestLeaderboardXSS:
    """leaderboard.html must sanitize p.emoji."""

    def setup_method(self) -> None:
        self.script = _extract_script(
            _read_html("server/static/leaderboard.html")
        )

    def test_emoji_is_sanitized(self) -> None:
        assert "sanitize(p.emoji)" in self.script, (
            "p.emoji must be wrapped in sanitize()"
        )


class TestProfileXSS:
    """profile.html must sanitize m.winner."""

    def setup_method(self) -> None:
        self.script = _extract_script(
            _read_html("server/static/profile.html")
        )

    def test_winner_is_sanitized(self) -> None:
        assert "sanitize(m.winner)" in self.script, (
            "m.winner must be wrapped in sanitize()"
        )


class TestNoRawUserDataInInnerHTML:
    """Verify no innerHTML assignment contains raw user fields."""

    def test_tournaments_no_raw_tname(self) -> None:
        script = _extract_script(
            _read_html("server/static/tournaments.html")
        )
        # Find innerHTML assignments containing t.name without sanitize
        # Pattern: string concat with t.name NOT wrapped in sanitize()
        inner_blocks = re.findall(
            r"\.innerHTML\s*=.*?;", script, re.DOTALL
        )
        combined = " ".join(inner_blocks)
        # t.name should only appear inside sanitize()
        raw_refs = re.findall(r"(?<!sanitize\()t\.name", combined)
        assert not raw_refs, (
            "Found raw t.name in innerHTML without sanitize()"
        )

    def test_tournaments_no_raw_twinner(self) -> None:
        script = _extract_script(
            _read_html("server/static/tournaments.html")
        )
        inner_blocks = re.findall(
            r"\.innerHTML\s*=.*?;", script, re.DOTALL
        )
        combined = " ".join(inner_blocks)
        # Match t.winner used in string concat (+ t.winner) but not in
        # conditionals (t.winner ?) or inside sanitize()
        raw_refs = re.findall(
            r"\+\s*t\.winner(?!\s*[?:=])", combined
        )
        assert not raw_refs, (
            "Found raw t.winner in innerHTML string concatenation"
        )

    def test_leaderboard_no_raw_emoji(self) -> None:
        script = _extract_script(
            _read_html("server/static/leaderboard.html")
        )
        inner_blocks = re.findall(
            r"\.innerHTML\s*=.*?;", script, re.DOTALL
        )
        combined = " ".join(inner_blocks)
        raw_refs = re.findall(r"(?<!sanitize\()p\.emoji", combined)
        assert not raw_refs, (
            "Found raw p.emoji in innerHTML without sanitize()"
        )

    def test_profile_no_raw_winner(self) -> None:
        script = _extract_script(
            _read_html("server/static/profile.html")
        )
        inner_blocks = re.findall(
            r"\.innerHTML\s*=.*?;", script, re.DOTALL
        )
        combined = " ".join(inner_blocks)
        # Match m.winner used in string concat (+ m.winner) but not in
        # conditionals (m.winner ===) or inside sanitize()
        raw_refs = re.findall(
            r"\+\s*m\.winner(?!\s*[?:=])", combined
        )
        assert not raw_refs, (
            "Found raw m.winner in innerHTML string concatenation"
        )


class TestSanitizeHandlesNullish:
    """The sanitize function must handle null/undefined gracefully."""

    @pytest.mark.parametrize("path", SANITIZE_REQUIRED)
    def test_sanitize_has_null_guard(self, path: str) -> None:
        script = _extract_script(_read_html(path))
        # Function should coerce falsy values to empty string
        func_match = re.search(
            r"function sanitize\(.*?\)\s*\{(.*?)\}",
            script,
            re.DOTALL,
        )
        assert func_match, f"Could not find sanitize function body in {path}"
        body = func_match.group(1)
        # Must have a fallback for null/undefined — either || '' or ternary
        assert "|| ''" in body or "|| \"\"" in body, (
            f"{path} sanitize() must handle null/undefined with a fallback"
        )
