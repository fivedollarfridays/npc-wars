"""Tests for S57 spectacle drama tuning — lowered thresholds + new event weights."""

from engine.spectacle import (
    DRAMA_WEIGHTS,
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
# Cycle 1 — Lowered tier thresholds
# ---------------------------------------------------------------------------

class TestTierThresholds:
    """Verify lowered tier boundaries so higher tiers actually trigger."""

    def test_calm_at_zero(self):
        eng = SpectacleEngine()
        assert eng.classify_tier(0) == "calm"

    def test_calm_upper_bound_is_2(self):
        eng = SpectacleEngine()
        assert eng.classify_tier(2) == "calm"

    def test_heating_starts_at_3(self):
        eng = SpectacleEngine()
        assert eng.classify_tier(3) == "heating"

    def test_heating_upper_bound_is_5(self):
        eng = SpectacleEngine()
        assert eng.classify_tier(5) == "heating"

    def test_intense_starts_at_6(self):
        eng = SpectacleEngine()
        assert eng.classify_tier(6) == "intense"

    def test_intense_upper_bound_is_9(self):
        eng = SpectacleEngine()
        assert eng.classify_tier(9) == "intense"

    def test_hype_starts_at_10(self):
        eng = SpectacleEngine()
        assert eng.classify_tier(10) == "hype"

    def test_hype_upper_bound_is_14(self):
        eng = SpectacleEngine()
        assert eng.classify_tier(14) == "hype"

    def test_chaos_starts_at_15(self):
        eng = SpectacleEngine()
        assert eng.classify_tier(15) == "chaos"

    def test_chaos_at_high_score(self):
        eng = SpectacleEngine()
        assert eng.classify_tier(50) == "chaos"

    def test_single_kill_reaches_heating(self):
        """A single kill should push into at least heating."""
        score = DRAMA_WEIGHTS["kill"]
        eng = SpectacleEngine()
        tier = eng.classify_tier(score)
        assert tier in ("heating", "intense"), f"Kill score {score} gave tier {tier}"

    def test_two_kills_reach_intense(self):
        """Two kills in one round should reach intense or higher."""
        score = DRAMA_WEIGHTS["kill"] * 2
        eng = SpectacleEngine()
        tier = eng.classify_tier(score)
        assert tier in ("intense", "hype"), f"Two kill score {score} gave tier {tier}"

    def test_kill_plus_near_death_reaches_intense_or_higher(self):
        """Kill + near_death should reach intense or higher."""
        score = DRAMA_WEIGHTS["kill"] + DRAMA_WEIGHTS["near_death"]
        eng = SpectacleEngine()
        tier = eng.classify_tier(score)
        assert tier in ("intense", "hype", "chaos"), (
            f"kill+near_death score {score} gave tier {tier}"
        )

    def test_hype_reachable_with_two_kills_and_chain_bump(self):
        """Two kills + chain_bump (4+4+2=10) should reach hype."""
        score = DRAMA_WEIGHTS["kill"] * 2 + DRAMA_WEIGHTS["chain_bump"]
        eng = SpectacleEngine()
        tier = eng.classify_tier(score)
        assert tier == "hype", f"2kill+chain_bump score {score} gave tier {tier}"

    def test_chaos_reachable(self):
        """Three or more dramatic events should reach chaos."""
        score = DRAMA_WEIGHTS["kill"] * 2 + DRAMA_WEIGHTS["near_death"] + DRAMA_WEIGHTS["multi_kill"]
        eng = SpectacleEngine()
        tier = eng.classify_tier(score)
        assert tier == "chaos", f"2kill+near_death+multi_kill score {score} gave tier {tier}"


# ---------------------------------------------------------------------------
# Cycle 2 — New event weights exist in DRAMA_WEIGHTS
# ---------------------------------------------------------------------------

class TestNewEventWeights:
    """New event types exist in DRAMA_WEIGHTS with expected values."""

    def test_multi_kill_weight_exists(self):
        assert "multi_kill" in DRAMA_WEIGHTS
        assert DRAMA_WEIGHTS["multi_kill"] == 6

    def test_last_two_alive_weight_exists(self):
        assert "last_two_alive" in DRAMA_WEIGHTS
        assert DRAMA_WEIGHTS["last_two_alive"] == 5

    def test_storm_kill_weight_exists(self):
        assert "storm_kill" in DRAMA_WEIGHTS
        assert DRAMA_WEIGHTS["storm_kill"] == 3

    def test_low_hp_combat_weight_exists(self):
        assert "low_hp_combat" in DRAMA_WEIGHTS
        assert DRAMA_WEIGHTS["low_hp_combat"] == 2

    def test_kill_weight_increased_to_4(self):
        assert DRAMA_WEIGHTS["kill"] == 4


# ---------------------------------------------------------------------------
# Cycle 3 — score_round detects new event types
# ---------------------------------------------------------------------------

class TestScoreRoundNewEvents:
    """score_round correctly detects and scores new event types."""

    def test_empty_round_is_calm(self):
        eng = SpectacleEngine()
        result = eng.score_round([], [])
        assert result.tier == "calm"
        assert result.drama_score == 0

    def test_kill_round_not_calm(self):
        """A round with a kill should NOT be calm with new thresholds."""
        eng = SpectacleEngine()
        events = [_evt("kill", attacker="A", victim="B")]
        result = eng.score_round(events, [_bot("A", 50), _bot("C", 50)])
        assert result.tier != "calm", f"Kill round was {result.tier}"

    def test_multi_kill_bonus_on_two_kills(self):
        """Two kills in one round triggers multi_kill bonus."""
        eng = SpectacleEngine()
        events = [
            _evt("kill", attacker="A", victim="B"),
            _evt("kill", attacker="A", victim="C"),
        ]
        bots = [_bot("A", 50), _bot("D", 50)]
        result = eng.score_round(events, bots)
        # 2 kills (4+4=8) + multi_kill bonus (6) = 14
        assert result.drama_score >= DRAMA_WEIGHTS["kill"] * 2 + DRAMA_WEIGHTS["multi_kill"]

    def test_last_two_alive_boosts_score(self):
        """When only 2 bots remain alive, last_two_alive bonus applies."""
        eng = SpectacleEngine()
        bots = [_bot("A", 50), _bot("B", 30)]
        result = eng.score_round([], bots)
        assert result.drama_score >= DRAMA_WEIGHTS["last_two_alive"]

    def test_storm_kill_boosts_score(self):
        """A storm kill adds storm_kill weight to the score."""
        eng = SpectacleEngine()
        events = [_evt("kill", attacker="storm", victim="X", cause="storm")]
        bots = [_bot("A", 50), _bot("B", 50), _bot("C", 50)]
        result = eng.score_round(events, bots)
        # kill(4) + storm_kill(3) = 7
        assert result.drama_score >= DRAMA_WEIGHTS["kill"] + DRAMA_WEIGHTS["storm_kill"]

    def test_low_hp_combat_detected(self):
        """Hit event between two low-HP bots triggers low_hp_combat."""
        eng = SpectacleEngine()
        events = [_evt("hit", attacker="A", target="B", attacker_hp=20, target_hp=15)]
        bots = [_bot("A", 20), _bot("B", 15), _bot("C", 80)]
        result = eng.score_round(events, bots)
        assert result.drama_score >= DRAMA_WEIGHTS["low_hp_combat"]

    def test_no_multi_kill_on_single_kill(self):
        """Single kill should NOT get multi_kill bonus."""
        eng = SpectacleEngine()
        events = [_evt("kill", attacker="A", victim="B")]
        bots = [_bot("A", 50), _bot("C", 50), _bot("D", 50)]
        result = eng.score_round(events, bots)
        # kill(4) only, no multi_kill
        assert result.drama_score == DRAMA_WEIGHTS["kill"]

    def test_combined_new_events_reach_chaos(self):
        """Multiple new events in one round should push into chaos."""
        eng = SpectacleEngine()
        events = [
            _evt("kill", attacker="A", victim="B"),
            _evt("kill", attacker="A", victim="C", cause="storm"),
            _evt("hit", attacker="A", target="D", attacker_hp=10, target_hp=25),
        ]
        bots = [_bot("A", 10), _bot("D", 25)]  # 2 alive, low HP combat
        result = eng.score_round(events, bots)
        assert result.tier == "chaos", f"Combined events gave tier {result.tier} (score={result.drama_score})"
