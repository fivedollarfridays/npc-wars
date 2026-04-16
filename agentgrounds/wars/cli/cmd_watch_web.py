"""agentgrounds killswitch watch-web — open match replay in browser viewer."""
from __future__ import annotations

import argparse
import functools
import http.server
import shutil
import sys
import threading
import webbrowser
from pathlib import Path

__all__ = ["register", "run"]


def register(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("watch-web", help="Open match replay in browser")
    p.add_argument("match_file", nargs="?", default=None, help="Match JSON file (default: latest)")
    p.add_argument("--port", type=int, default=8080, help="HTTP port (default: 8080)")
    p.set_defaults(func=run)


def _find_latest_match() -> str | None:
    """Find the most recent match JSON in results/."""
    results_dir = Path("results")
    if not results_dir.exists():
        return None
    matches = sorted(results_dir.glob("match_*.json"), reverse=True)
    return str(matches[0]) if matches else None


def _find_viewer_dir() -> Path | None:
    """Find the viewer directory (from package or repo)."""
    # Check relative to package install
    pkg_viewer = Path(__file__).resolve().parent.parent.parent.parent / "viewer"
    if (pkg_viewer / "index.html").exists():
        return pkg_viewer
    # Check current directory
    if (Path("viewer") / "index.html").exists():
        return Path("viewer")
    return None


def run(args: argparse.Namespace) -> None:
    match_file = args.match_file or _find_latest_match()
    if not match_file:
        print("No match file found. Run `agentgrounds killswitch play` first.", file=sys.stderr)
        sys.exit(1)

    match_path = Path(match_file)
    if not match_path.exists():
        print(f"Match file not found: {match_file}", file=sys.stderr)
        sys.exit(1)

    viewer_dir = _find_viewer_dir()
    if not viewer_dir:
        print("Viewer not found. Serving match file directly.", file=sys.stderr)
        print(f"Open your match JSON in the browser viewer manually: {match_path.resolve()}")
        return

    # Copy match file to viewer/results/ for URL-based loading
    viewer_results = viewer_dir / "results"
    viewer_results.mkdir(exist_ok=True)
    dest = viewer_results / match_path.name
    shutil.copy2(str(match_path), str(dest))

    # Start HTTP server in background (serve from viewer_dir without chdir)
    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler, directory=str(viewer_dir),
    )

    httpd = None
    for port in (args.port, args.port + 1):
        try:
            httpd = http.server.HTTPServer(("127.0.0.1", port), handler)
            break
        except OSError:
            continue
    if httpd is None:
        print(f"Ports {args.port} and {args.port + 1} in use. Try --port <number>.", file=sys.stderr)
        sys.exit(1)

    url = f"http://localhost:{port}/index.html?match=results/{match_path.name}"

    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    print(f"Viewer: {url}")
    webbrowser.open(url)
    print("Press Ctrl+C to stop.")

    try:
        thread.join()
    except KeyboardInterrupt:
        httpd.shutdown()
        print("\nStopped.")
