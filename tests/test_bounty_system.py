"""Tests for the bounty placement and reward system."""

from engine.bounty import (
    BOUNTY_SCALING,
    BountyInfo,
    apply_bounty_reward,
    claim_bounty,
    place_bounties,
)
from engine.combat import Bot, calculate_damage, tick_damage_bonus


def test_place_bounties_returns_bounties_for_human_emojis():
    """When human emojis are present, place_bounties creates one bounty per human."""
    bots = []  # bots list not used for filtering, human_emojis does
    human_emojis = {"🤖", "🐍"}

    result = place_bounties(bots, human_emojis)

    assert len(result) == 2
    target_emojis = {b.target_emoji for b in result}
    assert target_emojis == {"🤖", "🐍"}


def test_place_bounties_returns_empty_for_pure_bot_match():
    """No bounties when no humans are playing."""
    result = place_bounties([], set())

    assert result == []


def test_bounty_info_has_correct_defaults():
    """BountyInfo has target_emoji, reward, and bonus_damage_rounds fields."""
    info = BountyInfo(target_emoji="🎯")

    assert info.target_emoji == "🎯"
    assert info.reward == "full_restore"
    assert info.bonus_damage_rounds == 3


def test_claim_bounty_returns_reward_when_target_matches():
    """Killing a bounty target returns the reward dict."""
    bounties = [BountyInfo(target_emoji="🎯")]

    reward = claim_bounty("🎯", bounties)

    assert reward is not None
    assert reward["hp_restore"] == "full"
    assert reward["energy_restore"] == "full"
    assert reward["damage_bonus"] == 0.5
    assert reward["bonus_rounds"] == 3


def test_claim_bounty_returns_none_when_no_match():
    """Killing a non-bounty target returns None."""
    bounties = [BountyInfo(target_emoji="🎯")]

    reward = claim_bounty("🐍", bounties)

    assert reward is None


def _make_bot(**overrides) -> Bot:
    """Create a Bot with sensible defaults for testing."""
    defaults = {
        "name": "TestBot",
        "emoji": "🤖",
        "bio": "test",
        "author": "tester",
        "decide_func": lambda *a, **k: ("rest",),
        "x": 0,
        "y": 0,
    }
    defaults.update(overrides)
    return Bot(**defaults)


def test_apply_bounty_reward_restores_hp_and_energy():
    """Applying a bounty reward sets HP and energy to max."""
    bot = _make_bot()
    bot.hp = 30
    bot.energy = 5
    reward = {
        "hp_restore": "full",
        "energy_restore": "full",
        "damage_bonus": 0.5,
        "bonus_rounds": 3,
    }

    apply_bounty_reward(bot, reward)

    assert bot.hp == 100
    assert bot.energy == 100


def test_apply_bounty_reward_sets_damage_bonus():
    """Applying a bounty reward sets the damage bonus tracker."""
    bot = _make_bot()
    reward = {
        "hp_restore": "full",
        "energy_restore": "full",
        "damage_bonus": 0.5,
        "bonus_rounds": 3,
    }

    apply_bounty_reward(bot, reward)

    assert bot.damage_bonus == {"multiplier": 1.5, "rounds_remaining": 3}


# --- Co-op Bounty Scaling Tests ---


def test_bounty_scaling_constant_exists():
    """BOUNTY_SCALING dict maps human counts to scaling parameters."""
    assert isinstance(BOUNTY_SCALING, dict)
    assert 1 in BOUNTY_SCALING
    assert 2 in BOUNTY_SCALING
    assert 3 in BOUNTY_SCALING


def test_scaling_1_human_full_reward():
    """1 human: full HP + full energy + 3 bonus rounds (unchanged)."""
    bounties = place_bounties([], {"🎯"})

    assert len(bounties) == 1
    b = bounties[0]
    assert b.hp_restore == "full"
    assert b.bonus_damage_rounds == 3


def test_scaling_2_humans_reduced_rounds():
    """2 humans: full HP + full energy + 2 bonus rounds."""
    bounties = place_bounties([], {"🎯", "🐍"})

    assert len(bounties) == 2
    for b in bounties:
        assert b.hp_restore == "full"
        assert b.bonus_damage_rounds == 2


