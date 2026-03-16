"""Tests for player profile wiring in play.py."""

import ast
from pathlib import Path

import pytest


PLAY_PY = Path(__file__).resolve().parent.parent / "play.py"


class TestPlayProfilesImport:
    """Verify play.py imports Path from pathlib."""

    def test_imports_path_from_pathlib(self) -> None:
        source = PLAY_PY.read_text()
        tree = ast.parse(source)
        found = any(
            isinstance(node, ast.ImportFrom)
            and node.module == "pathlib"
            and any(alias.name == "Path" for alias in node.names)
            for node in ast.walk(tree)
        )
        assert found, "play.py must import Path from pathlib"


class TestPlayProfilesWiring:
    """Verify play.py passes profiles_path to run_match."""

    def test_run_match_called_with_profiles_path(self) -> None:
        """The run_match() call in main() must include profiles_path kwarg."""
        source = PLAY_PY.read_text()
        tree = ast.parse(source)
        # Find all calls to run_match in the main function
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "main":
                for child in ast.walk(node):
                    if (
                        isinstance(child, ast.Call)
                        and isinstance(child.func, ast.Name)
                        and child.func.id == "run_match"
                    ):
                        kwarg_names = [kw.arg for kw in child.keywords]
                        assert "profiles_path" in kwarg_names, (
                            "run_match() call must include profiles_path keyword argument"
                        )
                        return
        pytest.fail("Could not find run_match() call in main()")

    def test_profiles_path_uses_data_directory(self) -> None:
        """profiles_path must point to data/profiles.json."""
        source = PLAY_PY.read_text()
        assert "profiles.json" in source, (
            "play.py must reference profiles.json"
        )
        assert '"data"' in source or "'data'" in source, (
            "play.py must reference the data directory"
        )


class TestPlayProfilesDirCreation:
    """Verify play.py creates the data/ parent directory."""

    def test_mkdir_called_for_profiles_parent(self) -> None:
        """play.py must ensure the profiles_path parent directory exists."""
        source = PLAY_PY.read_text()
        assert "mkdir" in source, (
            "play.py must call mkdir to create the data directory"
        )
        assert "parents=True" in source, (
            "play.py must use parents=True for mkdir"
        )
        assert "exist_ok=True" in source, (
            "play.py must use exist_ok=True for mkdir"
        )
