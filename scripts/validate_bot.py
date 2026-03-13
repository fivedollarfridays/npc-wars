"""Bot validator — standalone for CI and local use.

Usage:
    python scripts/validate_bot.py bots/my_bot.py

Exit codes:
    0 — all checks passed
    1 — one or more checks failed
"""

import importlib.util
import os
import sys

__all__ = ["validate_bot"]

# Add project root to path when run as a script
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from engine.sandbox import execute_decide, validate_action  # noqa: E402

_MOCK_STATE = {
    "me": {"x": 5, "y": 5, "hp": 100, "energy": 100, "attack_power": 15, "defense": 0},
    "enemies": [{"name": "Enemy", "emoji": "👾", "x": 6, "y": 5, "hp": 80}],
    "round": 1,
    "grid_size": 10,
    "storm_border": 0,
}


def _load_module(path: str):
    """Load a bot file as a module."""
    spec = importlib.util.spec_from_file_location("_bot_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _check_attributes(module) -> list[str]:
    """Check required bot attributes. Returns list of error strings."""
    errors = []
    if not getattr(module, "BOT_NAME", None):
        errors.append("Missing required attribute: BOT_NAME")
    if not getattr(module, "BOT_EMOJI", None):
        errors.append("Missing required attribute: BOT_EMOJI")
    decide = getattr(module, "decide", None)
    if decide is None:
        errors.append("Missing required function: decide")
    elif not callable(decide):
        errors.append("decide is not callable")
    return errors


def _check_sandbox(decide) -> list[str]:
    """Run decide() in sandbox and validate the returned action. Returns errors."""
    import threading
    raw = execute_decide(decide, _MOCK_STATE, timeout=1.0)
    if raw is None:
        def _probe():
            try:
                decide(_MOCK_STATE)
            except Exception:
                pass
        t = threading.Thread(target=_probe)
        t.daemon = True
        t.start()
        t.join(0.1)
        msg = "decide() timed out (exceeded 1 second)" if t.is_alive() else \
              "decide() raised an exception or timed out"
        return [msg]
    if validate_action(raw) is None:
        return [f"decide() returned an invalid action: {raw!r}"]
    return []


def validate_bot(path: str) -> tuple[bool, list[str]]:
    """Validate a bot file. Returns (ok, errors)."""
    if not os.path.exists(path):
        return False, [f"File not found: {path}"]

    try:
        module = _load_module(path)
    except SyntaxError as e:
        return False, [f"Syntax error: {e}"]
    except Exception as e:
        return False, [f"Failed to load: {e}"]

    errors = _check_attributes(module)
    if errors:
        return False, errors

    errors = _check_sandbox(module.decide)
    return (not errors), errors


def _main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/validate_bot.py <path/to/bot.py>")
        sys.exit(1)

    path = sys.argv[1]
    ok, errors = validate_bot(path)

    if ok:
        print(f"✓ {path} — all checks passed")
        sys.exit(0)
    else:
        print(f"✗ {path} — validation failed:")
        for e in errors:
            print(f"  • {e}")
        sys.exit(1)


if __name__ == "__main__":
    _main()
