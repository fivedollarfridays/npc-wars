"""Effect, ability, and terrain feed formatters."""
from __future__ import annotations

from collections.abc import Callable

# ANSI escape codes
_RST = "\033[0m"
_DIM = "\033[2m"
_RED = "\033[31m"
_YELLOW = "\033[33m"
_BLUE = "\033[34m"
_PURPLE = "\033[35m"
_CYAN = "\033[36m"

_Formatter = Callable[[dict, int], str]


def _fmt_plague(evt: dict, rnd: int) -> str:
    dmg = evt.get("hp_damage", 0)
    rounds = evt.get("passive_rounds", 0)
    return (
        f"  {_PURPLE}R{rnd}:{_RST} {evt.get('emoji', '?')} "
        f"\U0001f9a0 plague! {_RED}-{dmg}hp{_RST} {_DIM}(idle {rounds}rd){_RST}"
    )


def _fmt_trap_placed(evt: dict, rnd: int) -> str:
    return f"  {_YELLOW}R{rnd}:{_RST} {evt.get('emoji', '?')} \U0001fa64 trap set"


def _fmt_trap_trigger(evt: dict, rnd: int) -> str:
    return (
        f"  {_RED}R{rnd}:{_RST} {evt.get('victim', '?')} "
        f"\U0001f4a5 hit {evt.get('owner', '?')}'s trap! "
        f"{_RED}-{evt.get('damage', '?')}hp{_RST}"
    )


def _fmt_tactical_activate(evt: dict, rnd: int) -> str:
    return (
        f"  {_CYAN}R{rnd}:{_RST} {evt.get('emoji', '?')} "
        f"\u26a1 {evt.get('tactical', '?')}! {evt.get('effect', '')}"
    )


def _fmt_ability_damage(evt: dict, rnd: int) -> str:
    return (
        f"  {_PURPLE}R{rnd}:{_RST} {evt.get('emoji', '?')} "
        f"\U0001f52e {evt.get('ability', '?')} \u2192 "
        f"{evt.get('target', '?')} {_RED}-{evt.get('damage', '?')}hp{_RST}"
    )


def _fmt_ability_heal(evt: dict, rnd: int) -> str:
    healed = evt.get("healed", 0)
    display = int(healed) if isinstance(healed, float) and healed == int(healed) else healed
    return (
        f"  {_CYAN}R{rnd}:{_RST} {evt.get('emoji', '?')} "
        f"\U0001f49a {evt.get('ability', '?')} +{display}hp"
    )


def _fmt_ability_shield(evt: dict, rnd: int) -> str:
    return (
        f"  {_BLUE}R{rnd}:{_RST} {evt.get('emoji', '?')} "
        f"\U0001f6e1\ufe0f {evt.get('ability', '?')} +{evt.get('dr', '?')} DR"
    )


def _fmt_ability_slow(evt: dict, rnd: int) -> str:
    return (
        f"  {_YELLOW}R{rnd}:{_RST} {evt.get('emoji', '?')} "
        f"\U0001f40c {evt.get('ability', '?')} \u2192 "
        f"{evt.get('target', '?')} -{evt.get('slow', '?')} init"
    )


def _fmt_evolve(evt: dict, rnd: int) -> str:
    return (
        f"  {_PURPLE}R{rnd}:{_RST} {evt.get('emoji', '?')} "
        f"\U0001f9ec evolved!"
    )


def _fmt_wall_blocked(evt: dict, rnd: int) -> str:
    return (
        f"  {_DIM}R{rnd}:{_RST} {evt.get('emoji', '?')} "
        f"blocked by wall"
    )


def _fmt_crystal_pickup(evt: dict, rnd: int) -> str:
    energy = evt.get("energy", "?")
    return (
        f"  {_PURPLE}R{rnd}:{_RST} {evt.get('emoji', '?')} "
        f"\u2728 crystal! +{energy} energy"
    )


def _fmt_terrain_blocked(evt: dict, rnd: int) -> str:
    return (
        f"  {_DIM}R{rnd}:{_RST} {evt.get('attacker', '?')} "
        f"\U0001f3f9 blocked by wall"
    )


def _fmt_water_penalty(evt: dict, rnd: int) -> str:
    cost = evt.get("cost", "?")
    return (
        f"  {_BLUE}R{rnd}:{_RST} {evt.get('emoji', '?')} "
        f"\U0001f30a water! -{cost} energy"
    )


EFFECT_FORMATTERS: dict[str, _Formatter] = {
    "plague": _fmt_plague,
    "trap_placed": _fmt_trap_placed,
    "trap_trigger": _fmt_trap_trigger,
    "tactical_activate": _fmt_tactical_activate,
    "ability_damage": _fmt_ability_damage,
    "ability_heal": _fmt_ability_heal,
    "ability_shield": _fmt_ability_shield,
    "ability_slow": _fmt_ability_slow,
    "evolve": _fmt_evolve,
    "wall_blocked": _fmt_wall_blocked,
    "crystal_pickup": _fmt_crystal_pickup,
    "terrain_blocked": _fmt_terrain_blocked,
    "water_penalty": _fmt_water_penalty,
}
