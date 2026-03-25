"""Tests for S49 sandbox builtins lockdown + scanner hardening.

Cycle 1: Scanner blocks new dangerous calls (getattr, vars, locals, globals, etc.)
Cycle 2: Sandbox builtins lockdown (__import__ removed, safe builtins work)
Cycle 3: Existing bots still pass validation
"""

import glob
import os

import pytest

from engine.bot_scanner import (
    BLOCKED_CALLS,
    _BLOCKED_ATTR_CALLS,
    scan_bot_source,
)
from server.docker_sandbox import load_bot_from_source


# --- Cycle 1: Scanner blocks new dangerous calls ---


class TestScannerBlocksNewCalls:
    """getattr, setattr, delattr, vars, locals, globals, dir, __build_class__."""

    def test_getattr_blocked(self):
        source = "x = getattr((), '__class__')\n"
        violations = scan_bot_source(source)
        assert any("getattr" in v for v in violations)

    def test_setattr_blocked(self):
        source = "setattr(obj, 'x', 1)\n"
        violations = scan_bot_source(source)
        assert any("setattr" in v for v in violations)

    def test_delattr_blocked(self):
        source = "delattr(obj, 'x')\n"
        violations = scan_bot_source(source)
        assert any("delattr" in v for v in violations)

    def test_vars_blocked(self):
        source = "x = vars()\n"
        violations = scan_bot_source(source)
        assert any("vars" in v for v in violations)

    def test_locals_blocked(self):
        source = "x = locals()\n"
        violations = scan_bot_source(source)
        assert any("locals" in v for v in violations)

    def test_globals_blocked(self):
        source = "x = globals()\n"
        violations = scan_bot_source(source)
        assert any("globals" in v for v in violations)

    def test_dir_blocked(self):
        source = "x = dir()\n"
        violations = scan_bot_source(source)
        assert any("dir" in v for v in violations)

    def test_build_class_blocked(self):
        source = "__build_class__(lambda: None, 'X')\n"
        violations = scan_bot_source(source)
        assert any("__build_class__" in v for v in violations)

    @pytest.mark.parametrize("call", [
        "getattr", "setattr", "delattr", "vars", "locals",
        "globals", "dir", "__build_class__",
    ])
    def test_new_calls_in_blocklist(self, call):
        assert call in BLOCKED_CALLS


class TestScannerBlocksNewAttrCalls:
    """__init__, __call__, __getattr__, __setattr__ in _BLOCKED_ATTR_CALLS."""

    @pytest.mark.parametrize("attr", [
        "__init__", "__call__", "__getattr__", "__setattr__",
    ])
    def test_attr_in_blocklist(self, attr):
        assert attr in _BLOCKED_ATTR_CALLS

    def test_obj_getattr_call_blocked(self):
        source = "x.__getattr__('secret')\n"
        violations = scan_bot_source(source)
        assert any("__getattr__" in v for v in violations)

    def test_obj_setattr_call_blocked(self):
        source = "x.__setattr__('y', 1)\n"
        violations = scan_bot_source(source)
        assert any("__setattr__" in v for v in violations)


# --- Cycle 2: Sandbox builtins lockdown ---


class TestSandboxBuiltinsLockdown:
    """__import__, getattr, setattr removed from exec namespace."""

    _MINIMAL_BOT = (
        "BOT_NAME = 'Test'\n"
        "BOT_EMOJI = '\\U0001f916'\n"
        "def decide(state): return ('rest',)\n"
    )

    def test_import_os_blocked_in_sandbox(self):
        """import os should raise ImportError inside sandbox exec."""
        source = (
            "import os\n"
            "BOT_NAME = 'Evil'\n"
            "BOT_EMOJI = '\\U0001f916'\n"
            "def decide(state): return ('rest',)\n"
        )
        # Scanner catches blocked imports first (ValueError)
        with pytest.raises(ValueError, match="failed scan"):
            load_bot_from_source(source, "evil_bot")

    def test_restricted_import_blocks_os_at_runtime(self):
        """Even without scanner, restricted __import__ blocks dangerous modules."""
        # Bypass scanner by testing the restricted import directly
        import builtins as _builtins
        from engine.bot_scanner import BLOCKED_MODULES

        real_import = _builtins.__import__

        def restricted_import(name, *args, **kwargs):
            root = name.split(".")[0]
            if root in BLOCKED_MODULES:
                raise ImportError(f"Import blocked: '{name}'")
            return real_import(name, *args, **kwargs)

        # Blocked module
        with pytest.raises(ImportError, match="Import blocked"):
            restricted_import("os")

        # Safe module works
        mod = restricted_import("random")
        assert hasattr(mod, "randint")

    def test_import_not_in_builtins(self):
        """Normal bot loads fine; __import__ simply isn't available."""
        config = load_bot_from_source(self._MINIMAL_BOT, "safe_bot")
        assert config["name"] == "Test"

    def test_safe_builtins_len(self):
        source = (
            "x = len([1, 2, 3])\n"
            "BOT_NAME = 'Test'\n"
            "BOT_EMOJI = '\\U0001f916'\n"
            "def decide(state): return ('rest',)\n"
        )
        config = load_bot_from_source(source, "test_bot")
        assert config["name"] == "Test"

    def test_safe_builtins_range(self):
        source = (
            "x = list(range(5))\n"
            "BOT_NAME = 'Test'\n"
            "BOT_EMOJI = '\\U0001f916'\n"
            "def decide(state): return ('rest',)\n"
        )
        config = load_bot_from_source(source, "test_bot")
        assert config["name"] == "Test"

    def test_safe_builtins_min_max_sorted(self):
        source = (
            "a = min(1, 2)\n"
            "b = max(3, 4)\n"
            "c = sorted([3, 1, 2])\n"
            "BOT_NAME = 'Test'\n"
            "BOT_EMOJI = '\\U0001f916'\n"
            "def decide(state): return ('rest',)\n"
        )
        config = load_bot_from_source(source, "test_bot")
        assert config["name"] == "Test"

    def test_safe_builtins_isinstance(self):
        source = (
            "x = isinstance(1, int)\n"
            "BOT_NAME = 'Test'\n"
            "BOT_EMOJI = '\\U0001f916'\n"
            "def decide(state): return ('rest',)\n"
        )
        config = load_bot_from_source(source, "test_bot")
        assert config["name"] == "Test"

    def test_safe_builtins_exceptions(self):
        source = (
            "try:\n"
            "    raise ValueError('test')\n"
            "except ValueError:\n"
            "    pass\n"
            "BOT_NAME = 'Test'\n"
            "BOT_EMOJI = '\\U0001f916'\n"
            "def decide(state): return ('rest',)\n"
        )
        config = load_bot_from_source(source, "test_bot")
        assert config["name"] == "Test"


# --- Cycle 3: Existing bots still pass validation ---


class TestExistingBotsStillValid:
    """All bots in bots/ must still pass scanner validation."""

    @pytest.fixture()
    def bot_files(self):
        bots_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "bots"
        )
        files = glob.glob(os.path.join(bots_dir, "*.py"))
        assert len(files) > 0, "No bot files found in bots/"
        return files

    def test_all_bots_pass_scan(self, bot_files):
        from engine.bot_scanner import scan_bot_file

        for bot_path in bot_files:
            violations = scan_bot_file(bot_path)
            assert violations == [], (
                f"Bot {os.path.basename(bot_path)} has violations: {violations}"
            )
