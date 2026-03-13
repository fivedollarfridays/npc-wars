"""AST pre-scan to block dangerous imports and calls in bot source code.

Scans bot source files using ast.parse() + ast.walk() to detect:
- Blocked module imports (import X, from X import Y)
- Dangerous built-in calls (eval, exec, compile, __import__, open)
"""

import ast
import importlib.abc
import importlib.util
import os
import types

__all__ = [
    "BLOCKED_MODULES", "BLOCKED_CALLS", "_BLOCKED_DUNDER_ATTRS",
    "scan_bot_source", "scan_bot_file", "load_bot_module",
]

BLOCKED_MODULES: frozenset[str] = frozenset({
    "os", "subprocess", "socket", "sys", "ctypes",
    "importlib", "shutil", "signal", "multiprocessing", "threading",
    "builtins", "io", "pathlib", "pickle", "http", "urllib", "asyncio",
})

BLOCKED_CALLS: frozenset[str] = frozenset({
    "eval", "exec", "compile", "__import__", "open",
})


def _check_imports(tree: ast.AST) -> list[str]:
    """Find blocked import statements in an AST."""
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in BLOCKED_MODULES:
                    violations.append(
                        f"Blocked import: '{alias.name}' (line {node.lineno})"
                    )
        elif isinstance(node, ast.ImportFrom):
            if node.module is not None:
                root = node.module.split(".")[0]
                if root in BLOCKED_MODULES:
                    violations.append(
                        f"Blocked import: 'from {node.module} import ...' (line {node.lineno})"
                    )
    return violations


# Calls that are dangerous even as method calls (obj.__import__())
_BLOCKED_ATTR_CALLS: frozenset[str] = frozenset({"__import__"})

_BLOCKED_DUNDER_ATTRS: frozenset[str] = frozenset({
    "__globals__", "__builtins__", "__subclasses__", "__mro__",
    "__bases__", "__class__", "__code__", "__closure__",
})


def _check_calls(tree: ast.AST) -> list[str]:
    """Find dangerous function calls in an AST."""
    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id in BLOCKED_CALLS:
            violations.append(
                f"Blocked call: '{func.id}()' (line {node.lineno})"
            )
        elif isinstance(func, ast.Attribute) and func.attr in _BLOCKED_ATTR_CALLS:
            violations.append(
                f"Blocked call: '{func.attr}()' (line {node.lineno})"
            )
    return violations


def _check_dunder_attrs(tree: ast.AST) -> list[str]:
    """Find blocked dunder attribute access in an AST."""
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in _BLOCKED_DUNDER_ATTRS:
            violations.append(
                f"Blocked dunder attr: '{node.attr}' (line {node.lineno})"
            )
    return violations


def scan_bot_source(source: str) -> list[str]:
    """Scan bot source code for security violations.

    Returns a list of violation description strings. Empty list means clean.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return [f"Syntax error — failed to parse source: {e}"]

    violations: list[str] = []
    violations.extend(_check_imports(tree))
    violations.extend(_check_calls(tree))
    violations.extend(_check_dunder_attrs(tree))
    return violations


def scan_bot_file(path: str) -> list[str]:
    """Scan a bot file on disk for security violations.

    Returns a list of violation description strings. Empty list means clean.
    """
    try:
        with open(path, encoding="utf-8") as f:
            source = f.read()
    except OSError as e:
        return [f"Failed to read file: {e}"]

    return scan_bot_source(source)


def load_bot_module(path: str, module_name: str | None = None) -> types.ModuleType:
    """Scan and load a bot file as a Python module.

    Runs AST pre-scan first. Raises ValueError if scan finds violations.
    Raises ImportError if module cannot be loaded.
    """
    violations = scan_bot_file(path)
    if violations:
        raise ValueError("; ".join(violations))

    if module_name is None:
        module_name = f"_bot_{os.path.basename(path).removesuffix('.py')}"

    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or not isinstance(spec.loader, importlib.abc.Loader):
        raise ImportError(f"Invalid module spec for {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
