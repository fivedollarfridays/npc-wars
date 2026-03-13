"""Load bot modules from the bots/ directory."""

import importlib.util
import os
import sys


def _load_single_bot(filepath, filename):
    """Load and validate a single bot module. Returns dict or None."""
    try:
        spec = importlib.util.spec_from_file_location(f"bot_{filename[:-3]}", filepath)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception as e:
        print(f"WARNING: Failed to load {filename}: {e}")
        return None

    name = getattr(module, "BOT_NAME", None)
    emoji = getattr(module, "BOT_EMOJI", None)
    decide = getattr(module, "decide", None)

    if not name or not emoji or not callable(decide):
        print(f"WARNING: Skipping {filename} — missing required attributes")
        return None

    return {"name": name, "emoji": emoji, "bio": getattr(module, "BOT_BIO", ""),
            "author": getattr(module, "BOT_AUTHOR", "unknown"), "decide_func": decide}


def _deduplicate_emojis(bots):
    """Remove bots with duplicate emojis, keeping first seen."""
    seen = set()
    unique = []
    for bot in bots:
        if bot["emoji"] in seen:
            print(f"WARNING: Skipping {bot['name']} — duplicate emoji {bot['emoji']}")
            continue
        seen.add(bot["emoji"])
        unique.append(bot)
    return unique


def load_bots(bots_dir: str) -> list[dict]:
    """Load all bot modules from a directory.

    Returns list of dicts with keys: name, emoji, bio, author, decide_func
    """
    bots = []
    for filename in sorted(os.listdir(bots_dir)):
        if not filename.endswith(".py"):
            continue
        if filename.startswith("_") or filename == "template.py":
            continue
        bot = _load_single_bot(os.path.join(bots_dir, filename), filename)
        if bot:
            bots.append(bot)
    return _deduplicate_emojis(bots)
