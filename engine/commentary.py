"""Commentary engine — generates play-by-play and color commentary from match data.

Consumes round-by-round match data, personality profiles, rivalry stats,
and spectacle data to produce commentary lines with timing and tone markers.
"""

from __future__ import annotations

import random
from typing import Any

from engine.commentary_templates import COLOR_COMMENTARY, PLAY_BY_PLAY, TONE_MODIFIERS
from engine.platform_commentary import CommentaryLine
from engine.spectacle import SpectacleEngine

__all__ = ["CommentaryLine", "generate_commentary"]

_TIERS = ("calm", "heating", "intense", "hype", "chaos")
_ABILITY_ACTIONS = frozenset(("battle_cry", "fortify", "teleport", "overdrive"))
_ACTION_CATEGORIES: dict[str, str] = {
    "attack": "attack", "ranged_attack": "ranged_attack",
    "defend": "defend", "trap": "trap", "dash": "dash",
    "move": "move", "rest": "rest",
}


def generate_commentary(
    match_data: dict[str, Any],
    profiles: dict[str, dict[str, Any]],
    rivalries: dict[tuple[str, str], dict[str, Any]],
) -> list[CommentaryLine]:
    """Generate commentary for an entire match.

    Returns a list of CommentaryLine ordered by round.
    """
    engine = SpectacleEngine()
    lines: list[CommentaryLine] = []
    rounds = match_data.get("rounds", [])
    stats = match_data.get("stats", {})
    eliminations = match_data.get("eliminations", [])
    elim_by_round = _index_eliminations(eliminations, rounds)

    for rnd in rounds:
        round_num = rnd.get("round", 0)
        positions = rnd.get("positions", [])
        events = rnd.get("events", [])
        bots = [_pos_to_bot(p) for p in positions]

        spectacle = engine.score_round(events, bots)
        tone = spectacle.tier

        # Play-by-play from events
        lines.extend(_event_commentary(round_num, events, tone, positions))

        # Play-by-play from actions
        lines.extend(_action_commentary(round_num, positions, tone, stats))

        # Near-death callouts
        for p in positions:
            if p.get("alive") and 0 < p.get("hp", 999) < 5:
                lines.append(_pbp(round_num, "near_death", tone, bot=p["emoji"]))

        # Color commentary
        lines.extend(
            _color_commentary(round_num, events, positions, tone, profiles, rivalries, stats, elim_by_round),
        )

    # Match closer
    winner = match_data.get("winner")
    if winner and rounds:
        last_round = rounds[-1].get("round", len(rounds))
        tone = "hype"
        lines.append(_color(last_round, "closer", tone, bot=winner))

    return lines


# --- internal helpers ---


def _index_eliminations(
    eliminations: list[dict[str, Any]],
    rounds: list[dict[str, Any]],
) -> dict[int, list[dict[str, Any]]]:
    """Index eliminations by round number."""
    by_round: dict[int, list[dict[str, Any]]] = {}
    for elim in eliminations:
        rnum = elim.get("round", 0)
        by_round.setdefault(rnum, []).append(elim)
    return by_round


def _pos_to_bot(pos: dict[str, Any]) -> dict[str, Any]:
    return {"emoji": pos.get("emoji", "?"), "hp": pos.get("hp", 0), "alive": pos.get("alive", True)}


def _event_commentary(
    round_num: int,
    events: list[dict[str, Any]],
    tone: str,
    positions: list[dict[str, Any]],
) -> list[CommentaryLine]:
    lines: list[CommentaryLine] = []
    for evt in events:
        etype = evt.get("type", "")
        if etype == "kill":
            cause = evt.get("cause", "")
            if cause == "storm":
                lines.append(_pbp(round_num, "storm_kill", tone, victim=evt.get("victim", "?")))
            else:
                lines.append(_pbp(
                    round_num, "kill", tone,
                    attacker=evt.get("attacker", "?"), victim=evt.get("victim", "?"),
                ))
        elif etype == "kill_streak":
            lines.append(_pbp(round_num, "kill_streak", tone, attacker=evt.get("attacker", "?")))
        elif etype == "chain_bump":
            lines.append(_pbp(round_num, "chain_bump", tone))
        elif etype in ("watcher_spawn", "watcher_kill", "watcher_sync"):
            lines.append(_pbp(round_num, etype, tone))
    return lines


def _action_commentary(
    round_num: int,
    positions: list[dict[str, Any]],
    tone: str,
    stats: dict[str, Any],
) -> list[CommentaryLine]:
    lines: list[CommentaryLine] = []
    for pos in positions:
        if not pos.get("alive", True):
            continue
        action_raw = pos.get("action", "")
        parts = action_raw.split() if action_raw else []
        if not parts:
            continue
        action = parts[0]
        direction = parts[1] if len(parts) > 1 else ""
        emoji = pos["emoji"]

        if action in _ABILITY_ACTIONS:
            lines.append(_pbp(round_num, "ability", tone, bot=emoji, tactical=action))
        elif action in _ACTION_CATEGORIES:
            cat = _ACTION_CATEGORIES[action]
            lines.append(_pbp(round_num, cat, tone, bot=emoji, direction=direction))
    return lines


