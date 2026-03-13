"""Integration tests validating the full Sprint 9 progression pipeline."""

import json
from pathlib import Path

from data.player_profiles import (
    BUDGET_BASE,
    BUDGET_CAP,
    BUDGET_PER_WIN,
    BUDGET_STREAK_REWARDS,
    PlayerProfile,
    calculate_line_budget,
    load_profiles,
    update_streak,
)
from engine.bot_scanner import count_decide_lines, validate_line_budget
from engine.game import run_match
from engine.sandbox import BASE_ACTIONS, validate_action
from engine.state import build_state
from tests.conftest import always_rest, bot_config, chase_and_attack


# ---------------------------------------------------------------------------
# Helper bots for new actions
# ---------------------------------------------------------------------------

def ranged_bot(state: dict) -> tuple:
    me = state["me"]
    if me["energy"] >= 20:
        return ("ranged_attack", "north")
    return ("rest",)


def dash_bot(state: dict) -> tuple:
    me = state["me"]
    if me["energy"] >= 15:
        return ("dash", "east")
    return ("rest",)


def taunt_bot(state: dict) -> tuple:
    me = state["me"]
    if me["energy"] >= 10:
        return ("taunt",)
    return ("rest",)


def _config_with_unlocks(
    name: str, emoji: str, decide_func: object, unlocks: list[str],
) -> dict:
    """Create a bot config with unlocked_actions."""
    cfg = bot_config(name, emoji, decide_func)
    cfg["unlocked_actions"] = unlocks
    return cfg


def _make_configs(count: int) -> list[dict]:
    """Build N aggressive bot configs with unique authors."""
    configs = []
    for i in range(count):
        cfg = bot_config(f"Bot{i}", chr(0x1F600 + i), chase_and_attack)
        cfg["author"] = f"author_{i}"
        configs.append(cfg)
    return configs


# ---------------------------------------------------------------------------
# TestProfilePersistence
# ---------------------------------------------------------------------------

class TestProfilePersistence:
    def test_profiles_persist_after_run_match(self, tmp_path: Path) -> None:
        """Profiles file is created when profiles_path is provided."""
        profiles_path = tmp_path / "profiles.json"
        configs = _make_configs(3)
        run_match(configs, match_id=1, seed=7, profiles_path=profiles_path)
        assert profiles_path.exists()
        data = json.loads(profiles_path.read_text())
        assert len(data) == 3

    def test_winner_profile_updated_after_match(self, tmp_path: Path) -> None:
        """Winner's profile shows updated wins and streak."""
        profiles_path = tmp_path / "profiles.json"
        configs = _make_configs(3)
        result = run_match(configs, match_id=1, seed=7, profiles_path=profiles_path)
        winner_emoji = result["winner"]
        assert winner_emoji != "none", "Need a seed that produces a winner"
        profiles = load_profiles(profiles_path)
        winner_profiles = [p for p in profiles.values() if p.emoji == winner_emoji]
        assert len(winner_profiles) == 1
        assert winner_profiles[0].wins >= 1
        assert winner_profiles[0].current_streak >= 1

    def test_multiple_matches_accumulate_wins(self, tmp_path: Path) -> None:
        """Running multiple matches accumulates wins correctly."""
        profiles_path = tmp_path / "profiles.json"
        configs = _make_configs(3)
        # Run 3 matches with same seed so same bot wins each time
        for i in range(3):
            run_match(configs, match_id=i + 1, seed=7, profiles_path=profiles_path)
        profiles = load_profiles(profiles_path)
        # Same seed means same winner each time -> that bot has 3 wins
        total_wins = sum(p.wins for p in profiles.values())
        assert total_wins == 3
        max_wins = max(p.wins for p in profiles.values())
        assert max_wins == 3


# ---------------------------------------------------------------------------
# TestLineBudgetProgression
# ---------------------------------------------------------------------------

