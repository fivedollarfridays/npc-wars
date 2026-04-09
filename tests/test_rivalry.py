"""Tests for engine/rivalry.py — pure rivalry computation."""

from engine.rivalry import compute_rivalry_stats, compute_rivalry_score, rivalry_trend


def _make_match(match_id, winner, players, eliminations=None, stats=None):
    """Build minimal match dict for rivalry tests."""
    return {
        "match_id": match_id,
        "date": f"2026-01-{match_id:02d}T00:00:00",
        "winner": winner,
        "players": [{"emoji": e} for e in players],
        "eliminations": eliminations or [],
        "stats": stats or {e: {"kills": 0, "damage_dealt": 0, "damage_taken": 0,
                                "rounds_survived": 5} for e in players},
        "duration_rounds": 10,
    }


# --- compute_rivalry_stats ---

class TestComputeRivalryStatsNoHistory:
    def test_empty_matches(self):
        result = compute_rivalry_stats("🤖", "🎯", [])
        assert result["wins_a"] == 0
        assert result["wins_b"] == 0
        assert result["matches"] == 0
        assert result["streak"] == 0

    def test_bots_never_met(self):
        matches = [_make_match(1, "🤖", ["🤖", "🐢"])]
        result = compute_rivalry_stats("🤖", "🎯", matches)
        assert result["matches"] == 0

    def test_same_bot(self):
        result = compute_rivalry_stats("🤖", "🤖", [])
        assert result["matches"] == 0


class TestComputeRivalryStatsSingleMatch:
    def test_a_wins(self):
        matches = [_make_match(1, "🤖", ["🤖", "🎯"])]
        result = compute_rivalry_stats("🤖", "🎯", matches)
        assert result["wins_a"] == 1
        assert result["wins_b"] == 0
        assert result["matches"] == 1
        assert result["streak"] == 1
        assert result["streak_holder"] == "🤖"

    def test_b_wins(self):
        matches = [_make_match(1, "🎯", ["🤖", "🎯"])]
        result = compute_rivalry_stats("🤖", "🎯", matches)
        assert result["wins_a"] == 0
        assert result["wins_b"] == 1
        assert result["streak"] == 1
        assert result["streak_holder"] == "🎯"

    def test_neither_wins(self):
        """Both in match but third party wins."""
        matches = [_make_match(1, "🐢", ["🤖", "🎯", "🐢"])]
        result = compute_rivalry_stats("🤖", "🎯", matches)
        assert result["matches"] == 1
        assert result["wins_a"] == 0
        assert result["wins_b"] == 0

    def test_kill_tracking(self):
        matches = [_make_match(1, "🤖", ["🤖", "🎯"],
                               eliminations=[{"emoji": "🎯", "killed_by": "🤖",
                                              "round": 5, "cause": "combat"}])]
        result = compute_rivalry_stats("🤖", "🎯", matches)
        assert result["kills_a"] == 1
        assert result["kills_b"] == 0


class TestComputeRivalryStatsMultipleMatches:
    def test_five_matches_mixed(self):
        matches = [
            _make_match(1, "🤖", ["🤖", "🎯"]),
            _make_match(2, "🎯", ["🤖", "🎯"]),
            _make_match(3, "🤖", ["🤖", "🎯"]),
            _make_match(4, "🤖", ["🤖", "🎯"]),
            _make_match(5, "🤖", ["🤖", "🎯"]),
        ]
        result = compute_rivalry_stats("🤖", "🎯", matches)
        assert result["wins_a"] == 4
        assert result["wins_b"] == 1
        assert result["matches"] == 5
        assert result["streak"] == 3
        assert result["streak_holder"] == "🤖"

    def test_streak_resets_on_loss(self):
        matches = [
            _make_match(1, "🤖", ["🤖", "🎯"]),
            _make_match(2, "🤖", ["🤖", "🎯"]),
            _make_match(3, "🎯", ["🤖", "🎯"]),
        ]
        result = compute_rivalry_stats("🤖", "🎯", matches)
        assert result["streak"] == 1
        assert result["streak_holder"] == "🎯"

    def test_skips_matches_without_both_bots(self):
        matches = [
            _make_match(1, "🤖", ["🤖", "🎯"]),
            _make_match(2, "🤖", ["🤖", "🐢"]),  # no 🎯
            _make_match(3, "🎯", ["🤖", "🎯"]),
        ]
        result = compute_rivalry_stats("🤖", "🎯", matches)
        assert result["matches"] == 2

    def test_accumulates_kills(self):
        matches = [
            _make_match(1, "🤖", ["🤖", "🎯"],
                        eliminations=[{"emoji": "🎯", "killed_by": "🤖",
                                       "round": 5, "cause": "combat"}]),
            _make_match(2, "🎯", ["🤖", "🎯"],
                        eliminations=[{"emoji": "🤖", "killed_by": "🎯",
                                       "round": 3, "cause": "combat"},
                                      {"emoji": "🎯", "killed_by": "🤖",
                                       "round": 7, "cause": "combat"}]),
        ]
        result = compute_rivalry_stats("🤖", "🎯", matches)
        assert result["kills_a"] == 2
        assert result["kills_b"] == 1


