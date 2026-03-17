"""ANSI terminal renderer for NPC Wars match playback."""
from __future__ import annotations

__all__ = ["TerminalRenderer"]

# ANSI escape codes
_RST = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_RED = "\033[31m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_BLUE = "\033[34m"
_PURPLE = "\033[35m"
_CYAN = "\033[36m"
_CLEAR = "\033[2J\033[H"

STORM_CHAR = "\u2593\u2593"
EMPTY_CHAR = " \u00b7"


class TerminalRenderer:
    """Renders NPC Wars match frames as ANSI-colored terminal output."""

    def __init__(self, players: list[dict], grid_size: int) -> None:
        self._players: dict[str, str] = {p["emoji"]: p["name"] for p in players}
        self._grid_size = grid_size
        self._kill_feed: list[str] = []

    def render_frame(self, round_data: dict, *, clear: bool = True) -> str:
        """Render one complete frame as an ANSI string."""
        lines: list[str] = []
        if clear:
            lines.append(_CLEAR)

        rnd = round_data["round"]
        storm = round_data.get("storm_border", 0)
        positions = round_data["positions"]
        events = round_data.get("events", [])

        lines.extend(self._title_bar(rnd, storm))
        lines.append("")
        lines.extend(self._grid(positions, storm))
        lines.append("")
        lines.extend(self._roster(positions))
        lines.append("")
        self._update_kill_feed(events, rnd)
        lines.extend(self._render_kill_feed())

        return "\n".join(lines)

    def render_winner(self, winner_emoji: str, duration: int) -> str:
        """Render the winner banner."""
        name = self._players.get(winner_emoji, "???")
        lines = [
            "",
            f"{_BOLD}{_CYAN}\u2554{'═' * 42}\u2557{_RST}",
            f"{_BOLD}{_CYAN}\u2551              \U0001f3c6  WINNER  \U0001f3c6              \u2551{_RST}",
            f"{_BOLD}{_CYAN}\u255a{'═' * 42}\u255d{_RST}",
            "",
            f"  {_BOLD}{winner_emoji} {name}{_RST}",
            f"  {_DIM}Survived {duration} rounds{_RST}",
            "",
        ]
        return "\n".join(lines)

    # -- Private helpers ------------------------------------------------

    @staticmethod
    def _title_bar(rnd: int, storm: int) -> list[str]:
        return [
            f"{_BOLD}{_CYAN}\u2554{'═' * 42}\u2557{_RST}",
            f"{_BOLD}{_CYAN}\u2551         \u2694\ufe0f  N P C   W A R S  \u2694\ufe0f          \u2551{_RST}",
            f"{_BOLD}{_CYAN}\u255a{'═' * 42}\u255d{_RST}",
            f"  {_DIM}Round {rnd} \u2502 Storm: {storm} tiles from edge{_RST}",
        ]

    def _grid(self, positions: list[dict], storm: int) -> list[str]:
        gs = self._grid_size
        pos_map = self._build_position_map(positions)

        border = f"  {_PURPLE}{STORM_CHAR * (gs + 2)}{_RST}"
        lines = [border]
        for y in range(gs):
            in_storm_row = y < storm or y >= gs - storm
            cells: list[str] = []
            for x in range(gs):
                in_storm = in_storm_row or x < storm or x >= gs - storm
                if (x, y) in pos_map:
                    cells.append(pos_map[(x, y)])
                elif in_storm:
                    cells.append(f"{_PURPLE}{STORM_CHAR}{_RST}")
                else:
                    cells.append(f"{_DIM} \u00b7{_RST}")
            lines.append(
                f"  {_PURPLE}{STORM_CHAR}{_RST}{''.join(cells)}{_PURPLE}{STORM_CHAR}{_RST}"
            )
        lines.append(border)
        return lines

    @staticmethod
    def _build_position_map(positions: list[dict]) -> dict[tuple[int, int], str]:
        pos_map: dict[tuple[int, int], str] = {}
        for p in positions:
            if p["alive"]:
                pos_map[(p["x"], p["y"])] = p["emoji"]
            else:
                pos_map[(p["x"], p["y"])] = f"{_DIM}\U0001f480{_RST}"
        return pos_map

    def _roster(self, positions: list[dict]) -> list[str]:
        lines = [f"  {_BOLD}Combatants{_RST}"]
        for p in positions:
            name = self._players.get(p["emoji"], "???")
            if not p["alive"]:
                lines.append(f"  {_DIM}{p['emoji']} {name:<12} ELIMINATED{_RST}")
                continue
            hp = max(0, p.get("hp", 0))
            energy = max(0, p.get("energy", 0))
            hp_bar = self._hp_bar(hp)
            lines.append(f"  {p['emoji']} {name:<12} {hp_bar} {hp:>3}hp  \u26a1{energy}")
        return lines

    def _update_kill_feed(self, events: list[dict], rnd: int) -> None:
        for evt in events:
            etype = evt.get("type")
            if etype == "hit":
                entry = (
                    f"  {_RED}R{rnd}:{_RST} {evt['attacker']} \u2192 "
                    f"{evt['target']} {_RED}-{evt.get('damage', '?')}hp{_RST}"
                )
                self._kill_feed.append(entry)
            elif etype == "kill":
                entry = (
                    f"  {_RED}{_BOLD}R{rnd}: {evt.get('attacker', '?')} "
                    f"eliminated {evt.get('victim', '?')}{_RST}"
                )
                self._kill_feed.append(entry)
            elif etype == "bump":
                entry = (
                    f"  {_YELLOW}R{rnd}:{_RST} "
                    f"{evt.get('pusher', '?')} bumped {evt.get('target', '?')}"
                )
                self._kill_feed.append(entry)

    def _render_kill_feed(self) -> list[str]:
        lines = [f"  {_BOLD}Kill Feed{_RST}"]
        if not self._kill_feed:
            lines.append(f"  {_DIM}No events yet{_RST}")
        else:
            for entry in self._kill_feed[-5:]:
                lines.append(entry)
        return lines

    @staticmethod
    def _hp_bar(hp: int, width: int = 10) -> str:
        filled = max(0, min(width, int(hp / 100 * width)))
        empty = width - filled
        if hp > 50:
            color = _GREEN
        elif hp > 25:
            color = _YELLOW
        else:
            color = _RED
        return f"{color}{'\u2588' * filled}{_RST}{'\u2591' * empty}"
