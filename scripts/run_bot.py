#!/usr/bin/env python3
"""Discord bot launcher — loads config, wires commands, runs NpcWarsBot."""

import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _PROJECT_ROOT)

from discord_bot.bot import BotDeps, NpcWarsBot  # noqa: E402
from discord_bot.config import load_config  # noqa: E402
from data.emoji_claims import load_claims  # noqa: E402

_DEFAULT_RESULTS_DIR = os.path.join(_PROJECT_ROOT, "results")
_DEFAULT_BOTS_DIR = os.path.join(_PROJECT_ROOT, "bots")
_DEFAULT_CLAIMS_PATH = os.path.join(_PROJECT_ROOT, "data", "claims.json")


def create_bot(
    config: dict,
    results_dir: str,
    claims_state: dict,
    claims_path: str | None = None,
    bots_dir: str = "bots",
) -> NpcWarsBot:
    """Create an NpcWarsBot with all dependencies wired."""
    deps = BotDeps(
        results_dir=results_dir,
        bots_dir=bots_dir,
        claims_state=claims_state,
        claims_path=claims_path,
    )
    return NpcWarsBot(config, deps=deps)


def main() -> None:
    """Load config, load claims from disk, create bot, and run."""
    config = load_config()
    claims_path = os.environ.get("CLAIMS_PATH", _DEFAULT_CLAIMS_PATH)
    results_dir = os.environ.get("RESULTS_DIR", _DEFAULT_RESULTS_DIR)
    bots_dir = os.environ.get("BOTS_DIR", _DEFAULT_BOTS_DIR)
    claims_state = load_claims(claims_path)
    bot = create_bot(
        config, results_dir=results_dir, claims_state=claims_state,
        claims_path=claims_path, bots_dir=bots_dir,
    )
    bot.run(config["bot_token"])


if __name__ == "__main__":
    main()
