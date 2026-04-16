"""Discord match JSON submission ingestion for #submissions channel."""

from __future__ import annotations

import json
import logging
import time
import uuid
from pathlib import Path
from typing import Any

import discord

__all__ = ["validate_match_json", "handle_submission", "setup_submission_listener"]

log = logging.getLogger(__name__)

RATE_LIMIT_SECONDS = 300  # 5 minutes

_rate_limits: dict[int, float] = {}

KS_REQUIRED = {"match_id", "rounds", "stats"}
CC_REQUIRED = {"frames", "results"}


def validate_match_json(data: Any) -> tuple[bool, str | None, str | None]:
    """Validate match JSON and detect game type.

    Returns (ok, game_type, error_message).
    """
    if not isinstance(data, dict):
        return False, None, "Expected a JSON object, got %s" % type(data).__name__
    keys = set(data.keys())
    if KS_REQUIRED <= keys:
        return True, "kill_switch", None
    if CC_REQUIRED <= keys:
        return True, "code_circuit", None
    missing_ks = KS_REQUIRED - keys
    missing_cc = CC_REQUIRED - keys
    return (
        False,
        None,
        "Unrecognised match schema. "
        f"Kill Switch needs {sorted(missing_ks)}; "
        f"Code Circuit needs {sorted(missing_cc)}.",
    )


def _is_rate_limited(user_id: int) -> bool:
    last = _rate_limits.get(user_id)
    if last is None:
        return False
    return (time.monotonic() - last) < RATE_LIMIT_SECONDS


async def handle_submission(
    message: discord.Message,
    *,
    queue_dir: str,
    channel_id: int,
) -> None:
    """Process a message in the submissions channel."""
    if message.author.bot:
        return
    if message.channel.id != channel_id:
        return
    json_attachments = [a for a in message.attachments if a.filename.endswith(".json")]
    if not json_attachments:
        return

    if _is_rate_limited(message.author.id):
        await message.add_reaction("\u23f3")  # hourglass
        await message.author.send("Rate limited — 1 submission per 5 minutes.")
        return

    attachment = json_attachments[0]
    raw = await attachment.read()

    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        await message.add_reaction("\u274c")
        await message.author.send(f"Invalid JSON: {exc}")
        return

    ok, game, err = validate_match_json(data)
    if not ok:
        await message.add_reaction("\u274c")
        await message.author.send(f"Submission rejected: {err}")
        return

    # Queue the file
    out = Path(queue_dir)
    out.mkdir(parents=True, exist_ok=True)
    filename = f"{game}_{uuid.uuid4().hex[:8]}.json"
    (out / filename).write_text(json.dumps(data), encoding="utf-8")

    _rate_limits[message.author.id] = time.monotonic()
    await message.add_reaction("\u2705")  # checkmark
    log.info("Queued %s submission from user %s", game, message.author.id)


def setup_submission_listener(
    bot: discord.Client,
    *,
    channel_id: int,
    queue_dir: str = "queue/submissions",
) -> None:
    """Register the on_message listener on a bot instance."""
    original_on_message = getattr(bot, "_original_on_message", None)

    async def on_message(message: discord.Message) -> None:
        await handle_submission(message, queue_dir=queue_dir, channel_id=channel_id)
        if original_on_message:
            await original_on_message(message)

    bot._original_on_message = getattr(bot, "on_message", None)  # type: ignore[attr-defined]
    bot.on_message = on_message  # type: ignore[method-assign]
