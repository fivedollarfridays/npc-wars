"""Tests for engine.bot_scanner — AST pre-scan to block dangerous imports/calls."""

import pytest

from engine.bot_scanner import (
    scan_bot_source, BLOCKED_MODULES, BLOCKED_CALLS, _BLOCKED_DUNDER_ATTRS,
)


# --- Cycle 1: import X detection ---

class TestImportDetection:
    """Detect blocked 'import X' statements."""

    def test_safe_import_random(self):
        source = "import random\n"
        violations = scan_bot_source(source)
        assert violations == []

    def test_safe_import_math(self):
        source = "import math\n"
        violations = scan_bot_source(source)
        assert violations == []

    def test_blocked_import_os(self):
        source = "import os\n"
        violations = scan_bot_source(source)
        assert len(violations) == 1
        assert "os" in violations[0]

    def test_blocked_import_subprocess(self):
        source = "import subprocess\n"
        violations = scan_bot_source(source)
        assert len(violations) == 1
        assert "subprocess" in violations[0]

    def test_blocked_import_socket(self):
        source = "import socket\n"
        violations = scan_bot_source(source)
        assert len(violations) == 1
        assert "socket" in violations[0]

    def test_multiple_blocked_imports(self):
        source = "import os\nimport subprocess\nimport socket\n"
        violations = scan_bot_source(source)
        assert len(violations) == 3

    def test_blocked_import_in_function(self):
        source = "def foo():\n    import sys\n"
        violations = scan_bot_source(source)
        assert len(violations) == 1
        assert "sys" in violations[0]


# --- Cycle 2: from X import Y detection ---

class TestFromImportDetection:
    """Detect blocked 'from X import Y' statements."""

    def test_from_os_import_system(self):
        source = "from os import system\n"
        violations = scan_bot_source(source)
        assert len(violations) == 1
        assert "os" in violations[0]

    def test_from_subprocess_import_run(self):
        source = "from subprocess import run\n"
        violations = scan_bot_source(source)
        assert len(violations) == 1
        assert "subprocess" in violations[0]

    def test_from_importlib_import_anything(self):
        source = "from importlib import util\n"
        violations = scan_bot_source(source)
        assert len(violations) == 1
        assert "importlib" in violations[0]

    def test_safe_from_import(self):
        source = "from collections import defaultdict\n"
        violations = scan_bot_source(source)
        assert violations == []


# --- Cycle 3: dangerous call detection ---

class TestDangerousCallDetection:
    """Detect calls to eval, exec, compile, __import__, open."""

    def test_eval_call(self):
        source = "x = eval('1+1')\n"
        violations = scan_bot_source(source)
        assert len(violations) == 1
        assert "eval" in violations[0]

    def test_exec_call(self):
        source = "exec('print(1)')\n"
        violations = scan_bot_source(source)
        assert len(violations) == 1
        assert "exec" in violations[0]

    def test_compile_call(self):
        source = "compile('pass', '<string>', 'exec')\n"
        violations = scan_bot_source(source)
        assert len(violations) == 1
        assert "compile" in violations[0]

    def test_dunder_import_call(self):
        source = "__import__('os')\n"
        violations = scan_bot_source(source)
        assert len(violations) == 1
        assert "__import__" in violations[0]

    def test_open_call(self):
        source = "f = open('/etc/passwd')\n"
        violations = scan_bot_source(source)
        assert len(violations) == 1
        assert "open" in violations[0]

    def test_no_dangerous_calls_in_clean_code(self):
        source = "x = len([1, 2, 3])\ny = max(1, 2)\n"
        violations = scan_bot_source(source)
        assert violations == []

    def test_mixed_imports_and_calls(self):
        source = "import os\nx = eval('1')\n"
        violations = scan_bot_source(source)
        assert len(violations) == 2


# --- Cycle 6: attribute call false-positive reduction ---

class TestAttributeCallFalsePositives:
    """Attribute-based calls (obj.compile(), file.open()) should NOT be flagged."""

    def test_re_compile_not_flagged(self):
        source = "import re\npattern = re.compile(r'\\d+')\n"
        violations = scan_bot_source(source)
        assert violations == []

    def test_file_open_not_flagged(self):
        source = "result = file.open()\n"
        violations = scan_bot_source(source)
        assert violations == []

    def test_obj_exec_not_flagged(self):
        source = "cursor.exec('SELECT 1')\n"
        violations = scan_bot_source(source)
        assert violations == []

    def test_obj_eval_not_flagged(self):
        source = "model.eval()\n"
        violations = scan_bot_source(source)
        assert violations == []

    def test_obj_dunder_import_still_flagged(self):
        """obj.__import__() is dangerous regardless of receiver."""
        source = "builtins.__import__('os')\n"
        violations = scan_bot_source(source)
        assert len(violations) == 1
        assert "__import__" in violations[0]

    def test_bare_builtins_still_flagged(self):
        """Direct calls (eval, exec, compile, open) are still flagged."""
        source = "eval('1')\nexec('2')\ncompile('3','','exec')\nopen('f')\n"
        violations = scan_bot_source(source)
        assert len(violations) == 4


# --- Cycle 4: scan_bot_file and clean bots ---

