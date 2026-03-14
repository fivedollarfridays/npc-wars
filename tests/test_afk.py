"""Tests for AFK detection and bot fallback."""

from engine.afk import AFKTracker, AFK_THRESHOLD, KICK_THRESHOLD


# --- Cycle 1: Registration and initial state ---

def test_constants():
    """AFK threshold is 3, kick threshold is 10."""
    assert AFK_THRESHOLD == 3
    assert KICK_THRESHOLD == 10


def test_register_initial_state():
    """Newly registered player starts with zero misses, not AFK, not kicked."""
    tracker = AFKTracker()
    tracker.register("🐍")
    status = tracker.get_status("🐍")
    assert status == {"afk": False, "kicked": False, "consecutive_misses": 0}


def test_is_afk_initial():
    """Newly registered player is not AFK."""
    tracker = AFKTracker()
    tracker.register("🐍")
    assert tracker.is_afk("🐍") is False


def test_is_kicked_initial():
    """Newly registered player is not kicked."""
    tracker = AFKTracker()
    tracker.register("🐍")
    assert tracker.is_kicked("🐍") is False


# --- Cycle 2: Misses below AFK threshold ---

def test_one_miss_not_afk():
    """A single miss does not trigger AFK."""
    tracker = AFKTracker()
    tracker.register("🐍")
    tracker.record_miss("🐍")
    assert tracker.is_afk("🐍") is False
    assert tracker.get_status("🐍")["consecutive_misses"] == 1


def test_two_misses_not_afk():
    """Two consecutive misses do not trigger AFK."""
    tracker = AFKTracker()
    tracker.register("🐍")
    tracker.record_miss("🐍")
    tracker.record_miss("🐍")
    assert tracker.is_afk("🐍") is False
    assert tracker.get_status("🐍")["consecutive_misses"] == 2


# --- Cycle 3: AFK at threshold ---

def test_three_misses_triggers_afk():
    """Three consecutive misses trigger AFK status."""
    tracker = AFKTracker()
    tracker.register("🐍")
    for _ in range(3):
        tracker.record_miss("🐍")
    assert tracker.is_afk("🐍") is True
    assert tracker.is_kicked("🐍") is False


def test_five_misses_still_afk_not_kicked():
    """Five misses: AFK but not kicked."""
    tracker = AFKTracker()
    tracker.register("🐍")
    for _ in range(5):
        tracker.record_miss("🐍")
    assert tracker.is_afk("🐍") is True
    assert tracker.is_kicked("🐍") is False
    assert tracker.get_status("🐍")["consecutive_misses"] == 5


# --- Cycle 4: Kick at threshold ---

def test_ten_misses_triggers_kick():
    """Ten consecutive misses trigger kicked status."""
    tracker = AFKTracker()
    tracker.register("🐍")
    for _ in range(10):
        tracker.record_miss("🐍")
    assert tracker.is_kicked("🐍") is True
    assert tracker.is_afk("🐍") is True


def test_nine_misses_not_kicked():
    """Nine misses: AFK but not kicked."""
    tracker = AFKTracker()
    tracker.register("🐍")
    for _ in range(9):
        tracker.record_miss("🐍")
    assert tracker.is_kicked("🐍") is False
    assert tracker.is_afk("🐍") is True


# --- Cycle 5: Input resets counter ---

def test_input_resets_miss_counter():
    """A successful input resets consecutive misses to zero."""
    tracker = AFKTracker()
    tracker.register("🐍")
    tracker.record_miss("🐍")
    tracker.record_miss("🐍")
    tracker.record_input("🐍")
    assert tracker.get_status("🐍")["consecutive_misses"] == 0
    assert tracker.is_afk("🐍") is False


def test_input_clears_afk_flag():
    """Input after being AFK clears the AFK flag."""
    tracker = AFKTracker()
    tracker.register("🐍")
    for _ in range(4):
        tracker.record_miss("🐍")
    assert tracker.is_afk("🐍") is True
    tracker.record_input("🐍")
    assert tracker.is_afk("🐍") is False
    assert tracker.get_status("🐍")["consecutive_misses"] == 0


# --- Cycle 6: Kicked persists, multiple players ---

def test_kicked_persists_after_input():
    """Once kicked, input does not unkick the player."""
    tracker = AFKTracker()
    tracker.register("🐍")
    for _ in range(10):
        tracker.record_miss("🐍")
    assert tracker.is_kicked("🐍") is True
    tracker.record_input("🐍")
    assert tracker.is_kicked("🐍") is True


def test_multiple_players_independent():
    """Each player's tracking is independent."""
    tracker = AFKTracker()
    tracker.register("🐍")
    tracker.register("🦊")
    for _ in range(3):
        tracker.record_miss("🐍")
    tracker.record_miss("🦊")
    assert tracker.is_afk("🐍") is True
    assert tracker.is_afk("🦊") is False
