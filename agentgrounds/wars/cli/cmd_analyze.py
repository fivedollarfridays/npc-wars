"""agentgrounds wars analyze -- parse sim output and generate analysis."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

__all__ = ["register", "run"]


def register(subparser: argparse._SubParsersAction) -> None:
    """Register the analyze subcommand."""
    p = subparser.add_parser("analyze", help="Analyze batch sim results (heatmaps, energy, balance)")
    p.add_argument(
        "--input", type=str, required=True,
        help="Directory containing match_*.json files",
    )
    p.add_argument(
        "--output", type=str, required=True,
        help="Directory for analysis output",
    )
    p.add_argument(
        "--format", type=str, default="both", choices=["ascii", "json", "both"],
        help="Output format (default: both)",
    )
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> None:
    """Execute the analyze command."""
    input_dir = Path(getattr(args, "input"))
    output_dir = Path(args.output)
    fmt = getattr(args, "format")

    if not input_dir.is_dir():
        print(f"Error: input directory not found: {input_dir}", file=sys.stderr)
        sys.exit(1)

    from agentgrounds.wars.analyzer import run_analysis

    result = run_analysis(input_dir=input_dir, output_dir=output_dir, fmt=fmt)
    report = result["report"]

    # Print ASCII heatmaps
    if result.get("ascii"):
        print(result["ascii"])

    # Print balance verdict
    print("=== Balance Verdict ===")
    for key, data in report["verdict"].items():
        print(f"  {key}: {data['verdict']}")

    print(f"\nAnalysis complete: {report['match_count']} matches analyzed")
    if fmt in ("json", "both"):
        print(f"Output written to: {output_dir}")
