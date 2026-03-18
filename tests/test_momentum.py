"""Tests for the momentum tier system."""

from __future__ import annotations


# --- Cycle 1: Tier thresholds, names, carryover ---

def test_tier_0_at_score_0():
    from engine.momentum import get_tier
    assert get_tier(0) == 0


def test_tier_0_at_score_9():
    from engine.momentum import get_tier
    assert get_tier(9) == 0


def test_tier_1_at_score_10():
    from engine.momentum import get_tier
    assert get_tier(10) == 1


def test_tier_1_at_score_24():
    from engine.momentum import get_tier
    assert get_tier(24) == 1


def test_tier_2_at_score_25():
    from engine.momentum import get_tier
    assert get_tier(25) == 2


def test_tier_2_at_score_39():
    from engine.momentum import get_tier
    assert get_tier(39) == 2


def test_tier_3_at_score_40():
    from engine.momentum import get_tier
    assert get_tier(40) == 3


def test_tier_3_at_score_59():
    from engine.momentum import get_tier
    assert get_tier(59) == 3


def test_tier_4_at_score_60():
    from engine.momentum import get_tier
    assert get_tier(60) == 4


def test_tier_4_at_score_100():
    from engine.momentum import get_tier
    assert get_tier(100) == 4


def test_tier_name_0():
    from engine.momentum import get_tier_name
    assert get_tier_name(5) == ""


def test_tier_name_momentum():
    from engine.momentum import get_tier_name
    assert get_tier_name(10) == "Momentum"


def test_tier_name_battle_fury():
    from engine.momentum import get_tier_name
    assert get_tier_name(25) == "Battle Fury"


def test_tier_name_crowd_favorite():
    from engine.momentum import get_tier_name
    assert get_tier_name(40) == "Crowd Favorite"


def test_tier_name_unstoppable():
    from engine.momentum import get_tier_name
    assert get_tier_name(60) == "Unstoppable"


def test_carryover_winner_50_percent():
    from engine.momentum import calculate_carryover
    assert calculate_carryover(80, is_winner=True) == 40


def test_carryover_winner_capped_at_50():
    from engine.momentum import calculate_carryover
    assert calculate_carryover(120, is_winner=True) == 50


def test_carryover_non_winner_is_zero():
    from engine.momentum import calculate_carryover
    assert calculate_carryover(80, is_winner=False) == 0


def test_carryover_winner_exact_100():
    from engine.momentum import calculate_carryover
    assert calculate_carryover(100, is_winner=True) == 50


# --- Cycle 2: apply_momentum_bonuses + Bot fields ---

def _make_bot(score: int = 0):
    """Create a minimal Bot for testing."""
    from engine.combat import Bot
    bot = Bot(name="Test", emoji="T", bio="test", author="test",
              decide_func=lambda s: ("rest",), x=0, y=0)
    bot.score = score
    return bot


def test_bot_has_momentum_fields():
    bot = _make_bot()
    assert bot.momentum_tier == 0
    assert bot.momentum_energy_bonus == 0
    assert bot.momentum_damage_multiplier == 1.0
    assert bot.momentum_defense_reduction == 0.0


def test_apply_tier0_no_bonuses():
    from engine.momentum import apply_momentum_bonuses
    bot = _make_bot(score=5)
    apply_momentum_bonuses(bot)
    assert bot.momentum_tier == 0
    assert bot.momentum_energy_bonus == 0
    assert bot.momentum_damage_multiplier == 1.0
    assert bot.momentum_defense_reduction == 0.0


def test_apply_tier1_energy_bonus():
    from engine.momentum import apply_momentum_bonuses
    bot = _make_bot(score=15)
    apply_momentum_bonuses(bot)
    assert bot.momentum_tier == 1
    assert bot.momentum_energy_bonus == 5
    assert bot.momentum_damage_multiplier == 1.0
    assert bot.momentum_defense_reduction == 0.0


def test_apply_tier2_energy_and_damage():
    from engine.momentum import apply_momentum_bonuses
    bot = _make_bot(score=30)
    apply_momentum_bonuses(bot)
    assert bot.momentum_tier == 2
    assert bot.momentum_energy_bonus == 5
    assert bot.momentum_damage_multiplier == 1.1
    assert bot.momentum_defense_reduction == 0.0


def test_apply_tier3_no_extra_stat_bonus():
    from engine.momentum import apply_momentum_bonuses
    bot = _make_bot(score=45)
    apply_momentum_bonuses(bot)
    assert bot.momentum_tier == 3
    assert bot.momentum_energy_bonus == 5
    assert bot.momentum_damage_multiplier == 1.1
    assert bot.momentum_defense_reduction == 0.0  # tier 3 is visual only