class TestScanBotFile:
    """Test file-based scanning and example bot validation."""

    def test_clean_bot_passes(self, tmp_path):
        bot = tmp_path / "clean_bot.py"
        bot.write_text("import random\nBOT_NAME='Test'\ndef decide(s): return ('rest',)\n")
        from engine.bot_scanner import scan_bot_file
        violations = scan_bot_file(str(bot))
        assert violations == []

    def test_bad_bot_detected(self, tmp_path):
        bot = tmp_path / "bad_bot.py"
        bot.write_text("import os\nimport subprocess\n")
        from engine.bot_scanner import scan_bot_file
        violations = scan_bot_file(str(bot))
        assert len(violations) == 2

    def test_syntax_error_returns_violation(self, tmp_path):
        bot = tmp_path / "broken.py"
        bot.write_text("def foo(\n")
        from engine.bot_scanner import scan_bot_file
        violations = scan_bot_file(str(bot))
        assert len(violations) == 1
        assert "syntax" in violations[0].lower()


# --- Cycle 5: blocklist completeness ---

class TestBlocklistCompleteness:
    """Ensure all required modules are in the blocklist."""

    @pytest.mark.parametrize("module", [
        "os", "subprocess", "socket", "sys", "ctypes",
        "importlib", "shutil", "signal", "multiprocessing", "threading",
        "builtins", "io", "pathlib", "pickle", "http", "urllib", "asyncio",
    ])
    def test_module_in_blocklist(self, module):
        assert module in BLOCKED_MODULES

    @pytest.mark.parametrize("call", [
        "eval", "exec", "compile", "__import__", "open",
    ])
    def test_call_in_blocklist(self, call):
        assert call in BLOCKED_CALLS


# --- Cycle 7: dunder attribute access blocking ---

class TestDunderAttrBlocking:
    """Block dangerous dunder attribute access chains."""

    def test_globals_access_blocked(self):
        source = "func.__globals__\n"
        violations = scan_bot_source(source)
        assert len(violations) == 1
        assert "__globals__" in violations[0]

    def test_builtins_access_blocked(self):
        source = "x.__builtins__\n"
        violations = scan_bot_source(source)
        assert len(violations) == 1
        assert "__builtins__" in violations[0]

    def test_subclasses_blocked(self):
        source = "().__class__.__subclasses__()\n"
        violations = scan_bot_source(source)
        dunder_violations = [v for v in violations if "dunder" in v.lower() or "__class__" in v or "__subclasses__" in v]
        assert len(dunder_violations) >= 2
        attrs_found = {v.split("'")[1] for v in dunder_violations if "'" in v}
        assert "__class__" in attrs_found
        assert "__subclasses__" in attrs_found

    def test_mro_blocked(self):
        source = "cls.__mro__\n"
        violations = scan_bot_source(source)
        assert len(violations) == 1
        assert "__mro__" in violations[0]

    def test_bases_blocked(self):
        source = "cls.__bases__\n"
        violations = scan_bot_source(source)
        assert len(violations) == 1
        assert "__bases__" in violations[0]

    def test_code_blocked(self):
        source = "func.__code__\n"
        violations = scan_bot_source(source)
        assert len(violations) == 1
        assert "__code__" in violations[0]

    def test_closure_blocked(self):
        source = "func.__closure__\n"
        violations = scan_bot_source(source)
        assert len(violations) == 1
        assert "__closure__" in violations[0]

    def test_safe_dunder_not_blocked(self):
        source = "x.__str__()\nx.__len__()\n"
        violations = scan_bot_source(source)
        assert violations == []

    def test_init_call_blocked(self):
        """__init__() is now blocked as an attr call (S49 hardening)."""
        source = "x.__init__()\n"
        violations = scan_bot_source(source)
        assert any("__init__" in v for v in violations)

    def test_chained_dunder_access(self):
        source = "().__class__.__bases__[0].__subclasses__()\n"
        violations = scan_bot_source(source)
        attrs_found = set()
        for v in violations:
            for attr in ("__class__", "__bases__", "__subclasses__"):
                if attr in v:
                    attrs_found.add(attr)
        assert "__class__" in attrs_found
        assert "__bases__" in attrs_found
        assert "__subclasses__" in attrs_found

    @pytest.mark.parametrize("attr", [
        "__globals__", "__builtins__", "__subclasses__", "__mro__",
        "__bases__", "__class__", "__code__", "__closure__",
    ])
    def test_dunder_attr_in_blocklist(self, attr):
        assert attr in _BLOCKED_DUNDER_ATTRS


# --- Cycle: semicolon chaining detection in decide() ---

class TestSemicolonDetection:
    """Flag real semicolon chaining without false-positives on comments/strings."""

    def test_trailing_comment_semicolon_not_flagged(self):
        source = "def decide(self):\n    return 0  # floors to 0; beats resting\n"
        violations = scan_bot_source(source)
        assert violations == []

    def test_real_chaining_flagged(self):
        source = "def decide(self):\n    a = 1; b = 2\n    return a\n"
        violations = scan_bot_source(source)
        semis = [v for v in violations if "Semicolon" in v]
        assert len(semis) == 1

    def test_chaining_with_trailing_comment_flagged(self):
        source = "def decide(self):\n    a = 1; b = 2  # note\n    return a\n"
        violations = scan_bot_source(source)
        semis = [v for v in violations if "Semicolon" in v]
        assert len(semis) == 1

    def test_semicolon_in_string_literal_not_flagged(self):
        source = 'def decide(self):\n    s = "a;b"\n    return 0\n'
        violations = scan_bot_source(source)
        assert violations == []
