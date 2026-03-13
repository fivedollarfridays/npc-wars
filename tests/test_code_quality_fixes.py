"""Tests for code quality and efficiency fixes across engine modules."""

from tests.conftest import make_bot

from engine.combat import (
    ACTION_COSTS,
    ATTACK_COST,
    DEFEND_COST,
    MOVE_COST,
    REST_COST,
    STARTING_DEFENSE,
)
from engine.loader import load_bots
from engine.rounds import resolve_attacks, resolve_defense
from engine.grid import apply_direction


def _write_bot(tmp_path, filename, content):
    """Write a bot file to tmp_path."""
    path = tmp_path / filename
    path.write_text(content)
    return path


# --- 1. Emoji uniqueness in loader ---


class TestEmojiUniqueness:
    def test_duplicate_emoji_skipped(self, tmp_path):
        """Second bot with same emoji should be skipped."""
        _write_bot(tmp_path, "bot_a.py", '''
BOT_NAME = "First"
BOT_EMOJI = "X"
def decide(state): return ("rest",)
''')
        _write_bot(tmp_path, "bot_b.py", '''
BOT_NAME = "Second"
BOT_EMOJI = "X"
def decide(state): return ("rest",)
''')
        bots = load_bots(str(tmp_path))
        assert len(bots) == 1
        assert bots[0]["name"] == "First"

    def test_unique_emojis_all_loaded(self, tmp_path):
        """Bots with distinct emojis should all load."""
        _write_bot(tmp_path, "bot_a.py", '''
BOT_NAME = "A"
BOT_EMOJI = "1"
def decide(state): return ("rest",)
''')
        _write_bot(tmp_path, "bot_b.py", '''
BOT_NAME = "B"
BOT_EMOJI = "2"
def decide(state): return ("rest",)
''')
        bots = load_bots(str(tmp_path))
        assert len(bots) == 2


# --- 2. No self.action attribute on Bot ---


class TestBotNoActionAttribute:
    def test_no_action_attribute(self):
        """Bot.__init__ should not set self.action."""
        bot = make_bot()
        assert not hasattr(bot, "action")


# --- 3. ACTION_COSTS module-level constant ---


class TestActionCostsConstant:
    def test_action_costs_exists(self):
        """ACTION_COSTS should be a module-level dict."""
        assert isinstance(ACTION_COSTS, dict)

    def test_action_costs_values(self):
        """ACTION_COSTS should map action names to their costs."""
        assert ACTION_COSTS["move"] == MOVE_COST
        assert ACTION_COSTS["attack"] == ATTACK_COST
        assert ACTION_COSTS["defend"] == DEFEND_COST
        assert ACTION_COSTS["rest"] == REST_COST

    def test_apply_action_cost_uses_constant(self):
        """apply_action_cost should still work correctly with the constant."""
        bot = make_bot(energy=100)
        bot.apply_action_cost("move")
        assert bot.energy == 100 - MOVE_COST


# --- 4. O(1) position lookup in resolve_attacks ---


class TestResolveAttacksPositionLookup:
    def test_hit_still_works(self):
        """Attack on adjacent occupied cell should hit."""
        attacker = make_bot(emoji="A", x=5, y=5)
        target = make_bot(emoji="B", x=6, y=5)
        actions = {"A": ("attack", "east")}
        events = resolve_attacks([attacker, target], actions)
        hits = [e for e in events if e["type"] == "hit"]
        assert len(hits) == 1
        assert hits[0]["target"] == "B"

    def test_miss_still_works(self):
        """Attack on empty cell should miss."""
        attacker = make_bot(emoji="A", x=5, y=5)
        other = make_bot(emoji="B", x=8, y=8)
        actions = {"A": ("attack", "east")}
        events = resolve_attacks([attacker, other], actions)
        misses = [e for e in events if e["type"] == "miss"]
        assert len(misses) == 1

    def test_no_self_hit(self):
        """Bot should not hit itself."""
        bot = make_bot(emoji="A", x=5, y=5)
        actions = {"A": ("attack", "north")}
        events = resolve_attacks([bot], actions)
        hits = [e for e in events if e["type"] == "hit"]
        assert len(hits) == 0


# --- 5. sum() for alive counting in game.py ---
# (This is a refactor -- behavior tested by existing test_game.py tests)


# --- 6. STARTING_DEFENSE used in resolve_defense ---


class TestResolveDefenseUsesConstant:
    def test_defense_resets_to_starting(self):
        """Defense should reset to STARTING_DEFENSE, not hardcoded 0."""
        bot = make_bot(emoji="A")
        bot.defense = 99
        actions = {"A": ("move", "north")}
        resolve_defense([bot], actions)
        assert bot.defense == STARTING_DEFENSE

    def test_defend_action_applies_bonus(self):
        """Defend action should still apply the defend bonus."""
        bot = make_bot(emoji="A")
        actions = {"A": ("defend",)}
        resolve_defense([bot], actions)
        from engine.combat import DEFEND_BONUS
        assert bot.defense == DEFEND_BONUS
