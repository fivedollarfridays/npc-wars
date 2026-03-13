#!/usr/bin/env python3
"""Run a match and prep the viewer. Usage: python3 play.py [seed]"""

import sys
import os
import shutil
import http.server

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.loader import load_bots
from engine.game import run_match
from engine.match_writer import write_match


def get_next_match_id(results_dir):
    if not os.path.exists(results_dir):
        return 1
    files = [f for f in os.listdir(results_dir) if f.startswith("match_") and f.endswith(".json")]
    if not files:
        return 1
    ids = [int(f.replace("match_", "").replace(".json", "")) for f in files]
    return max(ids) + 1


def _print_match_result(match_data: dict, filepath: str, viewer_match: str) -> None:
    winner = match_data["winner"]
    duration = match_data["duration_rounds"]
    player = next((p for p in match_data["players"] if p["emoji"] == winner), None)
    print(f"🏆 WINNER: {winner} {player['name'] if player else ''}")
    print(f"⏱️  {duration} rounds\n")
    print("💀 Kill Feed:")
    for elim in match_data["eliminations"]:
        print(f"   R{elim['round']}: {elim.get('killed_by', '?')} → {elim['emoji']} ({elim['cause']})")
    print(f"\n📁 Match saved: {filepath}")
    print(f"📺 Viewer: open viewer/match.html and load {viewer_match}")


def _start_viewer_server(project_dir: str, match_id: int) -> None:
    print("\n🌐 Starting local server...")
    os.chdir(project_dir)
    handler = http.server.SimpleHTTPRequestHandler
    httpd = http.server.HTTPServer(("", 8080), handler)
    url = f"http://localhost:8080/viewer/match.html?match=match_{match_id:03d}.json"
    print(f"   {url}")
    print("   Ctrl+C to stop\n")
    httpd.serve_forever()


def main() -> None:
    project_dir = os.path.dirname(os.path.abspath(__file__))
    bots_dir = os.path.join(project_dir, "bots")
    results_dir = os.path.join(project_dir, "results")
    viewer_dir = os.path.join(project_dir, "viewer")

    seed = int(sys.argv[1]) if len(sys.argv) > 1 else None
    match_id = get_next_match_id(results_dir)

    print("🎮 NPC Wars — Loading bots...")
    bot_configs = load_bots(bots_dir)
    print(f"   Loaded {len(bot_configs)} bots:")
    for b in bot_configs:
        print(f"   {b['emoji']} {b['name']} — {b['bio']}")

    if len(bot_configs) < 2:
        print("❌ Need at least 2 bots!")
        return

    print(f"\n⚔️  MATCH #{match_id} — {len(bot_configs)} bots locked in\n")

    match_data = run_match(bot_configs, match_id=match_id, seed=seed)
    filepath = write_match(match_data, results_dir)

    viewer_match = os.path.join(viewer_dir, f"match_{match_id:03d}.json")
    shutil.copy2(filepath, viewer_match)

    _print_match_result(match_data, filepath, viewer_match)
    _start_viewer_server(project_dir, match_id)


if __name__ == "__main__":
    main()
