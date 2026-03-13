"""Tests for line budget enforcement in bot scanner.

Tests count_decide_lines(), validate_line_budget(), and semicolon detection.
"""

import pytest

from engine.bot_scanner import count_decide_lines, validate_line_budget, scan_bot_source


# --- Test sources ---

SOURCE_5_LINES = """\
def decide(state):
    me = state["me"]
    enemies = state["enemies"]
    if not enemies:
        return ("rest",)
    return ("attack", "north")
"""


# --- Cycle 1: basic line counting ---


class TestCountDecideLinesBasic:
    """Count executable lines in decide() body."""

    def test_counts_simple_body(self):
        assert count_decide_lines(SOURCE_5_LINES) == 5

    def test_minimal_decide(self):
        source = "def decide(state):\n    return ('rest',)\n"
        assert count_decide_lines(source) == 1

    def test_no_decide_returns_zero(self):
        source = "def other(state):\n    return 1\n"
        assert count_decide_lines(source) == 0


# --- Cycle 2: exclusions (blanks, comments, docstrings) ---

SOURCE_WITH_BLANKS = """\
def decide(state):
    # setup
    me = state["me"]

    # find enemies
    enemies = state["enemies"]
    return ("rest",)
"""

SOURCE_WITH_DOCSTRING = '''\
def decide(state):
    """Pick an action based on current state."""
    me = state["me"]
    return ("rest",)
'''

SOURCE_MULTILINE_DOCSTRING = '''\
def decide(state):
    """Pick an action.

    Uses simple logic.
    """
    me = state["me"]
    return ("rest",)
'''


class TestCountDecideLinesExclusions:
    """Blank lines, comments, and docstrings are excluded."""

    def test_blanks_excluded(self):
        assert count_decide_lines(SOURCE_WITH_BLANKS) == 3

    def test_comments_excluded(self):
        assert count_decide_lines(SOURCE_WITH_BLANKS) == 3

    def test_single_line_docstring_excluded(self):
        assert count_decide_lines(SOURCE_WITH_DOCSTRING) == 2

    def test_multiline_docstring_excluded(self):
        assert count_decide_lines(SOURCE_MULTILINE_DOCSTRING) == 2


# --- Cycle 3: validate_line_budget ---


class TestValidateLineBudget:
    """validate_line_budget passes or raises ValueError."""

    def test_under_budget_passes(self):
        # 5 lines, budget 10 — should not raise
        validate_line_budget(SOURCE_5_LINES, 10)

    def test_at_budget_passes(self):
        # 5 lines, budget 5 — should not raise
        validate_line_budget(SOURCE_5_LINES, 5)

    def test_over_budget_raises(self):
        # 5 lines, budget 3 — should raise
        with pytest.raises(ValueError, match=r"decide\(\) has 5 lines, budget is 3"):
            validate_line_budget(SOURCE_5_LINES, 3)


# --- Cycle 4: semicolon detection ---

SOURCE_WITH_SEMICOLONS = """\
def decide(state):
    a = 1; b = 2
    return ("rest",)
"""


class TestSemicolonDetection:
    """Semicolons in decide() body are flagged by scanner."""

    def test_semicolon_flagged_as_violation(self):
        violations = scan_bot_source(SOURCE_WITH_SEMICOLONS)
        assert any("Semicolon" in v or "semicolon" in v.lower() for v in violations)

    def test_semicolon_counts_as_one_line(self):
        # a=1; b=2 is one source line, so counts as 1 line
        assert count_decide_lines(SOURCE_WITH_SEMICOLONS) == 2

    def test_semicolon_in_string_not_flagged(self):
        source = 'def decide(state):\n    x = "a;b"\n    return ("rest",)\n'
        violations = scan_bot_source(source)
        semicolon_violations = [v for v in violations if "semicolon" in v.lower()]
        assert semicolon_violations == []
