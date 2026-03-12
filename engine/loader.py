"""Load bot modules from the bots/ directory."""

import importlib.util
import os
import sys


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

        filepath = os.path.join(bots_dir, filename)

        try:
            spec = importlib.util.spec_from_file_location(
                f"bot_{filename[:-3]}", filepath
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Validate required attributes
            name = getattr(module, "BOT_NAME", None)
            emoji = getattr(module, "BOT_EMOJI", None)
            bio = getattr(module, "BOT_BIO", "")
            author = getattr(module, "BOT_AUTHOR", "unknown")
            decide = getattr(module, "decide", None)

            if not name or not emoji or not callable(decide):
                print(f"WARNING: Skipping {filename} — missing required attributes")
                continue

            bots.append({
                "name": name,
                "emoji": emoji,
                "bio": bio,
                "author": author,
                "decide_func": decide,
            })

        except Exception as e:
            print(f"WARNING: Failed to load {filename}: {e}")
            continue

    return bots