class TestLineBudgetProgression:
    def test_new_bot_starts_with_budget_50(self) -> None:
        """A fresh profile has budget == BUDGET_BASE (50)."""
        profile = PlayerProfile(player_id="new", bot_name="NewBot", emoji="N")
        assert profile.line_budget == BUDGET_BASE
        assert profile.line_budget == 50

    def test_after_one_win_budget_increases_to_60(self) -> None:
        """After 1 win, budget = 50 + 10 = 60."""
        profile = PlayerProfile(player_id="w1", bot_name="W1", emoji="W")
        profile.wins = 1
        budget = calculate_line_budget(profile)
        assert budget == BUDGET_BASE + BUDGET_PER_WIN
        assert budget == 60

    def test_budget_capped_at_200(self) -> None:
        """Budget never exceeds BUDGET_CAP (200)."""
        profile = PlayerProfile(player_id="cap", bot_name="Cap", emoji="C")
        profile.wins = 100  # Would give 50 + 1000 = 1050 without cap
        budget = calculate_line_budget(profile)
        assert budget == BUDGET_CAP
        assert budget == 200


# ---------------------------------------------------------------------------
# TestStreakTracking
# ---------------------------------------------------------------------------

class TestStreakTracking:
    def test_consecutive_wins_build_streak(self) -> None:
        """Consecutive wins increment current_streak."""
        profile = PlayerProfile(player_id="s", bot_name="S", emoji="S")
        for _ in range(5):
            update_streak(profile, is_winner=True)
        assert profile.current_streak == 5
        assert profile.best_streak == 5

    def test_loss_resets_current_preserves_best(self) -> None:
        """Loss resets current_streak but preserves best_streak."""
        profile = PlayerProfile(player_id="s", bot_name="S", emoji="S")
        for _ in range(3):
            update_streak(profile, is_winner=True)
        assert profile.best_streak == 3
        update_streak(profile, is_winner=False)
        assert profile.current_streak == 0
        assert profile.best_streak == 3

    def test_streak_bonuses_applied_to_budget(self) -> None:
        """Streak bonuses from BUDGET_STREAK_REWARDS applied correctly."""
        profile = PlayerProfile(player_id="s", bot_name="S", emoji="S")
        profile.best_streak = 5  # Should get 25 bonus
        budget = calculate_line_budget(profile)
        expected = BUDGET_BASE + BUDGET_STREAK_REWARDS[5]
        assert budget == expected
        assert budget == 75  # 50 + 25


# ---------------------------------------------------------------------------
# TestActionUnlockFlow
# ---------------------------------------------------------------------------

class TestActionUnlockFlow:
    def test_base_actions_only_without_unlocks(self) -> None:
        """Bot with no extra unlocks can only use base 4 actions."""
        unlocked = set(BASE_ACTIONS)
        for action in ["move", "attack", "rest", "defend"]:
            args = (action, "north") if action in ("move", "attack") else (action,)
            result = validate_action(args, unlocked_actions=unlocked)
            assert result is not None, f"{action} should be allowed"
        # Non-base actions should be rejected
        assert validate_action(("ranged_attack", "north"), unlocked_actions=unlocked) is None
        assert validate_action(("dash", "east"), unlocked_actions=unlocked) is None
        assert validate_action(("taunt",), unlocked_actions=unlocked) is None

    def test_unlocked_ranged_attack_accepted(self) -> None:
        """Bot with ranged_attack in unlocked_actions can use it."""
        unlocked = {"move", "attack", "rest", "defend", "ranged_attack"}
        result = validate_action(("ranged_attack", "north"), unlocked_actions=unlocked)
        assert result == ("ranged_attack", "north")

    def test_locked_ranged_attack_rejected(self) -> None:
        """Ranged attack rejected when not in unlocked_actions."""
        unlocked = {"move", "attack", "rest", "defend"}
        result = validate_action(("ranged_attack", "north"), unlocked_actions=unlocked)
        assert result is None

    def test_locked_dash_rejected_unlocked_accepted(self) -> None:
        """Dash rejected when locked, accepted when unlocked."""
        base_only = {"move", "attack", "rest", "defend"}
        assert validate_action(("dash", "east"), unlocked_actions=base_only) is None
        with_dash = base_only | {"dash"}
        result = validate_action(("dash", "east"), unlocked_actions=with_dash)
        assert result == ("dash", "east")


# ---------------------------------------------------------------------------
# TestNewActionsInMatch
# ---------------------------------------------------------------------------

