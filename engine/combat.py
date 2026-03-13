"""Combat mechanics for NPC Wars."""

from typing import Any, Callable

# Starting stats (identical for all bots)
STARTING_HP = 100
STARTING_ENERGY = 100
STARTING_ATTACK_POWER = 25
STARTING_DEFENSE = 0

# Action costs
MOVE_COST = 5
ATTACK_COST = 10
DEFEND_COST = 10
REST_COST = 0
RANGED_ATTACK_COST = 20
RANGED_ATTACK_DAMAGE = 15
TAUNT_COST = 10
DASH_COST = 15

# Rest healing
REST_HEAL = 5
REST_ENERGY_RESTORE = 20

# Defend bonus
DEFEND_BONUS = 10

ACTION_COSTS = {
    "move": MOVE_COST,
    "attack": ATTACK_COST,
    "defend": DEFEND_COST,
    "rest": REST_COST,
    "ranged_attack": RANGED_ATTACK_COST,
    "taunt": TAUNT_COST,
    "dash": DASH_COST,
}

# Storm damage
STORM_DAMAGE = 10

# Bumper physics
WALL_SPLAT_DAMAGE = 10

# Kill bounty
KILL_BOUNTY_ENERGY = 30

# Taunt range
TAUNT_RANGE = 2

# HP / Energy caps
MAX_HP = 100
MAX_ENERGY = 100

# Failure tracking
MAX_CONSECUTIVE_FAILURES = 3

# Progression defaults (single source for Bot and PlayerProfile)
DEFAULT_UNLOCKED_ACTIONS = frozenset({"move", "attack", "rest", "defend"})
DEFAULT_LINE_BUDGET = 50

__all__ = [
    "STARTING_HP", "STARTING_ENERGY", "STARTING_ATTACK_POWER", "STARTING_DEFENSE",
    "MOVE_COST", "ATTACK_COST", "DEFEND_COST", "REST_COST",
    "RANGED_ATTACK_COST", "RANGED_ATTACK_DAMAGE", "ACTION_COSTS",
    "REST_HEAL", "REST_ENERGY_RESTORE", "DEFEND_BONUS", "STORM_DAMAGE", "WALL_SPLAT_DAMAGE",
    "KILL_BOUNTY_ENERGY", "TAUNT_COST", "TAUNT_RANGE", "DASH_COST",
    "DEFAULT_UNLOCKED_ACTIONS", "DEFAULT_LINE_BUDGET",
    "MAX_HP", "MAX_ENERGY", "MAX_CONSECUTIVE_FAILURES",
    "Bot", "calculate_damage", "resolve_deaths", "get_round_bonus_attack",
]


class Bot:
    """Runtime state for a bot in a match."""

    def __init__(self, *, name: str, emoji: str, bio: str, author: str,
                 decide_func: Callable[..., Any], x: int, y: int) -> None:
        self.name = name
        self.emoji = emoji
        self.bio = bio
        self.author = author
        self.decide_func = decide_func
        self.x = x
        self.y = y
        self.hp = STARTING_HP
        self.energy = STARTING_ENERGY
        self.attack_power = STARTING_ATTACK_POWER
        self.defense = STARTING_DEFENSE
        self.alive = True
        self.consecutive_failures = 0
        # Stats tracking
        self.kills = 0
        self.damage_dealt = 0
        self.damage_taken = 0
        self.rounds_survived = 0
        self.taunt_target: str | None = None
        # Progression fields (defaults match sandbox.BASE_ACTIONS / BUDGET_BASE)
        self.unlocked_actions: list[str] = sorted(DEFAULT_UNLOCKED_ACTIONS)
        self.line_budget: int = DEFAULT_LINE_BUDGET
        self.win_streak: int = 0

    def can_act(self) -> bool:
        """Check if bot has enough energy for any action (move is cheapest at 5)."""
        return self.energy >= MOVE_COST

    def apply_action_cost(self, action_type: str) -> None:
        """Deduct energy for an action."""
        self.energy = max(0, self.energy - ACTION_COSTS.get(action_type, 0))

    def to_enemy_dict(self) -> dict[str, Any]:
        """Bot info visible to other bots."""
        return {
            "name": self.name,
            "emoji": self.emoji,
            "x": self.x,
            "y": self.y,
            "hp": self.hp,
        }

    def to_self_dict(self) -> dict[str, Any]:
        """Full bot info visible to self."""
        return {
            "x": self.x,
            "y": self.y,
            "hp": self.hp,
            "energy": self.energy,
            "attack_power": self.attack_power,
            "defense": self.defense,
            "unlocked_actions": list(self.unlocked_actions),
            "line_budget": self.line_budget,
            "win_streak": self.win_streak,
        }


def get_round_bonus_attack(round_num: int) -> int:
    """Calculate bonus attack power from round-based scaling.

    +2 attack per 10 rounds after round 15.
    """
    if round_num <= 15:
        return 0
    return ((round_num - 15) // 10) * 2


def calculate_damage(attacker: Bot, defender: Bot) -> int:
    """Calculate damage from attacker to defender."""
    return max(0, attacker.attack_power - defender.defense)


def resolve_deaths(bots: list[Bot], round_num: int) -> list[dict[str, Any]]:
    """Check for deaths and return elimination records.

    Death ordering: lower HP dies first, then lower energy, then less total damage dealt.
    """
    newly_dead = [b for b in bots if b.alive and b.hp <= 0]

    # Sort by death priority (first to die = worst stats)
    newly_dead.sort(key=lambda b: (b.hp, b.energy, b.damage_dealt))

    eliminations = []
    for bot in newly_dead:
        bot.alive = False
        eliminations.append({
            "emoji": bot.emoji,
            "round": round_num,
        })

    return eliminations