def test_scaling_3_humans_no_hp_restore():
    """3 humans: NO HP restore + energy only + 1 bonus round."""
    bounties = place_bounties([], {"🎯", "🐍", "🤖"})

    assert len(bounties) == 3
    for b in bounties:
        assert b.hp_restore == "none"
        assert b.bonus_damage_rounds == 1


def test_scaling_4_humans_same_as_3():
    """4+ humans: same scaling as 3 humans."""
    bounties = place_bounties([], {"🎯", "🐍", "🤖", "🦊"})

    assert len(bounties) == 4
    for b in bounties:
        assert b.hp_restore == "none"
        assert b.bonus_damage_rounds == 1


def test_claim_bounty_respects_scaled_rounds():
    """claim_bounty returns bonus_rounds from the BountyInfo, not hardcoded."""
    bounty = BountyInfo(target_emoji="🎯", hp_restore="full", bonus_damage_rounds=2)
    reward = claim_bounty("🎯", [bounty])

    assert reward is not None
    assert reward["bonus_rounds"] == 2
    assert reward["hp_restore"] == "full"


def test_claim_bounty_respects_no_hp_restore():
    """claim_bounty passes hp_restore='none' from BountyInfo."""
    bounty = BountyInfo(target_emoji="🎯", hp_restore="none", bonus_damage_rounds=1)
    reward = claim_bounty("🎯", [bounty])

    assert reward is not None
    assert reward["hp_restore"] == "none"
    assert reward["bonus_rounds"] == 1


def test_apply_bounty_reward_skips_hp_when_none():
    """apply_bounty_reward does NOT restore HP when hp_restore is 'none'."""
    bot = _make_bot()
    bot.hp = 30
    bot.energy = 5
    reward = {
        "hp_restore": "none",
        "energy_restore": "full",
        "damage_bonus": 0.5,
        "bonus_rounds": 1,
    }

    apply_bounty_reward(bot, reward)

    assert bot.hp == 30  # unchanged
    assert bot.energy == 100  # still restored


def test_scaling_is_automatic():
    """Scaling is determined by human_emojis count, no manual config needed."""
    # 1 human
    b1 = place_bounties([], {"🎯"})
    # 2 humans
    b2 = place_bounties([], {"🎯", "🐍"})

    assert b1[0].bonus_damage_rounds != b2[0].bonus_damage_rounds


# --- Damage Bonus Integration Tests ---


def test_calculate_damage_applies_bonus():
    """calculate_damage uses damage_bonus multiplier when active."""
    attacker = _make_bot(emoji="🗡️")
    defender = _make_bot(emoji="🛡️")
    base_dmg = calculate_damage(attacker, defender)

    attacker.damage_bonus = {"multiplier": 1.5, "rounds_remaining": 3}
    bonus_dmg = calculate_damage(attacker, defender)

    assert bonus_dmg == int(base_dmg * 1.5)
    assert bonus_dmg > base_dmg


def test_calculate_damage_no_bonus_when_expired():
    """calculate_damage ignores damage_bonus when rounds_remaining is 0."""
    attacker = _make_bot(emoji="🗡️")
    defender = _make_bot(emoji="🛡️")
    base_dmg = calculate_damage(attacker, defender)

    attacker.damage_bonus = {"multiplier": 1.5, "rounds_remaining": 0}
    assert calculate_damage(attacker, defender) == base_dmg


def test_tick_damage_bonus_decrements():
    """tick_damage_bonus decrements rounds_remaining each call."""
    bot = _make_bot()
    bot.damage_bonus = {"multiplier": 1.5, "rounds_remaining": 2}

    tick_damage_bonus([bot])
    assert bot.damage_bonus["rounds_remaining"] == 1

    tick_damage_bonus([bot])
    assert bot.damage_bonus is None


def test_tick_damage_bonus_noop_without_bonus():
    """tick_damage_bonus is safe when bot has no bonus."""
    bot = _make_bot()
    tick_damage_bonus([bot])
    assert bot.damage_bonus is None
