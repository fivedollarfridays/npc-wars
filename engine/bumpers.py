"""Bumper physics -- collision detection, knockback, and chain resolution."""

from typing import Any

from engine.combat import Bot, WALL_SPLAT_DAMAGE, STORM_DAMAGE
from engine.grid import is_valid_position, is_in_storm

__all__ = ["resolve_bumps", "BUMP_EVENT_TYPES"]

MAX_CHAIN_DEPTH = 5
BUMP_EVENT_TYPES = frozenset({"bump", "chain_bump", "wall_splat", "storm_bounce"})

_Event = dict[str, Any]
_PosMap = dict[tuple[int, int], Bot]


def _build_pos_map(bots: list[Bot]) -> _PosMap:
    """Build position -> alive bot lookup dict."""
    return {(b.x, b.y): b for b in bots if b.alive}


def _update_pos_map(pos_map: _PosMap, bot: Bot, old_x: int, old_y: int) -> None:
    """Update pos_map after a bot moves."""
    pos_map.pop((old_x, old_y), None)
    pos_map[(bot.x, bot.y)] = bot


def _compute_push_direction(
    from_x: int, from_y: int, to_x: int, to_y: int,
) -> tuple[int, int]:
    """Compute the push direction vector (dx, dy) from movement."""
    dx = to_x - from_x
    dy = to_y - from_y
    if dx != 0:
        dx = dx // abs(dx)
    if dy != 0:
        dy = dy // abs(dy)
    return dx, dy


def _apply_wall_splat(bot: Bot) -> _Event:
    """Apply wall splat damage and return the event."""
    bot.hp -= WALL_SPLAT_DAMAGE
    bot.damage_taken += WALL_SPLAT_DAMAGE
    return {"type": "wall_splat", "target": bot.emoji, "damage": WALL_SPLAT_DAMAGE}


def _check_storm_bounce(
    bot: Bot, grid_size: int, storm_border: int,
) -> _Event | None:
    """Check if bot landed in storm; apply damage and return event or None."""
    if not is_in_storm(bot.x, bot.y, grid_size, storm_border):
        return None
    bot.hp -= STORM_DAMAGE
    bot.damage_taken += STORM_DAMAGE
    return {"type": "storm_bounce", "target": bot.emoji, "damage": STORM_DAMAGE}


def _push_bot(
    bot: Bot, dx: int, dy: int,
    pos_map: _PosMap, grid_size: int, storm_border: int,
    visited: set[str], depth: int,
) -> list[_Event]:
    """Push a bot in direction (dx, dy), handling chains, walls, and storm."""
    events: list[_Event] = []
    if depth >= MAX_CHAIN_DEPTH:
        return events

    new_x = bot.x + dx
    new_y = bot.y + dy

    if not is_valid_position(new_x, new_y, grid_size):
        events.append(_apply_wall_splat(bot))
        return events

    # Chain: another bot at destination
    occupant = pos_map.get((new_x, new_y))
    if occupant and occupant.alive and occupant.emoji not in visited:
        visited.add(occupant.emoji)
        events.extend(_push_bot(
            occupant, dx, dy, pos_map, grid_size, storm_border,
            visited, depth + 1,
        ))
        if occupant.x != new_x or occupant.y != new_y:
            old_x, old_y = bot.x, bot.y
            bot.x = new_x
            bot.y = new_y
            _update_pos_map(pos_map, bot, old_x, old_y)
        else:
            return events
    else:
        old_x, old_y = bot.x, bot.y
        bot.x = new_x
        bot.y = new_y
        _update_pos_map(pos_map, bot, old_x, old_y)

    storm_evt = _check_storm_bounce(bot, grid_size, storm_border)
    if storm_evt:
        events.append(storm_evt)
    return events


def resolve_bumps(
    movers: list[tuple[Bot, int, int]],
    all_bots: list[Bot],
    grid_size: int,
    storm_border: int,
) -> tuple[list[_Event], set[str]]:
    """Resolve bump collisions. Returns (events, blocked_mover_emojis)."""
    pos_map = _build_pos_map(all_bots)
    events: list[_Event] = []
    blocked: set[str] = set()

    for mover, new_x, new_y in movers:
        occupant = pos_map.get((new_x, new_y))
        if occupant is None or occupant is mover:
            continue

        dx, dy = _compute_push_direction(mover.x, mover.y, new_x, new_y)
        if dx == 0 and dy == 0:
            continue

        visited: set[str] = {mover.emoji, occupant.emoji}
        occupant_pos_before = (occupant.x, occupant.y)
        push_events = _push_bot(
            occupant, dx, dy, pos_map, grid_size, storm_border,
            visited, depth=1,
        )
        occupant_displaced = (occupant.x, occupant.y) != occupant_pos_before

        if push_events or occupant_displaced:
            events.append({
                "type": "bump", "pusher": mover.emoji,
                "target": occupant.emoji,
                "direction": f"({dx},{dy})",
            })
        events.extend(push_events)

        if not occupant_displaced and not push_events:
            blocked.add(mover.emoji)

    return events, blocked
