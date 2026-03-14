"""Tests for engine/spectacle.py — drama scoring and trigger-to-effect map."""

import pytest

from engine.spectacle import (
    DRAMA_WEIGHTS,
    SpectacleData,
    SpectacleEngine,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _bot(emoji: str, hp: int, alive: bool = True) -> dict:
    return {"emoji": emoji, "hp": hp, "alive": alive}


def _evt(event_type: str, **kwargs) -> dict:
    return {"type": event_type, **kwargs}


# ---------------------------------------------------------------------------
# T10.1 — Drama Scoring
# ---------------------------------------------------------------------------

class TestScoreRoundBasics:
    """score_round returns SpectacleData with correct drama_score."""

    def test_returns_spectacle_data(self):
        eng = SpectacleEngine()
        result = eng.score_round([], [])
        assert isinstance(result, SpectacleData)
        assert isinstance(result.drama_score, int)

    def test_empty_round_scores_zero(self):
        eng = SpectacleEngine()
        result = eng.score_round([], [])
        assert result.drama_score == 0

    def test_kill_adds_3(self):
        eng = SpectacleEngine()
        events = [_evt("kill", attacker="A", victim="B")]
        result = eng.score_round(events, [])
        assert result.drama_score == DRAMA_WEIGHTS["kill"]
        assert result.drama_score == 3

    def test_chain_bump_adds_2(self):
        eng = SpectacleEngine()
        events = [_evt("chain_bump")]
        result = eng.score_round(events, [])
        assert result.drama_score == DRAMA_WEIGHTS["chain_bump"]
        assert result.drama_score == 2

    def test_near_death_detection(self):
        eng = SpectacleEngine()
        bots = [_bot("X", hp=3), _bot("Y", hp=50)]
        result = eng.score_round([], bots)
        assert result.drama_score == DRAMA_WEIGHTS["near_death"]
        assert result.drama_score == 4

    def test_kill_streak_adds_5(self):
        eng = SpectacleEngine()
        events = [_evt("kill_streak", attacker="A")]
        result = eng.score_round(events, [])
        assert result.drama_score == DRAMA_WEIGHTS["kill_streak"]
        assert result.drama_score == 5

    def test_watcher_sync_adds_3(self):
        eng = SpectacleEngine()
        events = [_evt("watcher_sync")]
        result = eng.score_round(events, [])
        assert result.drama_score == DRAMA_WEIGHTS["watcher_sync"]
        assert result.drama_score == 3


class TestScoreRoundAccumulation:
    """Multiple event types accumulate correctly."""

    def test_multiple_events_accumulate(self):
        eng = SpectacleEngine()
        events = [
            _evt("kill", attacker="A", victim="B"),
            _evt("kill", attacker="C", victim="D"),
            _evt("chain_bump"),
            _evt("kill_streak", attacker="A"),
        ]
        bots = [_bot("Z", hp=2)]  # near-death
        result = eng.score_round(events, bots)
        expected = 3 + 3 + 2 + 5 + 4  # 17
        assert result.drama_score == expected

    def test_near_deaths_field_has_emoji_list(self):
        eng = SpectacleEngine()
        bots = [_bot("X", hp=1), _bot("Y", hp=4), _bot("Z", hp=50)]
        result = eng.score_round([], bots)
        assert result.near_deaths == ["X", "Y"]

    def test_dead_bot_not_near_death(self):
        eng = SpectacleEngine()
        bots = [_bot("X", hp=3, alive=False)]
        result = eng.score_round([], bots)
        assert result.near_deaths == []
        assert result.drama_score == 0

    def test_hp_zero_not_near_death(self):
        eng = SpectacleEngine()
        bots = [_bot("X", hp=0, alive=True)]
        result = eng.score_round([], bots)
        assert result.near_deaths == []

    def test_hp_five_not_near_death(self):
        eng = SpectacleEngine()
        bots = [_bot("X", hp=5, alive=True)]
        result = eng.score_round([], bots)
        assert result.near_deaths == []


# ---------------------------------------------------------------------------
# T10.2 — Tier Classification
# ---------------------------------------------------------------------------

class TestTierClassification:
    """classify_tier boundary tests."""

    @pytest.mark.parametrize(
        "score, expected_tier",
        [
            (0, "calm"),
            (3, "calm"),
            (4, "heating"),
            (7, "heating"),
            (8, "intense"),
            (12, "intense"),
            (13, "hype"),
            (18, "hype"),
            (19, "chaos"),
            (25, "chaos"),
        ],
    )
    def test_tier_boundaries(self, score: int, expected_tier: str):
        eng = SpectacleEngine()
        assert eng.classify_tier(score) == expected_tier


# ---------------------------------------------------------------------------
# T10.2 — Trigger-to-Effect Map
# ---------------------------------------------------------------------------

class TestTriggerEffects:
    """select_effects returns correct effects for triggers."""

    def test_kill_trigger_shatter(self):
        eng = SpectacleEngine()
        events = [_evt("kill", attacker="A", victim="B")]
        effects = eng.select_effects(events, [])
        assert "shatter" in effects

    def test_kill_streak_trigger_fire_border(self):
        eng = SpectacleEngine()
        events = [_evt("kill_streak", attacker="A")]
        effects = eng.select_effects(events, [])
        assert "fire_border" in effects

    def test_near_death_trigger_slow_mo(self):
        eng = SpectacleEngine()
        bots = [_bot("X", hp=2)]
        effects = eng.select_effects([], bots)
        assert "slow_mo" in effects

    def test_chain_bump_trigger_multiball(self):
        eng = SpectacleEngine()
        events = [_evt("chain_bump")]
        effects = eng.select_effects(events, [])
        assert "multiball" in effects

    def test_last_2_alive_trigger_split_screen(self):
        eng = SpectacleEngine()
        bots = [_bot("A", hp=50), _bot("B", hp=30)]
        effects = eng.select_effects([], bots)
        assert "split_screen" in effects

    def test_storm_kill_trigger_glitch(self):
        eng = SpectacleEngine()
        events = [_evt("kill", attacker="storm", victim="X", cause="storm")]
        effects = eng.select_effects(events, [])
        assert "glitch" in effects

    def test_multiple_triggers_all_effects(self):
        eng = SpectacleEngine()
        events = [
            _evt("kill", attacker="A", victim="B"),
            _evt("chain_bump"),
        ]
        bots = [_bot("X", hp=2), _bot("Y", hp=40)]  # 2 alive, 1 near-death
        effects = eng.select_effects(events, bots)
        assert "shatter" in effects
        assert "multiball" in effects
        assert "slow_mo" in effects
        assert "split_screen" in effects


class TestSpectacleDataFields:
    """SpectacleData from score_round includes all fields."""

    def test_score_round_populates_all_fields(self):
        eng = SpectacleEngine()
        events = [_evt("kill", attacker="A", victim="B")]
        bots = [_bot("X", hp=2), _bot("Y", hp=80)]
        result = eng.score_round(events, bots)
        assert isinstance(result.drama_score, int)
        assert isinstance(result.tier, str)
        assert isinstance(result.triggers, list)
        assert isinstance(result.effects, list)
        assert isinstance(result.near_deaths, list)

    def test_score_round_tier_matches_score(self):
        eng = SpectacleEngine()
        # kill(3) + near_death(4) = 7 -> heating
        events = [_evt("kill", attacker="A", victim="B")]
        bots = [_bot("X", hp=1), _bot("Y", hp=80)]
        result = eng.score_round(events, bots)
        assert result.drama_score == 7
        assert result.tier == "heating"

    def test_kill_streak_from_3_kills_same_attacker(self):
        eng = SpectacleEngine()
        events = [
            _evt("kill", attacker="A", victim="B"),
            _evt("kill", attacker="A", victim="C"),
            _evt("kill", attacker="A", victim="D"),
        ]
        effects = eng.select_effects(events, [])
        assert "fire_border" in effects
