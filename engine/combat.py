"""Combat mechanics for NPC Wars."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from engine.stats import DEFAULT_ALLOCATION, StatAllocation, calculate_derived

if TYPE_CHECKING:
    from engine.human_input import HumanInputAdapter
    from engine.stats import DerivedStats

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
TRAP_COST = 15

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
    "trap": TRAP_COST,
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
    "KILL_BOUNTY_ENERGY", "TAUNT_COST", "TAUNT_RANGE", "DASH_COST", "TRAP_COST",
    "DEFAULT_UNLOCKED_ACTIONS", "DEFAULT_LINE_BUDGET",
    "MAX_HP", "MAX_ENERGY", "MAX_CONSECUTIVE_FAILURES",
    "Bot", "calculate_damage", "resolve_deaths", "get_round_bonus_attack",
]


class Bot:
    """Runtime state for a bot in a match."""

    def __init__(self, *, name: str, emoji: str, bio: str, author: str,
                 decide_func: Callable[..., Any], x: int, y: int,
                 stat_allocation: StatAllocation | None = None,
                 glyph: str | None = None) -> None:
        self.name = name
        self.emoji = emoji
        self.glyph: str = glyph if glyph is not None else self.emoji
        self.bio = bio
        self.author = author
        self.decide_func = decide_func
        self.x = x
        self.y = y
        # Stat allocation and derived stats
        self.stats: StatAllocation = stat_allocation if stat_allocation is not None else DEFAULT_ALLOCATION
        self.derived: DerivedStats = calculate_derived(self.stats)
        self.hp: float = float(self.derived.max_hp)
        self.energy = self.derived.max_energy
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
        # Copilot: optional human input adapter
        self.human_adapter: HumanInputAdapter | None = None
        # Bounty: temporary damage bonus from bounty reward
        # Schema: {"multiplier": float, "rounds_remaining": int}
        self.damage_bonus: dict[str, float | int] | None = None
        # Scoring
        self.score: int = 0
        self.passive_rounds: int = 0
        # Trap manager reference (set by game loop for state dict)
        self._trap_manager: Any = None
        self._current_round: int = 0
        # Momentum tier bonuses (set by engine.momentum.apply_momentum_bonuses)
        self.momentum_tier: int = 0
        self.momentum_energy_bonus: int = 0
        self.momentum_damage_multiplier: float = 1.0
        self.momentum_defense_reduction: float = 0.0
        # Leader status (set by engine.momentum.apply_momentum_bonuses)
        self.is_leader: bool = False
        # Callbacks (populated by engine.callbacks.discover_callbacks)
        from engine.callbacks import CallbackSet
        self.callbacks: CallbackSet = CallbackSet()
        self.trap_cooldown: int = 0  # managed by engine.traps.TrapManager

    def can_act(self) -> bool:
        """Check if bot has enough energy for any action (move is cheapest at 5)."""
        return self.energy >= MOVE_COST

    def apply_action_cost(self, action_type: str) -> None:
        """Deduct energy for an action."""
        self.energy = max(0, self.energy - ACTION_COSTS.get(action_type, 0))

    def _speed_class(self) -> str:
        """Qualitative speed label based on raw speed stat."""
        if self.stats.speed < 15:
            return "slow"
        if self.stats.speed <= 30:
            return "normal"
        if self.stats.speed <= 45:
            return "fast"
        return "blazing"

    def _get_trap_info(self) -> list[dict[str, Any]]:
        """Own trap positions and expiry for state dict."""
        if self._trap_manager is None:
            return []
        traps = self._trap_manager.get_traps_for(self.emoji)
        return [
            {"x": t.x, "y": t.y, "expires_in": t.expires_round - self._current_round}
            for t in traps
        ]

    def _get_trap_cooldown(self) -> int:
        """Rounds until next trap placement allowed."""
        if self._trap_manager is None:
            return 0
        return self._trap_manager.get_cooldown_at(self.emoji, self._current_round)

    def _get_active_callbacks(self) -> list[str]:
        """List of active callback names."""
        names: list[str] = []
        if self.callbacks.setup is not None:
            names.append("setup")
        if self.callbacks.on_kill is not None:
            names.append("on_kill")
        if self.callbacks.react is not None:
            names.append("react")
        return names

    def to_enemy_dict(self) -> dict[str, Any]:
        """Bot info visible to other bots."""
        has_traps = False
        if self._trap_manager is not None:
            has_traps = len(self._trap_manager.get_traps_for(self.emoji)) > 0
        return {
            "name": self.name,
            "emoji": self.emoji,
            "glyph": self.glyph,
            "x": self.x,
            "y": self.y,
            "hp": self.hp,
            "score": self.score,
            "momentum_tier": self.momentum_tier,
            "is_leader": self.is_leader,
            "max_hp": self.derived.max_hp,
            "speed_class": self._speed_class(),
            "has_traps": has_traps,
        }

    def to_self_dict(self) -> dict[str, Any]:
        """Full bot info visible to self."""
        from engine.momentum import get_tier_name
        return {
            "x": self.x,
            "y": self.y,
            "glyph": self.glyph,
            "hp": self.hp,
            "energy": self.energy,
            "attack_power": self.attack_power,
            "defense": self.defense,
            "unlocked_actions": list(self.unlocked_actions),
            "line_budget": self.line_budget,
            "win_streak": self.win_streak,
            "score": self.score,
            "momentum_tier": self.momentum_tier,
            "momentum_name": get_tier_name(self.score),
            "is_leader": self.is_leader,
            "power": self.stats.power,
            "speed": self.stats.speed,
            "armor": self.stats.armor,
            "mind": self.stats.mind,
            "max_hp": self.derived.max_hp,
            "max_energy": self.derived.max_energy,
            "min_damage": self.derived.min_damage,
            "max_damage": self.derived.max_damage,
            "dodge_chance": self.derived.dodge_chance,
            "damage_reduction": self.derived.damage_reduction,
            "passive_rounds": self.passive_rounds,
            "traps": self._get_trap_info(),
            "trap_cooldown": self._get_trap_cooldown(),
            "callbacks": self._get_active_callbacks(),
        }


def get_round_bonus_attack(round_num: int) -> int:
    """Calculate bonus attack power from round-based scaling.

    +2 attack per 10 rounds after round 15.
    """
    if round_num <= 15:
        return 0
    return ((round_num - 15) // 10) * 2


def calculate_damage(attacker: Bot, defender: Bot) -> int:
    """Calculate damage from attacker to defender, including bounty and momentum bonuses."""
    base = max(0, attacker.attack_power - defender.defense)
    if attacker.damage_bonus and attacker.damage_bonus.get("rounds_remaining", 0) > 0:
        base = int(base * attacker.damage_bonus["multiplier"])
    # Momentum: attacker damage multiplier (tier 2+)
    base = int(base * attacker.momentum_damage_multiplier)
    # Momentum: defender damage reduction (tier 4)
    if defender.momentum_defense_reduction > 0:
        base = int(base * (1.0 - defender.momentum_defense_reduction))
    return base


def tick_damage_bonus(bots: list[Bot]) -> None:
    """Decrement damage bonus rounds for all bots. Clears bonus when expired."""
    for bot in bots:
        if bot.damage_bonus and bot.damage_bonus.get("rounds_remaining", 0) > 0:
            bot.damage_bonus["rounds_remaining"] -= 1
            if bot.damage_bonus["rounds_remaining"] <= 0:
                bot.damage_bonus = None


def resolve_deaths(bots: list[Bot], round_num: int) -> list[dict[str, Any]]:
    """Check for deaths and return elimination records.

    Death ordering: lower HP dies first, then lower energy, then less total damage dealt.
    If ALL remaining bots would die, the best one survives at 1 HP — someone always wins.
    """
    newly_dead = [b for b in bots if b.alive and b.hp <= 0]

    # Sort by death priority (first to die = worst stats)
    newly_dead.sort(key=lambda b: (b.hp, b.energy, b.damage_dealt))

    # If everyone alive would die, spare the best one
    alive_count = sum(1 for b in bots if b.alive)
    if len(newly_dead) == alive_count and alive_count > 1:
        survivor = newly_dead.pop()  # best stats (last in sorted order)
        survivor.hp = 1

    eliminations = []
    for bot in newly_dead:
        bot.alive = False
        eliminations.append({
            "emoji": bot.emoji,
            "round": round_num,
        })

    return eliminations
