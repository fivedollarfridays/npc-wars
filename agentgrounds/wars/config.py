"""Configuration reader for agentgrounds.toml."""
from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

__all__ = ["CONFIG_FILENAME", "default_config", "load_config", "write_default_config"]

CONFIG_FILENAME = "agentgrounds.toml"


def default_config() -> dict[str, Any]:
    """Return default configuration values."""
    return {
        "bots_dir": "bots",
        "replays_dir": "replays",
        "seed": None,
    }


def load_config(path: Path) -> dict[str, Any]:
    """Load config from TOML file, merging with defaults."""
    defaults = default_config()
    if not path.is_file():
        return defaults
    with open(path, "rb") as f:
        data = tomllib.load(f)
    for key in defaults:
        if key in data:
            defaults[key] = data[key]
    return defaults


_DEFAULT_TOML = """\
# Agent Grounds configuration
# See: https://github.com/fivedollarfridays/npc-wars

# Directory containing bot files
bots_dir = "bots"

# Directory for match replay files
replays_dir = "replays"

# Random seed (uncomment for deterministic matches)
# seed = 42
"""


def write_default_config(path: Path) -> None:
    """Write a default agentgrounds.toml config file."""
    path.write_text(_DEFAULT_TOML, encoding="utf-8")
