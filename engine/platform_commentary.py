"""Platform commentary contract — game-agnostic commentary interface.

CommentaryLine is the shared dataclass that both Kill Switch and Code Circuit
commentary functions return.  Episode generator and highlight extractor consume
``list[CommentaryLine]`` without knowing which game produced it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

__all__ = [
    "CommentaryLine",
    "CommentaryContract",
    "VALID_TONES",
    "VALID_LINE_TYPES",
]

VALID_TONES: set[str] = {"calm", "heating", "intense", "hype", "chaos"}
VALID_LINE_TYPES: set[str] = {"play_by_play", "color", "analysis"}


@dataclass(frozen=True)
class CommentaryLine:
    """A single line of commentary output from either game."""

    timestamp: float
    text: str
    tone: str  # one of VALID_TONES
    line_type: str  # one of VALID_LINE_TYPES


@runtime_checkable
class CommentaryContract(Protocol):
    """Structural protocol for any game's commentary generator."""

    def generate_commentary(self, **kwargs: Any) -> list[CommentaryLine]: ...
