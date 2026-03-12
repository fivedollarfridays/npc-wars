"""Combat mechanics for NPC Wars."""


# Starting stats (identical for all bots)
STARTING_HP = 100
STARTING_ENERGY = 100
STARTING_ATTACK_POWER = 15
STARTING_DEFENSE = 0

# Action costs
MOVE_COST = 5
ATTACK_COST = 15
DEFEND_COST = 10
REST_COST = 0

# Rest healing
REST_HEAL = 10
REST_ENERGY_RESTORE = 20

# Defend bonus
DEFEND_BONUS = 10

# Storm damage
STORM_DAMAGE = 10

# HP / Energy caps
MAX_HP = 100
MAX_ENERGY = 100

# Failure tracking
MAX_CONSECUTIVE_FAILURES = 3


class Bot:
    """Runtime state for a bot in a match."""

    def __init__(self, name: str, emoji: str, bio: str, author: str, decide_func, x: int, y: int):
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
        self.action = None  # Set each round

        # Stats tracking
        self.kills = 0
        self.damage_dealt = 0
        self.damage_taken = 0
        self.rounds_survived = 0

    def can_act(self) -> bool:
        """Check if bot has enough energy for any action (move is cheapest at 5)."""
        return self.energy >= MOVE_COST

    def force_rest(self):
        """Force rest when out of energy."""
        self.hp = min(MAX_HP, self.hp + REST_HEAL)
        self.energy = min(MAX_ENERGY, self.energy + REST_ENERGY_RESTORE)

    def apply_action_cost(self, action_type: str):
        """Deduct energy for an action."""
        costs = {
            "move": MOVE_COST,
            "attack": ATTACK_COST,
            "defend": DEFEND_COST,
            "rest": REST_COST,
        }
        self.energy -= costs.get(action_type, 0)

    def to_enemy_dict(self) -> dict:
        """Bot info visible to other bots."""
        return {
            "name": self.name,
            "emoji": self.emoji,
            "x": self.x,
            "y": self.y,
            "hp": self.hp,
        }

    def to_self_dict(self) -> dict:
        """Full bot info visible to self."""
        return {
            "x": self.x,
            "y": self.y,
            "hp": self.hp,
            "energy": self.energy,
            "attack_power": self.attack_power,
            "defense": self.defense,
        }


def calculate_damage(attacker: Bot, defender: Bot) -> int:
    """Calculate damage from attacker to defender."""
    return max(0, attacker.attack_power - defender.defense)


def resolve_deaths(bots: list[Bot], round_num: int) -> list[dict]:
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
