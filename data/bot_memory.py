"""Per-bot memory persistence.

Stores and loads per-bot memory dicts as JSON files in a configurable
directory. Filenames use an MD5 hash of the emoji to stay filesystem-safe.
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any

_log = logging.getLogger(__name__)

DEFAULT_MEMORY_DIR: str = "data/bot_memory"
MAX_MEMORY_BYTES: int = 10_240  # 10 KB per bot


class MemoryLimitExceeded(ValueError):
    """Raised when serialized bot memory exceeds MAX_MEMORY_BYTES."""


def _emoji_hash(emoji: str) -> str:
    """Return a 12-char hex hash of *emoji* for use as a filename stem."""
    return hashlib.md5(emoji.encode()).hexdigest()[:12]


def load_bot_memory(emoji: str, memory_dir: str = DEFAULT_MEMORY_DIR) -> dict[str, Any]:
    """Load a single bot's memory dict from disk.

    Returns an empty dict if the file or directory does not exist.
    """
    path = Path(memory_dir) / f"{_emoji_hash(emoji)}.json"
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    # Envelope format: {"_emoji": "...", "data": {...}}
    if isinstance(raw, dict) and "data" in raw and "_emoji" in raw:
        return dict(raw["data"])
    # Fallback for plain dicts (forward compatibility)
    return dict(raw)


def _envelope_size(emoji: str, memory: dict[str, Any]) -> int:
    """Return the UTF-8 byte size of the JSON envelope for *memory*."""
    return len(json.dumps({"_emoji": emoji, "data": memory}, indent=2).encode("utf-8"))


def _truncate_if_needed(emoji: str, memory: dict[str, Any]) -> dict[str, Any]:
    """Remove oldest keys until the envelope fits within MAX_MEMORY_BYTES.

    Returns a (possibly smaller) copy of *memory*.  Raises
    :class:`MemoryLimitExceeded` if even a single remaining key exceeds
    the limit.
    """
    if _envelope_size(emoji, memory) <= MAX_MEMORY_BYTES:
        return memory

    # Work on a copy so caller's dict is not mutated
    trimmed = dict(memory)
    keys = list(trimmed.keys())  # insertion order (oldest first)

    for key in keys:
        if _envelope_size(emoji, trimmed) <= MAX_MEMORY_BYTES:
            break
        _log.warning(
            "Truncating memory key %r for bot %s to stay under %d bytes",
            key, emoji, MAX_MEMORY_BYTES,
        )
        del trimmed[key]

    if _envelope_size(emoji, trimmed) > MAX_MEMORY_BYTES or (
        not trimmed and memory
    ):
        raise MemoryLimitExceeded(
            f"Bot memory for {emoji} is {_envelope_size(emoji, memory)} bytes "
            f"(limit: {MAX_MEMORY_BYTES}) even after truncation"
        )
    return trimmed


def save_bot_memory(
    emoji: str, memory: dict[str, Any], memory_dir: str = DEFAULT_MEMORY_DIR
) -> None:
    """Serialize *memory* to JSON and write to disk.

    Creates parent directories if they do not exist.  The memory dict
    is wrapped in an envelope that stores the emoji alongside the data
    so :func:`load_all_memories` can reconstruct the emoji key.

    Raises :class:`MemoryLimitExceeded` if the serialized JSON exceeds
    :data:`MAX_MEMORY_BYTES`.
    """
    memory = _truncate_if_needed(emoji, memory)
    envelope = {"_emoji": emoji, "data": memory}
    payload = json.dumps(envelope, indent=2)
    directory = Path(memory_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{_emoji_hash(emoji)}.json"
    path.write_text(payload, encoding="utf-8")


def clear_all_memory(memory_dir: str = DEFAULT_MEMORY_DIR) -> int:
    """Delete all ``.json`` memory files in *memory_dir*.

    Returns the number of files deleted. Returns 0 if the directory
    does not exist.
    """
    directory = Path(memory_dir)
    if not directory.is_dir():
        return 0
    count = 0
    for path in directory.glob("*.json"):
        path.unlink()
        count += 1
    return count


def load_all_memories(
    memory_dir: str = DEFAULT_MEMORY_DIR,
) -> dict[str, dict[str, Any]]:
    """Load every bot memory file in *memory_dir*.

    Returns a dict mapping emoji -> memory dict.  Files without a
    valid ``_emoji`` envelope key are skipped.
    """
    directory = Path(memory_dir)
    if not directory.is_dir():
        return {}
    result: dict[str, dict[str, Any]] = {}
    for path in directory.glob("*.json"):
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, dict) and "_emoji" in raw and "data" in raw:
            result[raw["_emoji"]] = dict(raw["data"])
    return result


__all__ = [
    "DEFAULT_MEMORY_DIR",
    "MAX_MEMORY_BYTES",
    "MemoryLimitExceeded",
    "clear_all_memory",
    "load_all_memories",
    "load_bot_memory",
    "save_bot_memory",
]
