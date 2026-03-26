"""AST pre-scan to block dangerous imports and calls in bot source code.

Scans bot source files using ast.parse() + ast.walk() to detect:
- Blocked module imports (import X, from X import Y)
- Dangerous built-in calls (eval, exec, compile, __import__, open)
"""

import ast
import importlib.abc
import importlib.util
import os
import re
import types

__all__ = [
    "BLOCKED_MODULES", "BLOCKED_CALLS", "_BLOCKED_DUNDER_ATTRS",
    "scan_bot_source", "scan_bot_file", "load_bot_module",
    "count_decide_lines", "validate_line_budget",
]

BLOCKED_MODULES: frozenset[str] = frozenset({
    "os", "subprocess", "socket", "sys", "ctypes",
    "importlib", "shutil", "signal", "multiprocessing", "threading",
    "builtins", "io", "pathlib", "pickle", "http", "urllib", "asyncio",
    "ftplib", "smtplib", "telnetlib", "pty", "tty",
    "tempfile", "zipfile", "xmlrpc", "code", "marshal",
})

BLOCKED_CALLS: frozenset[str] = frozenset({
    "eval", "exec", "compile", "__import__", "open",
    "getattr", "setattr", "delattr", "vars", "locals", "globals",
    "dir", "__build_class__",
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
_BLOCKED_ATTR_CALLS: frozenset[str] = frozenset({
    "__import__", "__init__", "__call__", "__getattr__", "__setattr__",
})

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


_STRING_RE = re.compile(r'''("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')''')


def _check_semicolons(tree: ast.AST, source: str) -> list[str]:
    """Flag semicolon statement chaining in decide() body."""
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "decide":
            lines = source.splitlines()
            start = node.body[0].lineno if node.body else node.lineno
            end = node.end_lineno or start
            for lineno in range(start, end + 1):
                line = lines[lineno - 1].strip()
                if line.startswith("#"):
                    continue
                cleaned = _STRING_RE.sub("", line)
                if ";" in cleaned:
                    violations.append(
                        f"Semicolon chaining detected (line {lineno})"
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
    violations.extend(_check_semicolons(tree, source))
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


def count_decide_lines(source: str) -> int:
    """Count executable lines in the decide() function body.

    Excludes blank lines, comment-only lines, and docstring lines.
    Only counts lines in the first top-level `def decide(...)` function.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return 0
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "decide":
            body_lines = source.splitlines()
            start = node.body[0].lineno
            end = node.end_lineno or start
            # Skip docstring if first body node is Expr(Constant(str))
            skip_until = start
            if (node.body
                    and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)):
                skip_until = (node.body[0].end_lineno or start) + 1
            count = 0
            for lineno in range(skip_until, end + 1):
                line = body_lines[lineno - 1].strip()
                if not line:
                    continue
                if line.startswith("#"):
                    continue
                count += 1
            return count
    return 0


def validate_line_budget(source: str, budget: int) -> None:
    """Validate that decide() body doesn't exceed the line budget.

    Raises ValueError if count > budget.
    """
    count = count_decide_lines(source)
    if count > budget:
        raise ValueError(f"decide() has {count} lines, budget is {budget}")


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
