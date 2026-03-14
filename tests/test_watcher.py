"""Tests for The Cringe bot skeleton and emoji identity."""

from engine.combat import DEFAULT_UNLOCKED_ACTIONS
from engine.sandbox import validate_action
from engine.watcher import WATCHER_ACTIONS, WATCHER_EMOJI, WATCHER_NAME, WatcherBot


class TestWatcherIdentity:
    """Cycle 1: Watcher identity properties."""

    def test_emoji_is_eggplant(self) -> None:
        bot = WatcherBot(x=0, y=0)
        assert bot.emoji == "\U0001f346"

    def test_name_is_the_cringe(self) -> None:
        bot = WatcherBot(x=0, y=0)
        assert bot.name == "The Cringe"

    def test_is_watcher_true(self) -> None:
        bot = WatcherBot(x=0, y=0)
        assert bot.is_watcher is True

    def test_is_player_bot_false(self) -> None:
        bot = WatcherBot(x=0, y=0)
        assert bot.is_player_bot is False

    def test_watcher_emoji_constant(self) -> None:
        assert WATCHER_EMOJI == "\U0001f346"

    def test_watcher_name_constant(self) -> None:
        assert WATCHER_NAME == "The Cringe"


class TestWatcherActions:
    """Cycle 2: Watcher has all 7 actions unlocked."""

    def test_all_seven_actions_unlocked(self) -> None:
        bot = WatcherBot(x=0, y=0)
        expected = ["attack", "dash", "defend", "move", "ranged_attack", "rest", "taunt"]
        assert bot.unlocked_actions == expected

    def test_watcher_actions_constant(self) -> None:
        expected = ["attack", "dash", "defend", "move", "ranged_attack", "rest", "taunt"]
        assert WATCHER_ACTIONS == expected

    def test_decide_returns_rest_placeholder(self) -> None:
        bot = WatcherBot(x=0, y=0)
        result = bot.decide(state={})
        assert result == ("rest",)

    def test_decide_returns_tuple(self) -> None:
        bot = WatcherBot(x=0, y=0)
        result = bot.decide(state={})
        assert isinstance(result, tuple)


class TestWatcherFullActionAccess:
    """Cycle 3: Watcher bypasses unlock gating via validate_action."""

    def test_watcher_unlocked_actions_covers_all_seven(self) -> None:
        bot = WatcherBot(x=0, y=0)
        expected = {"attack", "dash", "defend", "move", "ranged_attack", "rest", "taunt"}
        assert set(bot.unlocked_actions) == expected

    def test_watcher_ranged_attack_validates(self) -> None:
        bot = WatcherBot(x=0, y=0)
        result = validate_action(("ranged_attack", "north"), unlocked_actions=set(bot.unlocked_actions))
        assert result == ("ranged_attack", "north")

    def test_watcher_dash_validates(self) -> None:
        bot = WatcherBot(x=0, y=0)
        result = validate_action(("dash", "south"), unlocked_actions=set(bot.unlocked_actions))
        assert result == ("dash", "south")

    def test_watcher_taunt_validates(self) -> None:
        bot = WatcherBot(x=0, y=0)
        result = validate_action(("taunt",), unlocked_actions=set(bot.unlocked_actions))
        assert result == ("taunt",)

    def test_regular_bot_ranged_attack_blocked(self) -> None:
        result = validate_action(("ranged_attack", "north"), unlocked_actions=set(DEFAULT_UNLOCKED_ACTIONS))
        assert result is None

    def test_regular_bot_dash_blocked(self) -> None:
        result = validate_action(("dash", "south"), unlocked_actions=set(DEFAULT_UNLOCKED_ACTIONS))
        assert result is None
