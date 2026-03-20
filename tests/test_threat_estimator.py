"""Tests for incoming threat estimator in state dict (T29.6)."""

from engine.combat import Bot
from engine.combat_rolls import calculate_hit_probability
from engine.state import build_state
from engine.stats import StatAllocation, calculate_derived


def _make_bot(emoji: str, x: int = 0, y: int = 0,
              alloc: StatAllocation | None = None) -> Bot:
    """Helper to create a bot with optional stat allocation."""
    return Bot(
        name=emoji, emoji=emoji, bio="", author="test",
        decide_func=lambda s: ("rest",), x=x, y=y,
        stat_allocation=alloc,
    )


# --- Cycle 1: calculate_hit_probability prerequisite ---

def test_hit_probability_returns_dict():
    """calculate_hit_probability returns dict with expected keys."""
    attacker = calculate_derived(StatAllocation(25, 25, 25, 25))
    defender = calculate_derived(StatAllocation(25, 25, 25, 25))
    result = calculate_hit_probability(attacker, defender)
    assert isinstance(result, dict)
    for key in ("hit_chance", "crit_chance", "dodge_chance", "expected_damage"):
        assert key in result


def test_hit_probability_high_power_more_damage():
    """Higher power attacker should have higher expected damage than low-power specialist."""
    weak = calculate_derived(StatAllocation(15, 50, 15, 20))
    strong = calculate_derived(StatAllocation(50, 15, 20, 15))
    defender = calculate_derived(StatAllocation(25, 25, 25, 25))
    assert (calculate_hit_probability(strong, defender)["expected_damage"]
            > calculate_hit_probability(weak, defender)["expected_damage"])


# --- Cycle 2: incoming_threat in state dict ---

def test_incoming_threat_in_state():
    """build_state result has incoming_threat in state['me']."""
    me = _make_bot("A")
    enemy = _make_bot("B", x=5, y=5)
    state = build_state(me, [me, enemy], round_num=1, grid_size=10, storm_border=0)
    assert "incoming_threat" in state["me"]


def test_incoming_threat_is_list():
    """incoming_threat should be a list."""
    me = _make_bot("A")
    enemy = _make_bot("B", x=5, y=5)
    state = build_state(me, [me, enemy], round_num=1, grid_size=10, storm_border=0)
    assert isinstance(state["me"]["incoming_threat"], list)


def test_incoming_threat_count_matches_enemies():
    """Length of incoming_threat matches the number of alive enemies."""
    me = _make_bot("A")
    e1 = _make_bot("B", x=3, y=3)
    e2 = _make_bot("C", x=5, y=5)
    dead = _make_bot("D", x=7, y=7)
    dead.alive = False
    state = build_state(me, [me, e1, e2, dead], round_num=1, grid_size=10, storm_border=0)
    assert len(state["me"]["incoming_threat"]) == 2


# --- Cycle 3: threat entry shape and sorting ---

def test_incoming_threat_has_emoji():
    """Each threat entry has an 'emoji' key."""
    me = _make_bot("A")
    enemy = _make_bot("B", x=5, y=5)
    state = build_state(me, [me, enemy], round_num=1, grid_size=10, storm_border=0)
    assert state["me"]["incoming_threat"][0]["emoji"] == "B"


def test_incoming_threat_has_hit_chance():
    """Each threat entry has a float 'hit_chance'."""
    me = _make_bot("A")
    enemy = _make_bot("B", x=5, y=5)
    state = build_state(me, [me, enemy], round_num=1, grid_size=10, storm_border=0)
    hc = state["me"]["incoming_threat"][0]["hit_chance"]
    assert isinstance(hc, float)


def test_incoming_threat_has_expected_damage():
    """Each threat entry has a float 'expected_damage'."""
    me = _make_bot("A")
    enemy = _make_bot("B", x=5, y=5)
    state = build_state(me, [me, enemy], round_num=1, grid_size=10, storm_border=0)
    ed = state["me"]["incoming_threat"][0]["expected_damage"]
    assert isinstance(ed, float)


def test_incoming_threat_sorted_by_damage():
    """Threats sorted by expected_damage descending."""
    me = _make_bot("A")
    weak = _make_bot("W", x=3, y=3,
                     alloc=StatAllocation(15, 50, 15, 20))  # low-power specialist
    strong = _make_bot("S", x=5, y=5,
                       alloc=StatAllocation(70, 10, 10, 10))  # extreme power
    state = build_state(me, [me, weak, strong], round_num=1, grid_size=10, storm_border=0)
    threats = state["me"]["incoming_threat"]
    assert threats[0]["emoji"] == "S"
    assert threats[0]["expected_damage"] >= threats[1]["expected_damage"]


def test_high_power_enemy_ranks_higher():
    """Enemy with extreme POWER ranks above low-power enemy in threat list."""
    me = _make_bot("A")
    low_power_enemy = _make_bot("D", x=2, y=2,
                                alloc=StatAllocation(15, 50, 15, 20))
    power_enemy = _make_bot("P", x=4, y=4,
                            alloc=StatAllocation(70, 10, 10, 10))
    state = build_state(me, [me, low_power_enemy, power_enemy],
                        round_num=1, grid_size=10, storm_border=0)
    threats = state["me"]["incoming_threat"]
    assert threats[0]["emoji"] == "P"
