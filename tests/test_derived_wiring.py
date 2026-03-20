"""Tests for derived stats wired into game loop (T27.6)."""

from engine.rounds import apply_energy_and_rest
from engine.stats import StatAllocation
from tests.conftest import make_bot


# --- Cycle 1: Rest caps use derived max_hp / max_energy ---


def test_rest_caps_hp_at_derived_max():
    """Bot with ARMOR=50 (max_hp=95 after versatility), set hp=93, rest -> hp=95."""
    bot = make_bot(emoji="🧪", stat_allocation=StatAllocation(15, 15, 50, 20))
    assert bot.derived.max_hp == 95
    bot.hp = 93
    actions = {"🧪": ("rest",)}
    apply_energy_and_rest([bot], actions, set())
    assert bot.hp == 95  # capped at derived max


def test_rest_caps_energy_at_derived_max():
    """Bot with MIND=50 (max_energy=120), rest -> energy capped at 120."""
    bot = make_bot(emoji="🧪", stat_allocation=StatAllocation(15, 15, 20, 50))
    assert bot.derived.max_energy == 120
    bot.energy = 110
    actions = {"🧪": ("rest",)}
    apply_energy_and_rest([bot], actions, set())
    assert bot.energy == 120  # capped at derived max


def test_default_stats_hp_cap_100():
    """Default bot (25/25/25/25) hp capped at 100 on rest."""
    bot = make_bot(emoji="🧪")
    assert bot.derived.max_hp == 100
    bot.hp = 98
    actions = {"🧪": ("rest",)}
    apply_energy_and_rest([bot], actions, set())
    assert bot.hp == 100  # capped at 100 for default stats


def test_default_stats_rest_unchanged():
    """Default bot (25/25/25/25) rest gives exactly 20 energy (no regen bonus)."""
    bot = make_bot(emoji="🧪")
    assert bot.derived.energy_regen == 0
    bot.energy = 50
    actions = {"🧪": ("rest",)}
    apply_energy_and_rest([bot], actions, set())
    assert bot.energy == 70  # 50 + 20 base restore


# --- Cycle 2: MIND energy regen bonus ---


def test_rest_adds_mind_regen_bonus():
    """Bot with MIND=50 (energy_regen=10), rest gives 30 energy (20 base + 10 regen)."""
    bot = make_bot(emoji="🧪", stat_allocation=StatAllocation(15, 15, 20, 50))
    assert bot.derived.energy_regen == 10
    bot.energy = 50
    actions = {"🧪": ("rest",)}
    apply_energy_and_rest([bot], actions, set())
    assert bot.energy == 80  # 50 + 20 base + 10 regen


# --- Cycle 3: Kill bounty energy cap uses derived ---


def test_kill_bounty_energy_caps_at_derived_max():
    """Kill bounty energy should cap at bot.derived.max_energy, not 100."""
    from engine.rounds import attribute_kills
    bot = make_bot(emoji="🗡️", stat_allocation=StatAllocation(15, 15, 20, 50))
    assert bot.derived.max_energy == 120
    bot.energy = 100
    bot.kills = 0
    victim = make_bot(emoji="💀", hp=0)
    victim.alive = True
    bots = [bot, victim]

    round_elims = [{"emoji": "💀", "round": 1}]
    round_events = [
        {"type": "hit", "attacker": "🗡️", "target": "💀", "damage": 50, "hp_before": 30},
    ]
    attribute_kills(round_elims, round_events, bots, round_num=1)
    assert bot.energy == 120  # 100 + 30 bounty, capped at derived 120


# --- Cycle 4: Bounty reward uses derived stats ---


def test_bounty_reward_uses_derived_max():
    """apply_bounty_reward should restore to derived max_hp/max_energy."""
    from engine.bounty import apply_bounty_reward
    bot = make_bot(emoji="🧪", stat_allocation=StatAllocation(15, 15, 50, 50))
    assert bot.derived.max_hp == 95
    assert bot.derived.max_energy == 120
    bot.hp = 50
    bot.energy = 30
    reward = {"hp_restore": "full", "damage_bonus": 0.5, "bonus_rounds": 3}
    apply_bounty_reward(bot, reward)
    assert bot.hp == 95
    assert bot.energy == 120


# --- Cycle 5: Watcher uses derived for ratio ---


def test_watcher_spawn_uses_derived_max_hp():
    """Watcher spawn HP ratio should use bot.derived.max_hp, not hardcoded 100."""
    from unittest.mock import MagicMock
    from engine.watcher_spawn import check_watcher_spawn
    bot = make_bot(emoji="🧪", stat_allocation=StatAllocation(15, 15, 50, 20))
    assert bot.derived.max_hp == 95
    # hp=44 is NOT >50% of derived 95 (44 < 47.5)
    bot.hp = 44
    bot.rounds_survived = 5
    bot.kills = 0
    bot.human_adapter = MagicMock()
    result = check_watcher_spawn([bot], round_num=10, watcher_present=False)
    assert result is False  # 44/95 = 46.3% < 50%


# --- Cycle 6: Integration — high armor bot starts with more hp ---


def test_high_armor_bot_starts_with_different_hp():
    """Bot with high ARMOR starts with hp != default (versatility changes HP)."""
    from engine.game import run_match
    from tests.conftest import bot_config, always_rest

    configs = [
        {**bot_config("Tank", "🛡️", always_rest),
         "stat_allocation": StatAllocation(15, 15, 50, 20)},
        bot_config("Normal", "⚔️", always_rest),
    ]
    result = run_match(configs, seed=42)
    round1 = result["rounds"][0]
    tank_pos = next(p for p in round1["positions"] if p["emoji"] == "🛡️")
    normal_pos = next(p for p in round1["positions"] if p["emoji"] == "⚔️")
    # Tank (specialist) has 95 HP; Normal (balanced 25/25/25/25) has 100 HP
    assert tank_pos["hp"] == 95
    assert normal_pos["hp"] == 100


def test_mode_override_still_works():
    """Mode starting_hp override sets initial HP; rest then caps at derived max."""
    from engine.game import _prepare_match
    from engine.match_modes import get_mode

    configs = [
        {"name": "Tank", "emoji": "🛡️", "bio": "", "author": "test",
         "decide_func": lambda s: ("rest",),
         "stat_allocation": StatAllocation(15, 15, 50, 20)},
        {"name": "Normal", "emoji": "⚔️", "bio": "", "author": "test",
         "decide_func": lambda s: ("rest",)},
    ]
    mode = get_mode("extended")
    assert mode.starting_hp == 200
    bots, _players, _grid_size, _rng = _prepare_match(configs, seed=42, mode=mode)
    tank = next(b for b in bots if b.emoji == "🛡️")
    normal = next(b for b in bots if b.emoji == "⚔️")
    # Mode override sets starting HP to 200 for both
    assert tank.hp == 200
    assert normal.hp == 200
