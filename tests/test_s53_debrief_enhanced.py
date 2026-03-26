"""Tests for enhanced debrief with Counter lesson + pattern table (T53.5)."""

from __future__ import annotations

from server.rival_debrief import analyze_rival_match
from server.rival_factory import RIVAL_EMOJI


# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------

def _mock_match(player_emoji="\U0001f916", rounds=None):
    return {
        "match_id": 1,
        "rounds": rounds or [],
        "eliminations": [],
        "winner": RIVAL_EMOJI,
        "stats": {},
    }


def _round_data(round_num, player_pos, rival_pos, events=None):
    return {
        "round": round_num,
        "storm_border": 0,
        "positions": [player_pos, rival_pos],
        "events": events or [],
    }


def _pos(emoji, x, y, hp, energy, action):
    return {
        "emoji": emoji, "x": x, "y": y, "hp": hp,
        "energy": energy, "action": action, "alive": True, "max_hp": 100,
    }


# ---------------------------------------------------------------------------
# Cycle 1: Counter debrief (tier 4)
# ---------------------------------------------------------------------------

class TestCounterDebrief:
    """Tier 4 analysis should show player patterns and counter info."""

    def test_tier_4_with_patterns_has_counter_analysis(self):
        patterns = {"at_range_1": {"attack": 0.7, "rest": 0.2, "defend": 0.1}}
        result = analyze_rival_match(_mock_match(), "\U0001f916", 4, pattern_data=patterns)
        assert result["tier"] == 4
        assert "patterns" in result
        lesson_lower = result["lesson"].lower()
        assert "counter" in lesson_lower or "pattern" in lesson_lower

    def test_tier_4_without_patterns_generic(self):
        result = analyze_rival_match(_mock_match(), "\U0001f916", 4)
        assert result["tier"] == 4
        assert "lesson" in result
        # Should mention patterns or learning
        assert "pattern" in result["lesson"].lower() or "learn" in result["lesson"].lower()

    def test_tier_4_shows_top_patterns(self):
        patterns = {
            "at_range_1": {"attack": 0.6, "rest": 0.3, "defend": 0.1},
            "below_30_hp": {"rest": 0.8, "move": 0.2},
        }
        result = analyze_rival_match(
            _mock_match(), "\U0001f916", 4, pattern_data=patterns,
        )
        assert "patterns" in result
        assert "at_range_1" in result["patterns"]
        assert "below_30_hp" in result["patterns"]

    def test_tier_4_has_top_patterns_list(self):
        patterns = {"at_range_1": {"attack": 0.7, "rest": 0.2, "defend": 0.1}}
        result = analyze_rival_match(
            _mock_match(), "\U0001f916", 4, pattern_data=patterns,
        )
        assert "top_patterns" in result
        assert len(result["top_patterns"]) >= 1
        top = result["top_patterns"][0]
        assert "context" in top
        assert "your_action" in top
        assert "probability" in top
        assert "counter_used" in top

    def test_tier_4_counter_lesson_mentions_frequency(self):
        patterns = {"at_range_1": {"attack": 0.8, "rest": 0.1, "defend": 0.1}}
        result = analyze_rival_match(
            _mock_match(), "\U0001f916", 4, pattern_data=patterns,
        )
        # Lesson should reference the probability
        assert "80%" in result["lesson"] or "0.8" in result["lesson"]


# ---------------------------------------------------------------------------
# Cycle 2: Economist debrief (tier 3) -- unchanged
# ---------------------------------------------------------------------------

class TestEconomistDebrief:
    def test_tier_3_has_energy_analysis(self):
        rounds = [
            _round_data(
                5,
                _pos("\U0001f916", 5, 5, 60, 15, "rest"),
                _pos(RIVAL_EMOJI, 6, 5, 90, 70, "attack west"),
            ),
        ]
        result = analyze_rival_match(_mock_match(rounds=rounds), "\U0001f916", 3)
        assert "energy" in result["lesson"].lower()
        assert "energy_starved_rounds" in result or "key_round" in result


# ---------------------------------------------------------------------------
# Cycle 3: Tiers 1 and 2 unchanged
# ---------------------------------------------------------------------------

class TestTier1And2Unchanged:
    def test_tier_1_still_works(self):
        result = analyze_rival_match(_mock_match(), "\U0001f916", 1)
        assert result["tier"] == 1
        assert "lesson" in result

    def test_tier_2_still_works(self):
        result = analyze_rival_match(_mock_match(), "\U0001f916", 2)
        assert result["tier"] == 2
        assert "lesson" in result


# ---------------------------------------------------------------------------
# Cycle 4: HTML pattern table
# ---------------------------------------------------------------------------

class TestDebriefHtml:
    def test_debrief_page_has_pattern_section(self):
        from pathlib import Path

        html = Path("server/static/debrief.html").read_text()
        assert "pattern" in html.lower()

    def test_debrief_page_has_pattern_table(self):
        from pathlib import Path

        html = Path("server/static/debrief.html").read_text()
        assert "pattern-table" in html or "pattern-body" in html

    def test_debrief_page_loads(self):
        from fastapi.testclient import TestClient

        from server.app import app
        from server.db import init_db

        old_db = getattr(app.state, "db", None)
        app.state.db = init_db(":memory:")
        client = TestClient(app)
        resp = client.get("/debrief/1")
        assert resp.status_code == 200
        app.state.db = old_db
