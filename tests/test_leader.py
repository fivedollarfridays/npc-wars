"""Tests for the one-leader rule — only highest scorer gets tier 3+."""

from __future__ import annotations

from tests.conftest import make_bot


# --- Cycle 1: determine_leader ---


def test_leader_is_highest_scorer():
    from engine.momentum import determine_leader
    a = make_bot(emoji="A")
    a.score = 50
    b = make_bot(emoji="B")
    b.score = 30
    assert determine_leader([a, b]) is a


def test_leader_tiebreak_by_kills():
    from engine.momentum import determine_leader
    a = make_bot(emoji="A")
    a.score = 50
    a.kills = 2
    b = make_bot(emoji="B")
    b.score = 50
    b.kills = 3
    assert determine_leader([a, b]) is b


def test_leader_tiebreak_by_emoji_alphabetical():
    from engine.momentum import determine_leader
    a = make_bot(emoji="A")
    a.score = 50
    a.kills = 2
    b = make_bot(emoji="B")
    b.score = 50
    b.kills = 2
    assert determine_leader([a, b]) is a


def test_dead_bot_cannot_be_leader():
    from engine.momentum import determine_leader
    a = make_bot(emoji="A")
    a.score = 100
    a.alive = False
    b = make_bot(emoji="B")
    b.score = 30
    assert determine_leader([a, b]) is b


def test_no_leader_when_all_dead():
    from engine.momentum import determine_leader
    a = make_bot(emoji="A")
    a.alive = False
    b = make_bot(emoji="B")
    b.alive = False
    assert determine_leader([a, b]) is None


def test_no_leader_when_all_scores_zero():
    from engine.momentum import determine_leader
    a = make_bot(emoji="A")
    b = make_bot(emoji="B")
    assert determine_leader([a, b]) is None


def test_sole_alive_bot_is_leader():
    from engine.momentum import determine_leader
    a = make_bot(emoji="A")
    a.score = 10
    assert determine_leader([a]) is a


def test_no_leader_empty_list():
    from engine.momentum import determine_leader
    assert determine_leader([]) is None


# --- Cycle 2: Non-leader tier capping ---


def test_non_leader_capped_at_tier2():
    """A non-leader with score 65 (normally tier 4) is capped at tier 2."""
    from engine.momentum import apply_momentum_bonuses
    bot = make_bot(emoji="A")
    bot.score = 65
    apply_momentum_bonuses(bot, is_leader=False)
    assert bot.momentum_tier == 2
    # Tier 2 bonuses only: energy + damage, no defense reduction
    assert bot.momentum_energy_bonus == 5
    assert bot.momentum_damage_multiplier == 1.1
    assert bot.momentum_defense_reduction == 0.0


def test_leader_gets_full_tier4():
    """The leader with score 65 gets full tier 4."""
    from engine.momentum import apply_momentum_bonuses
    bot = make_bot(emoji="A")
    bot.score = 65
    apply_momentum_bonuses(bot, is_leader=True)
    assert bot.momentum_tier == 4
    assert bot.momentum_energy_bonus == 5
    assert bot.momentum_damage_multiplier == 1.1
    assert bot.momentum_defense_reduction == 0.15


def test_non_leader_score_45_capped_at_tier2():
    """A non-leader with score 45 (normally tier 3) is capped at tier 2."""
    from engine.momentum import apply_momentum_bonuses
    bot = make_bot(emoji="A")
    bot.score = 45
    apply_momentum_bonuses(bot, is_leader=False)
    assert bot.momentum_tier == 2


def test_non_leader_score_30_stays_tier2():
    """A non-leader with score 30 (tier 2) is unaffected by cap."""
    from engine.momentum import apply_momentum_bonuses
    bot = make_bot(emoji="A")
    bot.score = 30
    apply_momentum_bonuses(bot, is_leader=False)
    assert bot.momentum_tier == 2


def test_default_is_leader_false():
    """Calling without is_leader defaults to False (backward compat)."""
    from engine.momentum import apply_momentum_bonuses
    bot = make_bot(emoji="A")
    bot.score = 65
    apply_momentum_bonuses(bot)
    # Default is_leader=False, so capped at tier 2
    assert bot.momentum_tier == 2


# --- Cycle 3: Bot.is_leader field + serialization ---


def test_bot_is_leader_defaults_false():
    bot = make_bot(emoji="A")
    assert bot.is_leader is False


def test_apply_sets_is_leader_true():
    from engine.momentum import apply_momentum_bonuses
    bot = make_bot(emoji="A")
    bot.score = 50
    apply_momentum_bonuses(bot, is_leader=True)
    assert bot.is_leader is True


def test_apply_sets_is_leader_false():
    from engine.momentum import apply_momentum_bonuses
    bot = make_bot(emoji="A")
    bot.score = 50
    apply_momentum_bonuses(bot, is_leader=False)
    assert bot.is_leader is False


def test_to_self_dict_has_is_leader():
    from engine.momentum import apply_momentum_bonuses
    bot = make_bot(emoji="A")
    bot.score = 50
    apply_momentum_bonuses(bot, is_leader=True)
    d = bot.to_self_dict()
    assert "is_leader" in d
    assert d["is_leader"] is True


def test_to_enemy_dict_has_is_leader():
    from engine.momentum import apply_momentum_bonuses
    bot = make_bot(emoji="A")
    bot.score = 50
    apply_momentum_bonuses(bot, is_leader=True)
    d = bot.to_enemy_dict()
    assert "is_leader" in d
    assert d["is_leader"] is True


# --- Cycle 4: Crown transfer + game loop integration ---


def test_crown_transfers_on_overtake():
    """When bot B overtakes A in score, B becomes leader."""
    from engine.momentum import determine_leader, apply_momentum_bonuses

    a = make_bot(emoji="A")
    a.score = 50
    b = make_bot(emoji="B")
    b.score = 40
    bots = [a, b]

    # Round 1: A is leader
    leader = determine_leader(bots)
    assert leader is a
    for bot in bots:
        apply_momentum_bonuses(bot, is_leader=(bot is leader))
    assert a.is_leader is True
    assert b.is_leader is False

    # B overtakes
    b.score = 55
    leader = determine_leader(bots)
    assert leader is b
    for bot in bots:
        apply_momentum_bonuses(bot, is_leader=(bot is leader))
    assert a.is_leader is False
    assert b.is_leader is True
    # A's tier capped at 2 even though score=50 (tier 3 normally)
    assert a.momentum_tier == 2
    # B gets full tier
    assert b.momentum_tier == 3


def test_game_loop_sets_leader():
    """Integration: run_match sets is_leader correctly during game."""
    from engine.game import run_match

    configs = [
        {"name": "A", "emoji": "A", "bio": "a", "author": "t",
         "decide_func": lambda s: ("rest",)},
        {"name": "B", "emoji": "B", "bio": "b", "author": "t",
         "decide_func": lambda s: ("rest",)},
    ]
    result = run_match(configs, match_id=1, seed=42)
    # Match should complete without errors
    assert result is not None
