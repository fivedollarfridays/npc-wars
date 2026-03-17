"""npcwars generate — AI-assisted bot creation."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

__all__ = ["register", "run"]

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the generate subcommand."""
    p = subparsers.add_parser("generate", help="Generate a bot using AI")
    p.add_argument("--strategy", type=str, default="", help="Strategy description")
    p.add_argument("--name", type=str, default="", help="Bot name")
    p.add_argument("--emoji", type=str, default="", help="Bot emoji")
    p.add_argument(
        "--auto",
        action="store_true",
        help="Call Claude API directly (requires ANTHROPIC_API_KEY)",
    )
    p.add_argument("--output", type=str, default="", help="Output file path")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> None:
    """Execute the generate command."""
    prompt = _build_prompt(args.strategy, args.name, args.emoji)

    if args.auto:
        _auto_generate(prompt, args)
    else:
        _manual_generate(prompt)


def _build_prompt(strategy: str, name: str, emoji: str) -> str:
    """Load PROMPT.md and append optional customisation."""
    prompt_path = _PROJECT_ROOT / "PROMPT.md"
    if not prompt_path.is_file():
        print("Error: PROMPT.md not found", file=sys.stderr)
        sys.exit(1)

    prompt = prompt_path.read_text(encoding="utf-8")

    extras: list[str] = []
    if name:
        extras.append(f"Bot name: {name}")
    if emoji:
        extras.append(f"Bot emoji: {emoji}")
    if strategy:
        extras.append(f"Strategy: {strategy}")

    if extras:
        prompt += "\n\n## Additional Requirements\n\n" + "\n".join(extras)

    return prompt


def _manual_generate(prompt: str) -> None:
    """Print prompt to stdout for copy-pasting into an LLM."""
    print(prompt)
    print("\n---")
    print("Copy the above prompt and paste it into Claude, Gemini, or GPT.")
    print("Save the response as a .py file in your bots/ directory.")
    print("Then run: npcwars validate bots/your_bot.py")


def _auto_generate(prompt: str, args: argparse.Namespace) -> None:
    """Call Claude API to generate a bot."""
    import os

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print(
            "Error: ANTHROPIC_API_KEY environment variable not set.",
            file=sys.stderr,
        )
        print("Set it with: export ANTHROPIC_API_KEY=sk-ant-...", file=sys.stderr)
        print(
            "\nOr use without --auto to get the prompt for manual pasting.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        import anthropic
    except ImportError:
        print("Error: anthropic package not installed.", file=sys.stderr)
        print("Install with: pip install anthropic", file=sys.stderr)
        sys.exit(1)

    print("Generating bot with Claude...", file=sys.stderr)
    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )

    source = response.content[0].text
    source = _strip_code_fences(source)

    _validate_and_save(source, args)


def _strip_code_fences(source: str) -> str:
    """Remove markdown code fences if present."""
    if source.startswith("```"):
        lines = source.split("\n")
        if lines[-1].strip() == "```":
            return "\n".join(lines[1:-1])
        return "\n".join(lines[1:])
    return source


def _validate_and_save(source: str, args: argparse.Namespace) -> None:
    """Validate generated source and write to disk."""
    from engine.bot_scanner import scan_bot_source

    errors = scan_bot_source(source)
    if errors:
        print(f"Warning: Generated bot has scan errors: {errors}", file=sys.stderr)
        print("Saving anyway — you may need to fix these.", file=sys.stderr)

    out_path = _resolve_output_path(args)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(source, encoding="utf-8")
    print(f"Bot saved to {out_path}", file=sys.stderr)
    print(f"Validate: npcwars validate {out_path}", file=sys.stderr)
    print("Play: npcwars battle --seed 42", file=sys.stderr)


def _resolve_output_path(args: argparse.Namespace) -> Path:
    """Determine output file path from args."""
    if args.output:
        return Path(args.output)
    if args.name:
        return Path("bots") / f"{args.name.lower().replace(' ', '_')}.py"
    return Path("bots") / "ai_generated.py"
