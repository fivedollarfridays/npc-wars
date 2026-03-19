"""Kill-feed event formatting for the terminal renderer."""
from __future__ import annotations

from collections.abc import Callable

__all__ = ["format_feed_event"]

# ANSI escape codes (subset needed for feed display)
_RST = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_RED = "\033[31m"
_YELLOW = "\033[33m"
_BLUE = "\033[34m"
_PURPLE = "\033[35m"
_CYAN = "\033[36m"


def format_feed_event(evt: dict, rnd: int) -> str | None:
    """Format a single event into a kill-feed line, or None if unrecognised."""
    etype = evt.get("type")
    formatter = _FORMATTERS.get(etype)
    if formatter is not None:
        return formatter(evt, rnd)
    return None


def _fmt_hit(evt: dict, rnd: int) -> str:
    crit = " CRIT!" if evt.get("is_crit") else ""
    dodge = " (glancing)" if evt.get("dodged") else ""
    return (
        f"  {_RED}R{rnd}:{_RST} {evt['attacker']} \u2192 "
        f"{evt['target']} \U0001f4a5{crit}{dodge} {_RED}-{evt.get('damage', '?')}hp{_RST}"
    )


def _fmt_kill(evt: dict, rnd: int) -> str:
    return (
        f"  {_RED}{_BOLD}R{rnd}: {evt.get('attacker', '?')} "
        f"\U0001f480\U0001f525 eliminated {evt.get('victim', '?')}{_RST}"
    )


def _fmt_bump(evt: dict, rnd: int) -> str:
    return (
        f"  {_YELLOW}R{rnd}:{_RST} "
        f"{evt.get('pusher', '?')} bumped {evt.get('target', '?')}"
    )


def _fmt_miss(evt: dict, rnd: int) -> str:
    return (
        f"  {_DIM}R{rnd}:{_RST} {evt.get('attacker', '?')} "
        f"\U0001f4a8 missed {evt.get('direction', '?')}"
    )


def _fmt_ranged_hit(evt: dict, rnd: int) -> str:
    crit = " CRIT!" if evt.get("is_crit") else ""
    dodge = " (glancing)" if evt.get("dodged") else ""
    return (
        f"  {_RED}R{rnd}:{_RST} {evt.get('attacker', '?')} \U0001f3f9 "
        f"{evt.get('target', '?')}{crit}{dodge} {_RED}-{evt.get('damage', '?')}hp{_RST}"
    )


def _fmt_ranged_miss(evt: dict, rnd: int) -> str:
    return (
        f"  {_DIM}R{rnd}:{_RST} {evt.get('attacker', '?')} "
        f"\U0001f3f9 missed {evt.get('direction', '?')}"
    )


def _fmt_defend(evt: dict, rnd: int) -> str:
    blocked = evt.get("blocked", False)
    if blocked:
        return (
            f"  {_BLUE}R{rnd}:{_RST} {evt.get('emoji', '?')} "
            f"\U0001f6e1\ufe0f blocked! \u2728"
        )
    return (
        f"  {_BLUE}R{rnd}:{_RST} {evt.get('emoji', '?')} "
        f"\U0001f6e1\ufe0f defending"
    )


def _fmt_dash(evt: dict, rnd: int) -> str:
    return f"  {_CYAN}R{rnd}:{_RST} {evt.get('emoji', '?')} dashed"


def _fmt_wall_splat(evt: dict, rnd: int) -> str:
    dmg = evt.get("damage", 10)
    return (
        f"  {_YELLOW}R{rnd}:{_RST} {evt.get('target', '?')} "
        f"wall splat! {_RED}-{dmg}hp{_RST}"
    )


def _fmt_storm_bounce(evt: dict, rnd: int) -> str:
    dmg = evt.get("damage", 10)
    return (
        f"  {_PURPLE}R{rnd}:{_RST} {evt.get('target', '?')} "
        f"storm bounce {_RED}-{dmg}hp{_RST}"
    )


def _fmt_taunt(evt: dict, rnd: int) -> str:
    targets = ", ".join(evt.get("affected", []))
    return (
        f"  {_YELLOW}R{rnd}:{_RST} {evt.get('taunter', '?')} "
        f"taunted {targets}"
    )


def _fmt_attack_miss(evt: dict, rnd: int) -> str:
    return (
        f"  {_DIM}R{rnd}:{_RST} {evt.get('attacker', '?')} \u2192 "
        f"{evt.get('target', '?')} \U0001f4a8 dodged"
    )


def _fmt_ranged_attack_miss(evt: dict, rnd: int) -> str:
    return (
        f"  {_DIM}R{rnd}:{_RST} {evt.get('attacker', '?')} \U0001f3f9 "
        f"{evt.get('target', '?')} \U0001f4a8 dodged"
    )


_Formatter = Callable[[dict, int], str]

def _fmt_leader_bounty(evt: dict, rnd: int) -> str:
    return (
        f"  {_RED}{_BOLD}R{rnd}: {evt.get('killer', '?')} "
        f"\U0001f451 REGICIDE! eliminated leader {evt.get('victim', '?')} "
        f"+{evt.get('bonus', 20)}pts{_RST}"
    )


_FORMATTERS: dict[str, _Formatter] = {
    "hit": _fmt_hit,
    "kill": _fmt_kill,
    "bump": _fmt_bump,
    "miss": _fmt_miss,
    "ranged_hit": _fmt_ranged_hit,
    "ranged_miss": _fmt_ranged_miss,
    "defend": _fmt_defend,
    "dash": _fmt_dash,
    "wall_splat": _fmt_wall_splat,
    "storm_bounce": _fmt_storm_bounce,
    "taunt": _fmt_taunt,
    "leader_bounty": _fmt_leader_bounty,
    "attack_miss": _fmt_attack_miss,
    "ranged_attack_miss": _fmt_ranged_attack_miss,
}
