"""Main match engine for NPC Wars."""

import random
from engine.combat import (
    Bot, STORM_DAMAGE, REST_HEAL, REST_ENERGY_RESTORE, DEFEND_BONUS,
    MAX_HP, MAX_ENERGY, MAX_CONSECUTIVE_FAILURES,
    calculate_damage, resolve_deaths
)
from engine.grid import (
    calculate_grid_size, spawn_positions, get_storm_border,
    is_in_storm, is_valid_position, apply_direction
)
from engine.state import build_state
from engine.sandbox import execute_decide, validate_action
from engine.match_writer import build_match_data


MAX_ROUNDS = 200  # Safety limit


def run_match(bot_configs: list[dict], match_id: int = 1, seed: int | None = None) -> dict:
    """Run a complete match. Returns match data dict.
    
    bot_configs: list of dicts with keys: name, emoji, bio, author, decide_func
    """
    rng = random.Random(seed)
    player_count = len(bot_configs)
    grid_size = calculate_grid_size(player_count)
    positions = spawn_positions(player_count, grid_size, rng)

    # Create bot instances
    bots = []
    for i, config in enumerate(bot_configs):
        x, y = positions[i]
        bot = Bot(
            name=config["name"],
            emoji=config["emoji"],
            bio=config["bio"],
            author=config.get("author", "unknown"),
            decide_func=config["decide_func"],
            x=x,
            y=y,
        )
        bots.append(bot)

    # Player info for match data
    players = [
        {"emoji": b.emoji, "name": b.name, "bio": b.bio, "author": b.author}
        for b in bots
    ]

    all_rounds = []
    all_eliminations = []
    round_num = 0

    while round_num < MAX_ROUNDS:
        round_num += 1
        alive_bots = [b for b in bots if b.alive]

        if len(alive_bots) <= 1:
            break

        storm_border = get_storm_border(round_num)

        # --- Phase 1: All bots decide ---
        actions = {}
        forced_rest = set()
        for bot in alive_bots:
            if not bot.can_act():
                # Forced rest - heal immediately
                bot.hp = min(MAX_HP, bot.hp + REST_HEAL)
                bot.energy = min(MAX_ENERGY, bot.energy + REST_ENERGY_RESTORE)
                actions[bot.emoji] = ("rest",)
                forced_rest.add(bot.emoji)
                bot.consecutive_failures = 0
                continue

            state = build_state(bot, bots, round_num, grid_size, storm_border)
            raw_action = execute_decide(bot.decide_func, state)
            action = validate_action(raw_action)

            if action is None:
                bot.consecutive_failures += 1
                if bot.consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    bot.hp = 0  # Disconnected
                    actions[bot.emoji] = ("disconnected",)
                else:
                    actions[bot.emoji] = ("nothing",)
            else:
                bot.consecutive_failures = 0
                actions[bot.emoji] = action

        # --- Phase 2: Defend actions resolve ---
        for bot in alive_bots:
            bot.defense = 0  # Reset defense each round
            action = actions.get(bot.emoji)
            if action and action[0] == "defend":
                bot.defense = DEFEND_BONUS

        # --- Phase 3: Move actions resolve ---
        for bot in alive_bots:
            action = actions.get(bot.emoji)
            if action and action[0] == "move":
                direction = action[1]
                new_x, new_y = apply_direction(bot.x, bot.y, direction)
                if is_valid_position(new_x, new_y, grid_size):
                    bot.x = new_x
                    bot.y = new_y
                # If invalid, bot stays put but energy is still spent

        # --- Phase 4: Attack actions resolve ---
        round_events = []
        for bot in alive_bots:
            if not bot.alive:
                continue
            action = actions.get(bot.emoji)
            if action and action[0] == "attack":
                direction = action[1]
                target_x, target_y = apply_direction(bot.x, bot.y, direction)

                # Find target at that position
                for target in alive_bots:
                    if target.emoji != bot.emoji and target.alive and target.x == target_x and target.y == target_y:
                        dmg = calculate_damage(bot, target)
                        target.hp -= dmg
                        target.damage_taken += dmg
                        bot.damage_dealt += dmg

                        if dmg > 0:
                            round_events.append({
                                "type": "hit",
                                "attacker": bot.emoji,
                                "target": target.emoji,
                                "damage": dmg,
                            })
                        break
                else:
                    # Miss - no target at that tile
                    round_events.append({
                        "type": "miss",
                        "attacker": bot.emoji,
                        "direction": direction,
                    })

        # --- Phase 5: Storm damage ---
        for bot in alive_bots:
            if bot.alive and is_in_storm(bot.x, bot.y, grid_size, storm_border):
                bot.hp -= STORM_DAMAGE
                bot.damage_taken += STORM_DAMAGE
                round_events.append({
                    "type": "storm_damage",
                    "target": bot.emoji,
                    "damage": STORM_DAMAGE,
                })

        # --- Phase 6: Energy deduction ---
        for bot in alive_bots:
            action = actions.get(bot.emoji)
            if action and action[0] not in ("nothing", "disconnected") and bot.emoji not in forced_rest:
                bot.apply_action_cost(action[0])

        # --- Phase 7: Explicit rest healing ---
        for bot in alive_bots:
            action = actions.get(bot.emoji)
            if action and action[0] == "rest" and bot.emoji not in forced_rest:
                bot.hp = min(MAX_HP, bot.hp + REST_HEAL)
                bot.energy = min(MAX_ENERGY, bot.energy + REST_ENERGY_RESTORE)

        # --- Phase 8: Death checks ---
        round_elims = resolve_deaths(bots, round_num)

        # Attribute kills
        for elim in round_elims:
            # Find who dealt the killing blow this round
            killer_emoji = None
            for evt in round_events:
                if evt.get("type") == "hit" and evt.get("target") == elim["emoji"]:
                    killer_emoji = evt["attacker"]
            if killer_emoji is None:
                # Check storm
                for evt in round_events:
                    if evt.get("type") == "storm_damage" and evt.get("target") == elim["emoji"]:
                        killer_emoji = "storm"

            elim["killed_by"] = killer_emoji or "unknown"
            elim["cause"] = "storm" if killer_emoji == "storm" else "combat"

            # Credit kills to attacker
            if killer_emoji and killer_emoji != "storm":
                for b in bots:
                    if b.emoji == killer_emoji:
                        b.kills += 1

            round_events.append({
                "type": "kill",
                "attacker": killer_emoji or "unknown",
                "victim": elim["emoji"],
                "round": round_num,
            })

        all_eliminations.extend(round_elims)

        # Track survival
        for bot in alive_bots:
            if bot.alive:
                bot.rounds_survived = round_num

        # Build round record
        round_data = {
            "round": round_num,
            "storm_border": storm_border,
            "positions": [],
            "events": round_events,
        }
        for bot in bots:
            action_str = " ".join(str(a) for a in actions.get(bot.emoji, ("dead",)))
            round_data["positions"].append({
                "emoji": bot.emoji,
                "x": bot.x,
                "y": bot.y,
                "hp": bot.hp,
                "energy": bot.energy,
                "action": action_str,
                "alive": bot.alive,
            })
        all_rounds.append(round_data)

        # Check for winner
        still_alive = [b for b in bots if b.alive]
        if len(still_alive) <= 1:
            break

    # Determine winner
    still_alive = [b for b in bots if b.alive]
    winner_emoji = still_alive[0].emoji if still_alive else "none"

    # Build stats
    stats = {}
    for bot in bots:
        stats[bot.emoji] = {
            "kills": bot.kills,
            "damage_dealt": bot.damage_dealt,
            "damage_taken": bot.damage_taken,
            "rounds_survived": bot.rounds_survived,
        }

    return build_match_data(
        match_id=match_id,
        grid_size=grid_size,
        players=players,
        rounds=all_rounds,
        eliminations=all_eliminations,
        winner_emoji=winner_emoji,
        stats=stats,
        duration_rounds=round_num,
    )
