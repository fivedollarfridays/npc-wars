"""Adaptive AI fill bots using preset strategies with skill calibration."""

from __future__ import annotations

import textwrap
from typing import Any

from npcwars.presets import PRESET_NAMES, generate_preset

__all__ = ["AI_EMOJI_POOL", "generate_fill_bots"]

AI_EMOJI_POOL: list[str] = [
    "\U0001f916",  # robot
    "\U0001f9be",  # mechanical arm
    "\u26a1",      # lightning
    "\U0001f3b2",  # die
    "\U0001f9e0",  # brain
    "\U0001f480",  # skull
    "\U0001f525",  # fire
    "\U0001f300",  # cyclone
]

_STYLES = list(PRESET_NAMES)


def generate_fill_bots(
    count: int,
    skill_level: float = 0.5,
    used_emojis: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Generate fill bot configs calibrated to a skill level.

    Args:
        count: Number of bots to generate.
        skill_level: 0.0 (easy) to 1.0 (hard), affects aggression/risk.
        used_emojis: Emojis already taken by human players.

    Returns:
        List of bot config dicts compatible with run_match().
    """
    used = set(used_emojis or [])
    available = [e for e in AI_EMOJI_POOL if e not in used]
    bots: list[dict[str, Any]] = []

    for i in range(min(count, len(available))):
        emoji = available[i]
        style = _STYLES[i % len(_STYLES)]
        aggression = max(1, min(10, int(skill_level * 10)))
        risk = max(1, min(10, int(skill_level * 8 + 1)))

        preset_body = generate_preset(style, aggression, risk)
        name = f"AI {style.title()}"
        source = _build_bot_source(name, emoji, preset_body)

        namespace: dict[str, Any] = {}
        exec(compile(source, f"<fill_bot_{i}>", "exec"), namespace)  # noqa: S102

        bots.append({
            "name": name,
            "emoji": emoji,
            "bio": f"AI fill bot ({style}, skill={skill_level:.1f})",
            "decide_func": namespace["decide"],
            "source": source,
        })

    return bots


def _build_bot_source(name: str, emoji: str, preset_body: str) -> str:
    """Build complete bot source code from a preset body."""
    return (
        f'BOT_NAME = "{name}"\n'
        f'BOT_EMOJI = "{emoji}"\n'
        f'BOT_BIO = "AI fill bot"\n'
        f"\n"
        f"def decide(state):\n"
        f"{textwrap.indent(preset_body, '    ')}\n"
    )