# --- compute_rivalry_score ---

class TestComputeRivalryScore:
    def test_no_matches_returns_50(self):
        stats = compute_rivalry_stats("🤖", "🎯", [])
        assert compute_rivalry_score(stats) == 50

    def test_total_dominance_a(self):
        matches = [_make_match(i, "🤖", ["🤖", "🎯"]) for i in range(1, 11)]
        stats = compute_rivalry_stats("🤖", "🎯", matches)
        score = compute_rivalry_score(stats)
        assert score == 100

    def test_total_dominance_b(self):
        matches = [_make_match(i, "🎯", ["🤖", "🎯"]) for i in range(1, 11)]
        stats = compute_rivalry_stats("🤖", "🎯", matches)
        score = compute_rivalry_score(stats)
        assert score == 0

    def test_even_split(self):
        matches = [
            _make_match(1, "🤖", ["🤖", "🎯"]),
            _make_match(2, "🎯", ["🤖", "🎯"]),
        ]
        stats = compute_rivalry_stats("🤖", "🎯", matches)
        score = compute_rivalry_score(stats)
        assert score == 50

    def test_score_in_range(self):
        matches = [
            _make_match(1, "🤖", ["🤖", "🎯"]),
            _make_match(2, "🤖", ["🤖", "🎯"]),
            _make_match(3, "🎯", ["🤖", "🎯"]),
        ]
        stats = compute_rivalry_stats("🤖", "🎯", matches)
        score = compute_rivalry_score(stats)
        assert 0 <= score <= 100


# --- rivalry_trend ---

class TestRivalryTrend:
    def test_no_matches(self):
        stats = compute_rivalry_stats("🤖", "🎯", [])
        assert rivalry_trend(stats) == "none"

    def test_single_match(self):
        matches = [_make_match(1, "🤖", ["🤖", "🎯"])]
        stats = compute_rivalry_stats("🤖", "🎯", matches)
        assert rivalry_trend(stats) == "none"

    def test_a_trending(self):
        matches = [
            _make_match(1, "🎯", ["🤖", "🎯"]),
            _make_match(2, "🤖", ["🤖", "🎯"]),
            _make_match(3, "🤖", ["🤖", "🎯"]),
        ]
        stats = compute_rivalry_stats("🤖", "🎯", matches)
        assert rivalry_trend(stats) == "a_rising"

    def test_b_trending(self):
        matches = [
            _make_match(1, "🤖", ["🤖", "🎯"]),
            _make_match(2, "🎯", ["🤖", "🎯"]),
            _make_match(3, "🎯", ["🤖", "🎯"]),
        ]
        stats = compute_rivalry_stats("🤖", "🎯", matches)
        assert rivalry_trend(stats) == "b_rising"

    def test_stable(self):
        """Neither wins in recent window — third party wins all."""
        matches = [
            _make_match(1, "🤖", ["🤖", "🎯", "🐢"]),
            _make_match(2, "🐢", ["🤖", "🎯", "🐢"]),
            _make_match(3, "🐢", ["🤖", "🎯", "🐢"]),
            _make_match(4, "🐢", ["🤖", "🎯", "🐢"]),
        ]
        stats = compute_rivalry_stats("🤖", "🎯", matches)
        assert rivalry_trend(stats) == "stable"
