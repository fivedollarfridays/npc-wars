"""ANSI terminal renderer for NPC Wars match playback."""
from __future__ import annotations

from agentgrounds.wars.cli.feed import format_feed_event as _format_feed_event
from agentgrounds.wars.cli.glyph_render import render_glyph as _render_glyph
from engine.momentum import TIER_ENERGY_DRAIN

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
    "melee": "\U0001f4a5",
    "ranged": "\U0001f3f9",
    "miss": "\U0001f4a8",
    "kill": "\U0001f480\U0001f525",
    "defend_block": "\U0001f6e1\ufe0f\u2728",
    "default": "\U0001f4a5",
}
DEFEND_FX = "\U0001f6e1\ufe0f"

_COMBAT_EVENT_TYPES = frozenset({"hit", "miss", "ranged_hit", "ranged_miss", "defend"})

_TIER_LABELS: dict[int, str] = {
    1: f"{_CYAN}\u26a1MOMENTUM{_RST}",
    2: f"{_YELLOW}\u26a1BATTLE FURY{_RST}",
    3: f"{_RED}\U0001f525CROWD FAVORITE{_RST}",
    4: f"{_BOLD}{_PURPLE}\U0001f48eUNSTOPPABLE{_RST}",
}


class TerminalRenderer:
    """Renders NPC Wars match frames as ANSI-colored terminal output."""

    def __init__(self, players: list[dict], grid_size: int) -> None:
        self._players: dict[str, str] = {p["emoji"]: p["name"] for p in players}
        for p in players:
            if "glyph" in p:
                self._players[p["glyph"]] = p["name"]
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
        from agentgrounds.wars.cli.overlay import build_aura_overlay

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

        aura = build_aura_overlay(positions, self._grid_size, storm)
        lines.extend(self._title_bar(rnd, storm))
        lines.append("")
        lines.extend(self._grid(positions, storm, overlay=aura or None))
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
        from agentgrounds.wars.cli.overlay import build_aura_overlay, build_combat_overlay

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

        # Aura first, then combat FX overwrites (combat takes priority)
        aura = build_aura_overlay(positions, self._grid_size, storm)
        combat = build_combat_overlay(positions, events)
        overlay = {**aura, **combat}

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
        pos_map = {}
        for p in positions:
            if p["alive"]:
                glyph = p.get("glyph", p["emoji"])
                pos_map[(p["x"], p["y"])] = _render_glyph(
                    glyph, p.get("hp", 100), p.get("max_hp", 100),
                )
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
            score = p.get("score", 0)
            tier = p.get("momentum_tier", 0)
            tier_label = _TIER_LABELS.get(tier, "")
            is_leader = p.get("is_leader", False)
            glyph = p.get("glyph", p["emoji"])
            hp = max(0, p.get("hp", 0))
            max_hp = p.get("max_hp", 100)
            colored_glyph = _render_glyph(glyph, hp, max_hp)
            emoji_display = f"\U0001f451{colored_glyph}" if is_leader else colored_glyph
            if not p["alive"]:
                tail = f"  [{score} pts]"
                if tier_label:
                    tail += f" {tier_label}"
                lines.append(f"  {_DIM}{emoji_display} {name:<12} ELIMINATED{_RST}{tail}")
                continue
            energy = max(0, p.get("energy", 0))
            hp_bar = self._hp_bar(hp, max_hp=max_hp)
            tail = f"  [{score} pts]"
            if tier_label:
                tail += f" {tier_label}"
            drain = TIER_ENERGY_DRAIN.get(tier, 0)
            if drain > 0:
                tail += f"  \u26a1-{drain}/rd"
            lines.append(
                f"  {emoji_display} {name:<12} {hp_bar} {hp:>3}hp  \u26a1{energy}{tail}"
            )
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
    def _hp_bar(hp: int, width: int = 10, max_hp: int = 100) -> str:
        effective_max = max(1, max_hp)
        filled = max(0, min(width, int(hp / effective_max * width)))
        empty = width - filled
        pct = hp / effective_max
        if pct > 0.5:
            color = _GREEN
        elif pct > 0.25:
            color = _YELLOW
        else:
            color = _RED
        return f"{color}{'\u2588' * filled}{_RST}{'\u2591' * empty}"
