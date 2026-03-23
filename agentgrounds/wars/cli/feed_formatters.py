"""Feed formatter registry — hub merging combat and effect formatters."""
from __future__ import annotations

from collections.abc import Callable

from .feed_fmt_combat import COMBAT_FORMATTERS
from .feed_fmt_effects import EFFECT_FORMATTERS

_Formatter = Callable[[dict, int], str]

FORMATTERS: dict[str, _Formatter] = {**COMBAT_FORMATTERS, **EFFECT_FORMATTERS}
