"""Tests verifying Python version compatibility requirements."""

import ast
from pathlib import Path

import tomllib


class TestPythonVersionConfig:
    def test_requires_python_is_3_13(self) -> None:
        with open("pyproject.toml", "rb") as f:
            data = tomllib.load(f)
        assert data["project"]["requires-python"] == ">=3.13"

    def test_ruff_target_is_py313(self) -> None:
        with open("pyproject.toml", "rb") as f:
            data = tomllib.load(f)
        assert data["tool"]["ruff"]["target-version"] == "py313"

    def test_mypy_python_version_is_3_13(self) -> None:
        with open("pyproject.toml", "rb") as f:
            data = tomllib.load(f)
        assert data["tool"]["mypy"]["python_version"] == "3.13"

    def test_classifiers_include_3_13(self) -> None:
        with open("pyproject.toml", "rb") as f:
            data = tomllib.load(f)
        classifiers = data["project"]["classifiers"]
        assert "Programming Language :: Python :: 3.13" in classifiers

    def test_all_source_files_parseable(self) -> None:
        for py_file in Path(".").rglob("*.py"):
            if any(skip in str(py_file) for skip in [".paircoder", "__pycache__", ".claude", "egg-info", "build"]):
                continue
            source = py_file.read_text()
            ast.parse(source)
