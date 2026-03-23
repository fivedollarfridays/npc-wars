"""agentgrounds wars upload -- upload a bot to the server."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

__all__ = ["register", "run"]

_DEFAULT_SERVER = "http://localhost:8000"
_CONFIG_DIR = Path.home() / ".agentgrounds"
_CONFIG_FILE = _CONFIG_DIR / "config.json"


def register(subparser: argparse._SubParsersAction) -> None:
    """Register the upload subcommand."""
    p = subparser.add_parser("upload", help="Upload a bot to the server")
    p.add_argument("bot_file", type=str, help="Path to bot .py file")
    p.add_argument("--server", type=str, default=None, help="Server URL")
    p.add_argument("--api-key", type=str, default=None, help="API key")
    p.add_argument(
        "--no-join", action="store_true", help="Upload only, don't join lobby",
    )
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> None:
    """Execute the upload command."""
    bot_path = Path(args.bot_file)
    if not bot_path.exists():
        print(f"Error: {bot_path} not found", file=sys.stderr)
        sys.exit(1)

    # Local validation before upload
    from engine.bot_scanner import scan_bot_file

    errors = scan_bot_file(str(bot_path))
    if errors:
        print("Bot validation failed:", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        sys.exit(1)

    source = bot_path.read_text()
    config = _load_config()
    server = args.server or config.get("server", _DEFAULT_SERVER)
    api_key = args.api_key or config.get("api_key")

    # Upload
    print(f"Uploading {bot_path.name} to {server}...")
    result = _post_json(f"{server}/api/submit-bot", {"source": source}, api_key)

    bot_id = result.get("bot_id")
    new_key = result.get("api_key")
    if new_key:
        _save_config({"server": server, "api_key": new_key})
        api_key = new_key
        print(f"API key saved to {_CONFIG_FILE}")

    print(f"Bot uploaded: {result.get('name', bot_path.stem)} (id: {bot_id})")

    if args.no_join:
        return

    _join_lobby(server, bot_id, api_key)


def _join_lobby(server: str, bot_id: str | None, api_key: str | None) -> None:
    """Join the lobby and poll for a match."""
    print("Joining lobby...")
    try:
        join_result = _post_json(
            f"{server}/api/lobby/join", {"bot_id": bot_id}, api_key,
        )
        print(f"Lobby: {join_result.get('message', 'joined')}")
    except Exception as exc:  # noqa: BLE001
        print(f"Lobby join failed: {exc}", file=sys.stderr)
        print("Bot uploaded successfully. Join lobby manually.")
        return

    _poll_for_match(server, api_key)


def _poll_for_match(server: str, api_key: str | None) -> None:
    """Poll lobby status until a match starts or timeout."""
    print("Waiting for opponents...", end="", flush=True)
    for _ in range(120):
        time.sleep(1)
        try:
            status = _get_json(f"{server}/api/lobby/status", api_key)
        except Exception:  # noqa: BLE001
            break
        if status.get("match_id"):
            mid = status["match_id"]
            print(f"\nMatch started! ID: {mid}")
            print(f"Watch: {server}/m/{mid}")
            return
        print(".", end="", flush=True)
    print("\nTimeout waiting for match.")


def _post_json(
    url: str, data: dict, api_key: str | None = None,
) -> dict:
    """POST JSON to url and return parsed response."""
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key
    req = Request(url, json.dumps(data).encode(), headers, method="POST")
    try:
        with urlopen(req, timeout=30) as resp:  # noqa: S310
            return json.loads(resp.read())
    except HTTPError as exc:
        body = exc.read().decode()
        print(f"Server error ({exc.code}): {body}", file=sys.stderr)
        sys.exit(1)
    except URLError as exc:
        print(f"Cannot connect to {url}: {exc}", file=sys.stderr)
        sys.exit(1)


def _get_json(url: str, api_key: str | None = None) -> dict:
    """GET JSON from url and return parsed response."""
    headers: dict[str, str] = {}
    if api_key:
        headers["X-API-Key"] = api_key
    req = Request(url, headers=headers)
    with urlopen(req, timeout=10) as resp:  # noqa: S310
        return json.loads(resp.read())


def _load_config() -> dict:
    """Load config from ~/.agentgrounds/config.json."""
    if _CONFIG_FILE.exists():
        return json.loads(_CONFIG_FILE.read_text())
    return {}


def _save_config(data: dict) -> None:
    """Save/merge config to ~/.agentgrounds/config.json."""
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    existing = _load_config()
    existing.update(data)
    _CONFIG_FILE.write_text(json.dumps(existing, indent=2))
