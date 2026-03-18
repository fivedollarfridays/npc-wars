"""ANSI terminal renderer for NPC Wars match playback."""
from __future__ import annotations

from agentgrounds.wars.cli.feed import format_feed_event as _format_feed_event

__all__ = ["TerminalRenderer", "WEAPON_FX", "DEFEND_FX"]

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
_ALT_SCREEN_ON = "\033[?1049h"
_ALT_SCREEN_OFF = "\033[?1049l"

STORM_CHAR = "\u2593\u2593"
EMPTY_CHAR = " \u00b7"

WEAPON_FX: dict[str, str] = {
    "melee": "\u2694\ufe0f",
    "ranged": "\U0001f3f9",
    "default": "\u2694\ufe0f",
}
DEFEND_FX = "\U0001f6e1\ufe0f"

_COMBAT_EVENT_TYPES = frozenset({"hit", "miss", "ranged_hit", "ranged_miss", "defend"})


class TerminalRenderer:
    """Renders NPC Wars match frames as ANSI-colored terminal output."""

    def __init__(self, players: list[dict], grid_size: int) -> None:
        self._players: dict[str, str] = {p["emoji"]: p["name"] for p in players}
        self._grid_size = grid_size
        self._kill_feed: list[str] = []
        self._first_frame = True

    def enter_alt_screen(self) -> str:
        """Enter alternate screen buffer for clean animation."""
        return _ALT_SCREEN_ON

    def exit_alt_screen(self) -> str:
        """Exit alternate screen buffer, restoring original terminal content."""
        return _ALT_SCREEN_OFF

    def render_frame(self, round_data: dict, *, clear: bool = True) -> str:
        """Render one complete frame as an ANSI string."""
        lines: list[str] = []
        if clear:
            if self._first_frame:
                lines.append(_ALT_SCREEN_ON)
                self._first_frame = False
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
        lines.extend(self._feed_lines(events, rnd))

        return "\n".join(lines)

    def render_winner(self, winner_emoji: str, duration: int) -> str:
        """Render the winner banner for normal scrollback."""
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

    def render_final_frame(
        self, round_data: dict, winner_emoji: str,
    ) -> str:
        """Render the last round with winner highlighted. Stays in alt screen."""
        from agentgrounds.wars.cli.standings import build_final_roster

        lines: list[str] = [_CLEAR]

        rnd = round_data["round"]
        storm = round_data.get("storm_border", 0)
        positions = round_data["positions"]

        lines.extend(self._title_bar(rnd, storm))
        lines.append("")
        lines.extend(self._grid(positions, storm))
        lines.append("")
        lines.extend(
            build_final_roster(positions, winner_emoji, self._players, self._hp_bar)
        )
        lines.append("")
        lines.append(
            f"  {_BOLD}{_YELLOW}\U0001f3c6  WINNER: "
            f"{winner_emoji} {self._players.get(winner_emoji, '???')}{_RST}"
        )
        return "\n".join(lines)

    def render_standings(self, match_data: dict) -> str:
        """Render final standings table for normal scrollback."""
        from agentgrounds.wars.cli.standings import build_standings

        return build_standings(match_data, self._players)

    def render_action_frame(self, round_data: dict, *, clear: bool = True) -> str:
        """Render an action-phase frame with combat FX indicators."""
        lines: list[str] = []
        if clear:
            if self._first_frame:
                lines.append(_ALT_SCREEN_ON)
                self._first_frame = False
            lines.append(_CLEAR)

        rnd = round_data["round"]
        storm = round_data.get("storm_border", 0)
        positions = round_data["positions"]
        events = round_data.get("events", [])

        from agentgrounds.wars.cli.overlay import build_combat_overlay

        overlay = build_combat_overlay(positions, events)

        lines.extend(self._title_bar(rnd, storm))
        lines.append("")
        lines.extend(self._grid(positions, storm, overlay=overlay))
        lines.append("")
        lines.extend(self._roster(positions))
        lines.append("")
        lines.extend(self._feed_lines(events, rnd))

        return "\n".join(lines)

    @staticmethod
    def has_combat_events(round_data: dict) -> bool:
        """Return True if the round contains any combat events."""
        return any(
            evt.get("type") in _COMBAT_EVENT_TYPES
            for evt in round_data.get("events", [])
        )

    # -- Private helpers ------------------------------------------------

    @staticmethod
    def _title_bar(rnd: int, storm: int) -> list[str]:
        return [
            f"{_BOLD}{_CYAN}\u2554{'═' * 42}\u2557{_RST}",
            f"{_BOLD}{_CYAN}\u2551         \u2694\ufe0f  N P C   W A R S  \u2694\ufe0f          \u2551{_RST}",
            f"{_BOLD}{_CYAN}\u255a{'═' * 42}\u255d{_RST}",
            f"  {_DIM}Round {rnd} \u2502 Storm: {storm} tiles from edge{_RST}",
        ]

    def _grid(
        self,
        positions: list[dict],
        storm: int,
        *,
        overlay: dict[tuple[int, int], str] | None = None,
    ) -> list[str]:
        gs = self._grid_size
        pos_map = {
            (p["x"], p["y"]): p["emoji"] for p in positions if p["alive"]
        }
        fx = overlay or {}

        border = f"  {_PURPLE}{STORM_CHAR * (gs + 2)}{_RST}"
        lines = [border]
        for y in range(gs):
            in_storm_row = y < storm or y >= gs - storm
            cells: list[str] = []
            for x in range(gs):
                in_storm = in_storm_row or x < storm or x >= gs - storm
                if (x, y) in pos_map and (x, y) not in fx:
                    cells.append(pos_map[(x, y)])
                elif (x, y) in fx:
                    cells.append(fx[(x, y)])
                elif in_storm:
                    cells.append(f"{_PURPLE}{STORM_CHAR}{_RST}")
                else:
                    cells.append(f"{_DIM} \u00b7{_RST}")
            lines.append(
                f"  {_PURPLE}{STORM_CHAR}{_RST}{''.join(cells)}{_PURPLE}{STORM_CHAR}{_RST}"
            )
        lines.append(border)
        return lines

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

    def _feed_lines(self, events: list[dict], rnd: int) -> list[str]:
        """Update the kill feed with new events and return display lines."""
        for evt in events:
            line = _format_feed_event(evt, rnd)
            if line is not None:
                self._kill_feed.append(line)
        lines = [f"  {_BOLD}Kill Feed{_RST}"]
        if not self._kill_feed:
            lines.append(f"  {_DIM}No events yet{_RST}")
        else:
            lines.extend(self._kill_feed[-5:])
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
