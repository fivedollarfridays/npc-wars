"""Tests for engine/highlights.py — highlight extractor."""

# --- helpers ---


def _match_data(rounds, eliminations=None, winner="🤖", stats=None):
    """Build minimal match data."""
    return {
        "match_id": 1,
        "winner": winner,
        "players": [{"emoji": "🤖"}, {"emoji": "👾"}, {"emoji": "🎯"}],
        "rounds": rounds,
        "eliminations": eliminations or [],
        "stats": stats or {},
        "duration_rounds": len(rounds),
    }


def _round(num, positions, events=None):
    return {"round": num, "storm_border": 5, "positions": positions, "events": events or []}


def _pos(emoji, hp=50, alive=True):
    return {"emoji": emoji, "action": "move north", "hp": hp, "alive": alive, "x": 3, "y": 3}


def _evt(type_, **kw):
    return {"type": type_, **kw}


def _calm_round(num):
    """A round with no events — just bots moving around."""
    return _round(num, [_pos("🤖"), _pos("👾"), _pos("🎯")])


def _kill_round(num, attacker="🤖", victim="👾"):
    """A round with a kill event (drama_score >= 4, tier = heating+)."""
    positions = [_pos("🤖"), _pos("👾", hp=0, alive=False), _pos("🎯")]
    events = [_evt("kill", attacker=attacker, victim=victim)]
    return _round(num, positions, events)


def _hype_round(num):
    """A round that reaches 'hype' tier (drama_score >= 10)."""
    positions = [_pos("🤖", hp=3), _pos("👾", hp=0, alive=False)]
    events = [
        _evt("kill", attacker="🤖", victim="👾"),
        _evt("chain_bump"),
    ]
    return _round(num, positions, events)


# --- test: calm match produces no highlights ---


class TestNoHighlights:
    def test_calm_match_returns_empty(self):
        from engine.highlights import extract_highlights

        rounds = [_calm_round(i) for i in range(1, 6)]
        result = extract_highlights(_match_data(rounds))
        assert result == []

    def test_below_threshold_still_has_kill_guarantee(self):
        """A match with a kill below threshold still gets a highlight (kill guarantee)."""
        from engine.highlights import extract_highlights

        # Single kill = drama below "hype", but kill guarantee kicks in
        rounds = [_calm_round(1), _calm_round(2), _kill_round(3), _calm_round(4)]
        result = extract_highlights(_match_data(rounds), threshold="hype")
        assert len(result) == 1
        assert result[0]["trigger_type"] == "kill"


# --- test: single highlight ---


class TestSingleHighlight:
    def test_hype_round_produces_highlight(self):
        from engine.highlights import extract_highlights

        rounds = [
            _calm_round(1), _calm_round(2), _calm_round(3),
            _hype_round(4),
            _calm_round(5), _calm_round(6),
        ]
        result = extract_highlights(_match_data(rounds), threshold="hype")
        assert len(result) == 1
        h = result[0]
        assert h["round_range"] == (2, 5)  # 2 before trigger (4) → 1 after
        assert "kill" in h["trigger_type"] or "near_death" in h["trigger_type"]
        assert h["drama_score"] >= 10
        assert "participants" in h
        assert "commentary" in h

    def test_highlight_at_start_clamps_range(self):
        """Trigger in round 1 — can't go 2 before, clamp to round 1."""
        from engine.highlights import extract_highlights

        rounds = [_hype_round(1), _calm_round(2), _calm_round(3)]
        result = extract_highlights(_match_data(rounds), threshold="hype")
        assert len(result) == 1
        assert result[0]["round_range"][0] == 1

    def test_highlight_at_end_clamps_range(self):
        """Trigger in last round — can't go 1 after, clamp to last."""
        from engine.highlights import extract_highlights

        rounds = [_calm_round(1), _calm_round(2), _hype_round(3)]
        result = extract_highlights(_match_data(rounds), threshold="hype")
        assert len(result) == 1
        assert result[0]["round_range"][1] == 3

    def test_highlight_fields(self):
        """Each highlight has all required fields."""
        from engine.highlights import extract_highlights

        rounds = [_calm_round(1), _calm_round(2), _calm_round(3), _hype_round(4), _calm_round(5)]
        result = extract_highlights(_match_data(rounds), threshold="hype")
        assert len(result) >= 1
        h = result[0]
        assert "round_range" in h
        assert "trigger_type" in h
        assert "participants" in h
        assert "drama_score" in h
        assert "commentary" in h


# --- test: kill guarantee ---


class TestKillGuarantee:
    def test_match_with_kill_always_has_highlight(self):
        """Any match containing a kill produces at least 1 highlight."""
        from engine.highlights import extract_highlights

        # Kill at drama 4 (heating) — below hype, but kill guarantee kicks in
        rounds = [_calm_round(1), _calm_round(2), _kill_round(3), _calm_round(4)]
        result = extract_highlights(_match_data(rounds))
        assert len(result) >= 1
        assert any("kill" in h["trigger_type"] for h in result)


# --- test: overlapping highlights merge ---


class TestMergeOverlapping:
    def test_adjacent_highlights_merge(self):
        """Two hype rounds close together → single merged highlight."""
        from engine.highlights import extract_highlights

        rounds = [
            _calm_round(1),
            _hype_round(2),
            _calm_round(3),
            _hype_round(4),
            _calm_round(5),
        ]
        # Round 2 → range (1, 3), Round 4 → range (2, 5) — overlap, should merge
        result = extract_highlights(_match_data(rounds), threshold="hype")
        assert len(result) == 1
        h = result[0]
        assert h["round_range"][0] <= 1
        assert h["round_range"][1] >= 5

    def test_distant_highlights_stay_separate(self):
        """Two hype rounds far apart → two separate highlights."""
        from engine.highlights import extract_highlights

        rounds = [
            _calm_round(1),
            _hype_round(2),
            _calm_round(3),
            _calm_round(4),
            _calm_round(5),
            _calm_round(6),
            _calm_round(7),
            _hype_round(8),
            _calm_round(9),
        ]
        # Round 2 → range (1, 3), Round 8 → range (6, 9) — no overlap
        result = extract_highlights(_match_data(rounds), threshold="hype")
        assert len(result) == 2


# --- test: custom threshold ---


class TestThreshold:
    def test_chaos_threshold(self):
        """Only chaos-tier rounds trigger highlights with threshold='chaos'."""
        from engine.highlights import extract_highlights

        rounds = [_calm_round(1), _calm_round(2), _hype_round(3), _calm_round(4)]
        result = extract_highlights(_match_data(rounds), threshold="chaos")
        # hype round is drama ~10, chaos needs 15+ — no highlights (unless kill guarantee)
        # Kill guarantee still applies
        assert all(h["trigger_type"] == "kill" for h in result) or result == []

    def test_heating_threshold_more_highlights(self):
        """Lower threshold → more highlights."""
        from engine.highlights import extract_highlights

        rounds = [_calm_round(1), _kill_round(2), _calm_round(3), _hype_round(4), _calm_round(5)]
        heating = extract_highlights(_match_data(rounds), threshold="heating")
        hype = extract_highlights(_match_data(rounds), threshold="hype")
        assert len(heating) >= len(hype)
