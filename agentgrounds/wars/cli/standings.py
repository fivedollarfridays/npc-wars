"""Post-match standings and final roster rendering."""
from __future__ import annotations

from collections.abc import Callable

__all__ = ["build_standings", "build_final_roster"]

# ANSI codes (subset needed for standings display)
_RST = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RED = "\033[31m"


def build_standings(
    match_data: dict, player_names: dict[str, str],
) -> str:
    """Build a final standings table string from match data."""
    winner = match_data.get("winner", "")
    eliminations = match_data.get("eliminations", [])
    stats = match_data.get("stats", {})
    duration = match_data.get("duration_rounds", 0)

    placed = _placement_order(winner, eliminations)

    lines = [f"  {_BOLD}Final Standings{_RST}"]
    for i, emoji in enumerate(placed, 1):
        name = player_names.get(emoji, "???")
        st = stats.get(emoji, {})
        kills = st.get("kills", 0)
        dmg = st.get("damage_dealt", 0)

        if emoji == winner:
            detail = f"Survived {duration} rounds"
        else:
            elim_round = _elim_round(eliminations, emoji)
            detail = f"Eliminated R{elim_round}" if elim_round else "Eliminated"

        lines.append(
            f"  {_DIM}{i}.{_RST} {emoji} {name:<12} "
            f"K:{kills}  Dmg:{dmg}  {detail}"
        )
    lines.append("")
    return "\n".join(lines)


def build_final_roster(
    positions: list[dict],
    winner_emoji: str,
    player_names: dict[str, str],
    hp_bar_fn: Callable[[int], str],
) -> list[str]:
    """Roster with the winner highlighted in bold gold."""
    lines = [f"  {_BOLD}Combatants{_RST}"]
    for p in positions:
        name = player_names.get(p["emoji"], "???")
        if p["emoji"] == winner_emoji:
            hp = max(0, p.get("hp", 0))
            energy = max(0, p.get("energy", 0))
            hp_bar = hp_bar_fn(hp)
            lines.append(
                f"  {_BOLD}{_YELLOW}{p['emoji']} {name:<12}{_RST} "
                f"{hp_bar} {hp:>3}hp  \u26a1{energy}  "
                f"{_BOLD}{_YELLOW}WINNER{_RST}"
            )
        elif not p["alive"]:
            lines.append(f"  {_DIM}{p['emoji']} {name:<12} ELIMINATED{_RST}")
        else:
            hp = max(0, p.get("hp", 0))
            energy = max(0, p.get("energy", 0))
            hp_bar = hp_bar_fn(hp)
            lines.append(f"  {p['emoji']} {name:<12} {hp_bar} {hp:>3}hp  \u26a1{energy}")
    return lines


def _placement_order(winner: str, eliminations: list[dict]) -> list[str]:
    """Winner first, then reverse elimination order."""
    placed: list[str] = []
    if winner and winner != "none":
        placed.append(winner)
    for elim in reversed(eliminations):
        emoji = elim["emoji"]
        if emoji not in placed:
            placed.append(emoji)
    return placed


def _elim_round(eliminations: list[dict], emoji: str) -> int | None:
    """Find the round a bot was eliminated in."""
    for elim in eliminations:
        if elim["emoji"] == emoji:
            return elim.get("round")
    return None
