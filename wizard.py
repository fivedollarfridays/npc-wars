"""NPC Wars Bot Wizard -- interactive bot generator.

Usage:
    python wizard.py                          # interactive mode
    python wizard.py --non-interactive ...    # scripted mode
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
import textwrap
from pathlib import Path

from npcwars.presets import PRESET_NAMES, generate_preset

__all__ = [
    "build_bot_source",
    "check_name_unique",
    "create_bot_file",
    "parse_args",
    "run_interactive",
    "validate_inputs",
]

_STYLE_MENU = {
    "1": "aggro",
    "2": "tank",
    "3": "kiter",
    "4": "opportunist",
    "5": "chaos",
}

_STYLE_LABELS = {
    "aggro": "Aggro    -- chase and kill everything",
    "tank": "Tank     -- defend, counter, outlast",
    "kiter": "Kiter    -- stay at range, poke wounded",
    "opportunist": "Opportunist -- conserve energy, strike when advantageous",
    "chaos": "Chaos    -- pure random mayhem",
}

_NAME_RE = re.compile(r"^[A-Za-z0-9_ ]+$")
_RESERVED_NAMES = frozenset({
    "__init__", "__main__", "setup", "conftest", "__pycache__",
})


def validate_inputs(
    name: str,
    emoji: str,
    style: str,
    aggression: int,
    risk: int,
) -> list[str]:
    """Validate wizard inputs. Returns list of error strings (empty = valid)."""
    errors: list[str] = []
    if not name or not name.strip():
        errors.append("Name must be non-empty")
    elif not _NAME_RE.match(name):
        errors.append("Name must be alphanumeric, spaces, or underscores")
    elif name.lower().replace(" ", "_") in _RESERVED_NAMES:
        errors.append(f"Name {name!r} conflicts with a reserved Python filename")
    if not emoji or not emoji.strip():
        errors.append("Emoji must be non-empty")
    if style not in PRESET_NAMES:
        errors.append(f"Style must be one of {PRESET_NAMES!r}, got {style!r}")
    if not (1 <= aggression <= 10):
        errors.append(f"Aggression must be 1-10, got {aggression}")
    if not (1 <= risk <= 10):
        errors.append(f"Risk must be 1-10, got {risk}")
    return errors


def check_name_unique(
    name: str, emoji: str, output_dir: Path
) -> list[str]:
    """Check for duplicate BOT_NAME or BOT_EMOJI in output directory."""
    errors: list[str] = []
    if not output_dir.is_dir():
        return errors
    for path in output_dir.glob("*.py"):
        try:
            content = path.read_text()
        except OSError:
            continue
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("BOT_NAME") and (f'"{name}"' in stripped or f"'{name}'" in stripped):
                errors.append(f"BOT_NAME {name!r} already exists in {path.name}")
            if stripped.startswith("BOT_EMOJI") and (f'"{emoji}"' in stripped or f"'{emoji}'" in stripped):
                errors.append(
                    f"BOT_EMOJI {emoji!r} already exists in {path.name}"
                )
    return errors


def build_bot_source(
    name: str,
    emoji: str,
    style: str,
    aggression: int,
    risk: int,
    bio: str = "",
    author: str = "",
) -> str:
    """Build complete bot file source code."""
    preset_body = generate_preset(style, aggression, risk)
    indented_body = textwrap.indent(preset_body, "    ")
    docstring = (
        f'"""NPC Wars Bot -- {name} '
        f'({style} preset, aggression={aggression}, risk={risk})"""'
    )
    lines = [
        docstring,
        "",
        f"BOT_NAME = {repr(name)}",
        f"BOT_EMOJI = {repr(emoji)}",
        f"BOT_BIO = {repr(bio)}",
        f"BOT_AUTHOR = {repr(author)}",
        "",
        "",
        "def decide(state):",
        indented_body,
        "",
    ]
    return "\n".join(lines)


def create_bot_file(
    name: str,
    emoji: str,
    style: str,
    aggression: int,
    risk: int,
    bio: str,
    author: str,
    output_dir: Path,
) -> Path:
    """Create the bot file and return its path."""
    source = build_bot_source(name, emoji, style, aggression, risk, bio, author)
    # Sanity check: generated code must parse
    ast.parse(source)
    filename = name.lower().replace(" ", "_") + ".py"
    out_path = output_dir / filename
    output_dir.mkdir(parents=True, exist_ok=True)
    resolved = out_path.resolve()
    if not str(resolved).startswith(str(output_dir.resolve())):
        raise ValueError("filename would escape output directory")
    out_path.write_text(source)
    return out_path


def _prompt_slider(label: str, default: int = 5) -> int:
    """Prompt for a 1-10 slider value."""
    raw = input(f"{label} (1-10, default {default}): > ").strip()
    if not raw:
        return default
    try:
        val = int(raw)
    except ValueError:
        print(f"Invalid number, using default {default}")
        return default
    if not (1 <= val <= 10):
        print(f"Out of range, using default {default}")
        return default
    return val


def run_interactive() -> None:
    """Run the wizard in interactive mode."""
    print("NPC Wars Bot Wizard")
    name = input("Bot name: > ").strip()
    emoji = input("Pick an emoji: > ").strip()
    bio = input("Short bio (optional): > ").strip()
    author = input("Author name (optional): > ").strip()
    print("\nPick a playstyle:")
    for num, style_key in sorted(_STYLE_MENU.items()):
        print(f"  {num}. {_STYLE_LABELS[style_key]}")
    style_input = input("> ").strip()
    style = _STYLE_MENU.get(style_input)
    if style is None and style_input in PRESET_NAMES:
        style = style_input
    if style is None:
        print(f"Error: invalid style choice {style_input!r}")
        sys.exit(1)
    aggression = _prompt_slider("Aggression")
    risk = _prompt_slider("Risk tolerance")
    errors = validate_inputs(name, emoji, style, aggression, risk)
    if errors:
        for e in errors:
            print(f"Error: {e}")
        sys.exit(1)
    output_dir = Path("bots")
    dup_errors = check_name_unique(name, emoji, output_dir)
    if dup_errors:
        for e in dup_errors:
            print(f"Error: {e}")
        sys.exit(1)
    out_path = create_bot_file(
        name, emoji, style, aggression, risk, bio, author, output_dir
    )
    print(f"Created {out_path}")
    print("Run: python play.py")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="NPC Wars Bot Wizard")
    parser.add_argument("--non-interactive", action="store_true")
    parser.add_argument("--name", type=str, default="")
    parser.add_argument("--emoji", type=str, default="")
    parser.add_argument("--style", type=str, default="")
    parser.add_argument("--aggression", type=int, default=5)
    parser.add_argument("--risk", type=int, default=5)
    parser.add_argument("--bio", type=str, default="")
    parser.add_argument("--author", type=str, default="")
    parser.add_argument("--output-dir", type=str, default="bots")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Entry point."""
    args = parse_args(argv)
    if not args.non_interactive:
        run_interactive()
        return
    # Non-interactive mode
    errors = validate_inputs(
        args.name, args.emoji, args.style, args.aggression, args.risk
    )
    if errors:
        for e in errors:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    output_dir = Path(args.output_dir)
    dup_errors = check_name_unique(args.name, args.emoji, output_dir)
    if dup_errors:
        for e in dup_errors:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    out_path = create_bot_file(
        args.name, args.emoji, args.style, args.aggression, args.risk,
        args.bio, args.author, output_dir,
    )
    print(f"Created {out_path}")


if __name__ == "__main__":
    main()
