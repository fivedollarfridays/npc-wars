"""Tests for T56.3: structured logging in server/worker.py."""

from pathlib import Path


def test_worker_no_print_statements():
    """Worker should use logging, not print()."""
    source = Path("server/worker.py").read_text()
    lines = source.split("\n")
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("print(") and not stripped.startswith("#"):
            assert False, f"Found print() at line {i}: {stripped}"


def test_worker_imports_logging():
    """Worker should import the logging module."""
    source = Path("server/worker.py").read_text()
    assert "import logging" in source


def test_worker_has_logger():
    """Worker should define a module-level logger."""
    source = Path("server/worker.py").read_text()
    assert "logging.getLogger" in source