def _color_commentary(
    round_num: int,
    events: list[dict[str, Any]],
    positions: list[dict[str, Any]],
    tone: str,
    profiles: dict[str, dict[str, Any]],
    rivalries: dict[tuple[str, str], dict[str, Any]],
    stats: dict[str, Any],
    elim_by_round: dict[int, list[dict[str, Any]]],
) -> list[CommentaryLine]:
    lines: list[CommentaryLine] = []
    kills = [e for e in events if e.get("type") == "kill"]

    _rivalry_color(lines, round_num, tone, kills, rivalries)
    _trait_color_all(lines, round_num, tone, positions, profiles)
    _equipment_color(lines, round_num, tone, kills, positions, stats)

    if any(e.get("type", "").startswith("watcher") for e in events):
        lines.append(_color(round_num, "watcher_event", tone))
    return lines


def _rivalry_color(
    lines: list[CommentaryLine], round_num: int, tone: str,
    kills: list[dict[str, Any]],
    rivalries: dict[tuple[str, str], dict[str, Any]],
) -> None:
    for kill in kills:
        a, v = kill.get("attacker", ""), kill.get("victim", "")
        rdata = _find_rivalry(a, v, rivalries)
        if rdata:
            lines.append(_color(
                round_num, "rivalry_kill", tone,
                attacker=a, victim=v, streak=str(rdata.get("streak", 0)),
            ))


def _trait_color_all(
    lines: list[CommentaryLine], round_num: int, tone: str,
    positions: list[dict[str, Any]],
    profiles: dict[str, dict[str, Any]],
) -> None:
    for pos in positions:
        if not pos.get("alive", True):
            continue
        prof = profiles.get(pos["emoji"])
        if prof:
            _add_trait_color(
                lines, round_num, tone, pos["emoji"],
                prof.get("traits", []), prof.get("archetype_variant", ""),
            )


def _equipment_color(
    lines: list[CommentaryLine], round_num: int, tone: str,
    kills: list[dict[str, Any]],
    positions: list[dict[str, Any]], stats: dict[str, Any],
) -> None:
    if not kills and tone not in ("hype", "chaos"):
        return
    for pos in positions:
        if not pos.get("alive", True):
            continue
        eq = stats.get(pos["emoji"], {}).get("equipment", {})
        if eq.get("weapon"):
            lines.append(_color(
                round_num, "equipment_weapon", tone,
                bot=pos["emoji"], weapon=eq["weapon"],
            ))
            return


def _add_trait_color(
    lines: list[CommentaryLine],
    round_num: int,
    tone: str,
    emoji: str,
    traits: list[str],
    variant: str,
) -> None:
    trait_map = {
        "Aggressive": "trait_aggro", "Aggressive Opener": "trait_aggro",
        "Defensive": "trait_defensive", "Turtle": "trait_defensive",
        "Mobile": "trait_mobile", "Trap Obsessed": "trait_trap",
    }
    for trait in traits:
        key = trait_map.get(trait)
        if key:
            lines.append(_color(round_num, key, tone, bot=emoji, trait=trait, variant=variant))
            return  # one trait callout per bot per round


def _find_rivalry(
    a: str, b: str,
    rivalries: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any] | None:
    return rivalries.get((a, b)) or rivalries.get((b, a))


def _pbp(round_num: int, category: str, tone: str, **kwargs: str) -> CommentaryLine:
    templates = PLAY_BY_PLAY.get(category, ["{bot} acts."])
    template = random.choice(templates)
    text = _apply_tone(template.format_map(_safe_format(kwargs)), tone)
    return CommentaryLine(timestamp=round_num, text=text, tone=tone, line_type="play_by_play")


def _color(round_num: int, category: str, tone: str, **kwargs: str) -> CommentaryLine:
    templates = COLOR_COMMENTARY.get(category, ["Interesting development."])
    template = random.choice(templates)
    text = _apply_tone(template.format_map(_safe_format(kwargs)), tone)
    return CommentaryLine(timestamp=round_num, text=text, tone=tone, line_type="color")


def _apply_tone(text: str, tone: str) -> str:
    mod = TONE_MODIFIERS.get(tone, TONE_MODIFIERS["calm"])
    return f"{mod['prefix']}{text}{mod['suffix']}"


def _safe_format(kwargs: dict[str, str]) -> dict[str, str]:
    """Provide defaults so missing keys don't crash format_map."""
    defaults = {
        "attacker": "?", "victim": "?", "bot": "?", "direction": "",
        "trait": "", "rival": "?", "streak": "0", "variant": "",
        "weapon": "", "armor": "", "tactical": "",
    }
    defaults.update(kwargs)
    return defaults
