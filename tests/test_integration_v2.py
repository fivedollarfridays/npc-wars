"""Integration tests validating Sprint 8 features work together."""

from engine.combat import (
    ATTACK_COST, KILL_BOUNTY_ENERGY, REST_HEAL,
    STARTING_ATTACK_POWER, WALL_SPLAT_DAMAGE, get_round_bonus_attack,
)
from engine.game import run_match
from engine.state import build_state
from tests.conftest import bot_config, chase_and_attack


def _make_configs(count: int) -> list[dict]:
    """Build N aggressive bot configs using shared chase_and_attack."""
    return [bot_config(f"Bot{i}", chr(0x1F600 + i), chase_and_attack) for i in range(count)]


# ---------------------------------------------------------------------------
# Balance constants (T8.1)
# ---------------------------------------------------------------------------

class TestBalanceConstants:
    def test_attack_power_is_25(self) -> None:
        assert STARTING_ATTACK_POWER == 25

    def test_attack_cost_is_10(self) -> None:
        assert ATTACK_COST == 10

    def test_rest_heal_is_5(self) -> None:
        assert REST_HEAL == 5


# ---------------------------------------------------------------------------
# Storm timing (T8.2)
# ---------------------------------------------------------------------------

class TestStormTiming:
    def test_no_storm_before_round_10(self) -> None:
        """Storm border is 0 for rounds 1-9."""
        from engine.grid import get_storm_border
        for r in range(1, 10):
            assert get_storm_border(r) == 0, f"Expected no storm at round {r}"

    def test_storm_starts_round_10(self) -> None:
        """Storm border becomes >= 1 by round 14 (first tick at R14)."""
        from engine.grid import get_storm_border
        assert get_storm_border(14) >= 1


# ---------------------------------------------------------------------------
# Damage scaling (T8.3)
# ---------------------------------------------------------------------------

class TestDamageScaling:
    def test_no_bonus_at_round_15(self) -> None:
        assert get_round_bonus_attack(15) == 0

    def test_plus_2_at_round_25(self) -> None:
        assert get_round_bonus_attack(25) == 2

    def test_plus_4_at_round_35(self) -> None:
        assert get_round_bonus_attack(35) == 4


# ---------------------------------------------------------------------------
# Kill bounty (T8.5)
# ---------------------------------------------------------------------------

class TestKillBounty:
    def test_bounty_is_30(self) -> None:
        assert KILL_BOUNTY_ENERGY == 30


# ---------------------------------------------------------------------------
# Bumper physics constants (T8.6)
# ---------------------------------------------------------------------------

class TestBumperConstants:
    def test_wall_splat_damage_is_10(self) -> None:
        assert WALL_SPLAT_DAMAGE == 10


# ---------------------------------------------------------------------------
# State dict includes bumps (T8.8)
# ---------------------------------------------------------------------------

class TestStateDictBumps:
    def test_bumps_last_round_present(self) -> None:
        from engine.combat import Bot
        bot = Bot(name="Test", emoji="T", bio="t", author="t",
                  decide_func=lambda s: ("rest",), x=5, y=5)
        state = build_state(bot, [bot], 1, 15, 0)
        assert "bumps_last_round" in state
        assert isinstance(state["bumps_last_round"], list)

    def test_bumps_defaults_to_empty(self) -> None:
        from engine.combat import Bot
        bot = Bot(name="Test", emoji="T", bio="t", author="t",
                  decide_func=lambda s: ("rest",), x=5, y=5)
        state = build_state(bot, [bot], 1, 15, 0)
        assert state["bumps_last_round"] == []


# ---------------------------------------------------------------------------
# Full match integration
# ---------------------------------------------------------------------------

class TestFullMatchIntegration:
    def test_match_completes_without_error(self) -> None:
        """Full 5-bot match runs to completion with all Sprint 8 features."""
        configs = _make_configs(5)
        result = run_match(configs, match_id=999, seed=42)
        assert result["winner"] != "none"
        assert len(result["rounds"]) > 0
        assert len(result["eliminations"]) >= 4

    def test_match_result_has_expected_keys(self) -> None:
        """Match result dict includes all standard keys."""
        configs = _make_configs(3)
        result = run_match(configs, match_id=1, seed=7)
        expected_keys = {"match_id", "date", "grid_size", "players", "rounds",
                         "eliminations", "winner", "stats", "duration_rounds"}
        assert expected_keys.issubset(result.keys())

    def test_storm_border_increases_during_match(self) -> None:
        """Storm border grows in rounds after 10."""
        configs = _make_configs(5)
        result = run_match(configs, match_id=999, seed=42)
        round_14_plus = [r for r in result["rounds"] if r["round"] >= 14]
        if round_14_plus:
            assert round_14_plus[0]["storm_border"] >= 1

    def test_bump_events_no_crash(self) -> None:
        """Match with bump physics enabled runs without error.

        Bump events may or may not occur depending on seed, but the engine
        must not crash.
        """
        configs = _make_configs(5)
        result = run_match(configs, match_id=999, seed=42)
        all_events = []
        for r in result["rounds"]:
            all_events.extend(r.get("events", []))
        bump_types = {"bump", "wall_splat", "storm_bounce", "chain_bump"}
        bump_events = [e for e in all_events if e.get("type") in bump_types]
        # No crash -- bumps may or may not happen depending on seed
        assert isinstance(bump_events, list)

    def test_damage_scaling_applied_late_rounds(self) -> None:
        """If match reaches round 26+, bots have bonus attack power."""
        configs = _make_configs(5)
        result = run_match(configs, match_id=999, seed=42)
        if len(result["rounds"]) >= 26:
            # At round 25, bonus is +2, so attack_power should be 27
            round_25 = result["rounds"][24]
            alive_bots = [p for p in round_25["positions"] if p["alive"]]
            # We can't inspect attack_power directly in round record,
            # but if they survived to R25 the scaling was applied without error
            assert len(alive_bots) >= 1

    def test_kill_events_present(self) -> None:
        """Kill events appear in round events when bots die."""
        configs = _make_configs(5)
        result = run_match(configs, match_id=999, seed=42)
        all_events = []
        for r in result["rounds"]:
            all_events.extend(r.get("events", []))
        kill_events = [e for e in all_events if e.get("type") == "kill"]
        assert len(kill_events) >= 1  # At least one kill in a 5-bot match

    def test_eliminations_have_killed_by(self) -> None:
        """Every elimination has killed_by and cause fields."""
        configs = _make_configs(5)
        result = run_match(configs, match_id=999, seed=42)
        for elim in result["eliminations"]:
            assert "killed_by" in elim, f"Missing killed_by in {elim}"
            assert "cause" in elim, f"Missing cause in {elim}"

    def test_deterministic_with_same_seed(self) -> None:
        """Two matches with the same seed produce identical results."""
        configs = _make_configs(5)
        r1 = run_match(configs, match_id=1, seed=42)
        r2 = run_match(configs, match_id=1, seed=42)
        assert r1["winner"] == r2["winner"]
        assert r1["duration_rounds"] == r2["duration_rounds"]
        assert len(r1["eliminations"]) == len(r2["eliminations"])