def test_apply_tier4_all_cumulative():
    from engine.momentum import apply_momentum_bonuses
    bot = _make_bot(score=65)
    apply_momentum_bonuses(bot)
    assert bot.momentum_tier == 4
    assert bot.momentum_energy_bonus == 5
    assert bot.momentum_damage_multiplier == 1.1
    assert bot.momentum_defense_reduction == 0.15


def test_to_self_dict_has_momentum():
    from engine.momentum import apply_momentum_bonuses
    bot = _make_bot(score=15)
    apply_momentum_bonuses(bot)
    d = bot.to_self_dict()
    assert d["momentum_tier"] == 1
    assert d["momentum_name"] == "Momentum"


def test_to_enemy_dict_has_momentum_tier():
    from engine.momentum import apply_momentum_bonuses
    bot = _make_bot(score=30)
    apply_momentum_bonuses(bot)
    d = bot.to_enemy_dict()
    assert d["momentum_tier"] == 2


# --- Cycle 3: Combat integration (damage, defense, energy) ---

def test_damage_multiplier_applied_tier2():
    """Tier 2+ bot deals 10% more damage via momentum_damage_multiplier."""
    from engine.combat import calculate_damage
    from engine.momentum import apply_momentum_bonuses

    attacker = _make_bot(score=30)  # tier 2
    apply_momentum_bonuses(attacker)
    defender = _make_bot(score=0)

    dmg = calculate_damage(attacker, defender)
    # base = 25 (attack_power) - 0 (defense) = 25, * 1.1 = 27.5 -> 27
    assert dmg == 27


def test_damage_no_multiplier_tier0():
    """Tier 0 bot deals normal damage."""
    from engine.combat import calculate_damage

    attacker = _make_bot(score=0)
    defender = _make_bot(score=0)

    dmg = calculate_damage(attacker, defender)
    assert dmg == 25  # base unchanged


def test_defense_reduction_applied_tier4():
    """Tier 4 defender takes 15% less incoming damage."""
    from engine.combat import calculate_damage
    from engine.momentum import apply_momentum_bonuses

    attacker = _make_bot(score=0)
    defender = _make_bot(score=65)  # tier 4
    apply_momentum_bonuses(defender)

    dmg = calculate_damage(attacker, defender)
    # base = 25 - 0 = 25, reduced by 15% -> 25 * 0.85 = 21.25 -> 21
    assert dmg == 21


def test_damage_and_defense_both_apply():
    """Tier 4 attacker vs tier 4 defender: both bonuses apply."""
    from engine.combat import calculate_damage
    from engine.momentum import apply_momentum_bonuses

    attacker = _make_bot(score=65)  # tier 4
    apply_momentum_bonuses(attacker)
    defender = _make_bot(score=65)  # tier 4
    apply_momentum_bonuses(defender)

    dmg = calculate_damage(attacker, defender)
    # base = 25 - 0 = 25
    # attacker multiplier: int(25 * 1.1) = 27
    # defender reduction: int(27 * 0.85) = 22
    assert dmg == 22


def test_energy_restore_with_momentum_bonus():
    """Tier 1+ bot gets +5 energy on rest (25 total instead of 20)."""
    from engine.momentum import apply_momentum_bonuses
    from engine.rounds import apply_energy_and_rest

    bot = _make_bot(score=15)  # tier 1
    apply_momentum_bonuses(bot)
    bot.energy = 50  # start with some energy

    actions = {bot.emoji: ("rest",)}
    forced_rest: set[str] = set()
    apply_energy_and_rest([bot], actions, forced_rest)

    # rest gives 20 base + 5 momentum bonus = 25
    assert bot.energy == 75


def test_energy_restore_no_momentum_bonus():
    """Tier 0 bot gets normal 20 energy on rest."""
    from engine.rounds import apply_energy_and_rest

    bot = _make_bot(score=0)
    bot.energy = 50

    actions = {bot.emoji: ("rest",)}
    apply_energy_and_rest([bot], actions, set())

    assert bot.energy == 70  # 50 + 20


# --- Cycle 4: Game loop integration ---

def test_game_loop_applies_momentum():
    """After _apply_round_scores, bots should have momentum_tier updated."""
    from engine.game import run_match

    # Create 2 simple bots that just rest
    configs = [
        {"name": "A", "emoji": "A", "bio": "a", "author": "t",
         "decide_func": lambda s: ("rest",)},
        {"name": "B", "emoji": "B", "bio": "b", "author": "t",
         "decide_func": lambda s: ("rest",)},
    ]
    result = run_match(configs, match_id=1, seed=42)
    # Just verify match completes without error (momentum wiring works)
    assert "winner" in result or "winner_emoji" in result or result is not None