class TestNewActionsInMatch:
    def test_match_with_ranged_attack_runs_clean(self) -> None:
        """Full match with ranged_attack bots completes without error."""
        all_actions = ["move", "attack", "rest", "defend", "ranged_attack"]
        configs = [
            _config_with_unlocks("Ranger", "R", ranged_bot, all_actions),
            _config_with_unlocks("Chaser", "C", chase_and_attack, all_actions),
            bot_config("Rester", "Z", always_rest),
        ]
        result = run_match(configs, match_id=1, seed=42)
        assert result["winner"] != "none"

    def test_match_with_dash_runs_clean(self) -> None:
        """Full match with dash bots completes without error."""
        all_actions = ["move", "attack", "rest", "defend", "dash"]
        configs = [
            _config_with_unlocks("Dasher", "D", dash_bot, all_actions),
            _config_with_unlocks("Chaser", "C", chase_and_attack, all_actions),
            bot_config("Rester", "Z", always_rest),
        ]
        result = run_match(configs, match_id=1, seed=42)
        assert result["winner"] != "none"

    def test_match_with_taunt_runs_clean(self) -> None:
        """Full match with taunt bots completes without error."""
        all_actions = ["move", "attack", "rest", "defend", "taunt"]
        configs = [
            _config_with_unlocks("Taunter", "T", taunt_bot, all_actions),
            _config_with_unlocks("Chaser", "C", chase_and_attack, all_actions),
            bot_config("Rester", "Z", always_rest),
        ]
        result = run_match(configs, match_id=1, seed=42)
        assert result["winner"] != "none"

    def test_match_result_has_expected_keys(self) -> None:
        """Match result dict includes all standard keys."""
        configs = _make_configs(3)
        result = run_match(configs, match_id=1, seed=7)
        expected_keys = {
            "match_id", "date", "grid_size", "players", "rounds",
            "eliminations", "winner", "stats", "duration_rounds",
        }
        assert expected_keys.issubset(result.keys())


# ---------------------------------------------------------------------------
# TestLineBudgetEnforcement
# ---------------------------------------------------------------------------

class TestLineBudgetEnforcement:
    def test_count_decide_lines_correct(self) -> None:
        """count_decide_lines returns correct count for a sample bot."""
        source = (
            "def decide(state):\n"
            "    me = state['me']\n"
            "    if me['energy'] >= 20:\n"
            "        return ('ranged_attack', 'north')\n"
            "    return ('rest',)\n"
        )
        assert count_decide_lines(source) == 4

    def test_validate_line_budget_raises_when_over(self) -> None:
        """validate_line_budget raises ValueError when over budget."""
        source = (
            "def decide(state):\n"
            "    a = 1\n"
            "    b = 2\n"
            "    c = 3\n"
            "    return ('rest',)\n"
        )
        import pytest
        with pytest.raises(ValueError, match="budget"):
            validate_line_budget(source, budget=2)

    def test_validate_line_budget_passes_when_under(self) -> None:
        """validate_line_budget passes when under budget."""
        source = (
            "def decide(state):\n"
            "    return ('rest',)\n"
        )
        # Should not raise
        validate_line_budget(source, budget=50)


# ---------------------------------------------------------------------------
# TestStateDictProgression
# ---------------------------------------------------------------------------

class TestStateDictProgression:
    def _make_bot_with_state(self) -> dict:
        """Create a bot and return its state dict."""
        from engine.combat import Bot
        bot = Bot(
            name="Test", emoji="T", bio="t", author="t",
            decide_func=lambda s: ("rest",), x=5, y=5,
        )
        bot.unlocked_actions = ["move", "attack", "rest", "defend", "ranged_attack"]
        bot.line_budget = 75
        bot.win_streak = 3
        return build_state(bot, [bot], 1, 15, 0)

    def test_state_includes_unlocked_actions(self) -> None:
        """State dict me field includes unlocked_actions."""
        state = self._make_bot_with_state()
        assert "unlocked_actions" in state["me"]
        assert "ranged_attack" in state["me"]["unlocked_actions"]

    def test_state_includes_line_budget(self) -> None:
        """State dict me field includes line_budget."""
        state = self._make_bot_with_state()
        assert "line_budget" in state["me"]
        assert state["me"]["line_budget"] == 75

    def test_state_includes_win_streak(self) -> None:
        """State dict me field includes win_streak."""
        state = self._make_bot_with_state()
        assert "win_streak" in state["me"]
        assert state["me"]["win_streak"] == 3
