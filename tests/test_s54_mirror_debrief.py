"""Tests for T54.3: Mirror debrief + graduation ceremony."""

from server.rival_debrief import analyze_rival_match
from server.rival_factory import RIVAL_EMOJI


def _mock_match(rounds=None):
    return {
        "match_id": 1,
        "rounds": rounds or [],
        "eliminations": [],
        "winner": RIVAL_EMOJI,
        "stats": {},
    }


class TestMirrorLesson:
    """Tier 5 should route to mirror-specific analysis."""

    def test_tier_5_routes_to_mirror_analysis(self):
        patterns = {"at_range_1": {"attack": 0.7, "rest": 0.2, "defend": 0.1}}
        result = analyze_rival_match(
            _mock_match(), "🤖", 5, pattern_data=patterns,
        )
        assert result["tier"] == 5
        # Must NOT be the generic default analysis
        assert "tests advanced skills" not in result["lesson"]
        # Should reference player's actual pattern data
        assert "what_happened" in result
        assert "tip" in result

    def test_mirror_without_patterns_generic(self):
        result = analyze_rival_match(_mock_match(), "🤖", 5)
        assert result["tier"] == 5
        assert "lesson" in result

    def test_mirror_shows_accuracy_cap(self):
        patterns = {"at_range_1": {"attack": 0.8}}
        result = analyze_rival_match(
            _mock_match(), "🤖", 5, pattern_data=patterns,
        )
        assert "lesson" in result
        assert "tip" in result

    def test_mirror_includes_patterns_field(self):
        patterns = {"at_range_1": {"attack": 0.7, "rest": 0.3}}
        result = analyze_rival_match(
            _mock_match(), "🤖", 5, pattern_data=patterns,
        )
        assert "patterns" in result


class TestGraduationCeremony:
    """Graduation ceremony on tier 5 completion."""

    def test_ceremony_when_graduated(self):
        result = analyze_rival_match(
            _mock_match(), "🤖", 5, graduated=True,
        )
        assert "ceremony_message" in result
        msg = result["ceremony_message"].lower()
        assert "master" in msg or "complete" in msg

    def test_no_ceremony_when_not_graduated(self):
        result = analyze_rival_match(
            _mock_match(), "🤖", 5, graduated=False,
        )
        assert result.get("ceremony_message") is None

    def test_ceremony_on_tier_5_win(self):
        match = {
            "match_id": 1,
            "rounds": [],
            "eliminations": [],
            "winner": "🤖",
            "stats": {},
        }
        result = analyze_rival_match(match, "🤖", 5, graduated=True)
        assert result["outcome"] == "win"
        assert "ceremony_message" in result

    def test_no_ceremony_on_lower_tiers(self):
        result = analyze_rival_match(
            _mock_match(), "🤖", 3, graduated=False,
        )
        assert result.get("ceremony_message") is None


class TestDebriefHtml:
    """Debrief HTML includes ceremony rendering."""

    def test_debrief_has_ceremony_section(self):
        from pathlib import Path

        html = Path("server/static/debrief.html").read_text()
        assert "ceremony" in html.lower()

    def test_debrief_has_trophy_or_complete(self):
        from pathlib import Path

        html = Path("server/static/debrief.html").read_text()
        assert "TRAINING COMPLETE" in html or "trophy" in html.lower()
