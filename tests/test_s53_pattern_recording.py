"""Tests for post-match pattern recording in debrief endpoint (T53.2)."""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Mock match helpers
# ---------------------------------------------------------------------------

def _mock_match(
    player_emoji="\U0001f916",
    rival_emoji="\U0001f3af",
    rounds=None,
    winner=None,
):
    return {
        "match_id": 1,
        "rounds": rounds or [],
        "eliminations": [],
        "winner": winner or rival_emoji,
        "stats": {},
        "players": [
            {"emoji": player_emoji, "name": "TestBot"},
            {"emoji": rival_emoji, "name": "Rival"},
        ],
    }


# ---------------------------------------------------------------------------
# Cycle 1: analyze_rival_match accepts pattern_data kwarg
# ---------------------------------------------------------------------------

class TestAnalyzeAcceptsPatternData:
    def test_accepts_pattern_data_none(self):
        """analyze_rival_match should accept pattern_data=None without error."""
        from server.rival_debrief import analyze_rival_match

        match = _mock_match()
        result = analyze_rival_match(match, "\U0001f916", 1, pattern_data=None)
        assert "tier" in result
        assert result["tier"] == 1

    def test_accepts_pattern_data_dict(self):
        """analyze_rival_match should accept a pattern_data dict."""
        from server.rival_debrief import analyze_rival_match

        match = _mock_match()
        patterns = {"at_range_1": {"attack": 0.6, "rest": 0.4}}
        result = analyze_rival_match(match, "\U0001f916", 4, pattern_data=patterns)
        assert "tier" in result
        assert result["tier"] == 4


# ---------------------------------------------------------------------------
# Cycle 2: patterns field presence in result
# ---------------------------------------------------------------------------

class TestPatternsInResult:
    def test_patterns_included_when_provided(self):
        """Result should contain patterns field when pattern_data is non-empty."""
        from server.rival_debrief import analyze_rival_match

        match = _mock_match()
        patterns = {"at_range_1": {"attack": 0.6, "rest": 0.4}}
        result = analyze_rival_match(match, "\U0001f916", 4, pattern_data=patterns)
        assert "patterns" in result
        assert result["patterns"] == patterns

    def test_no_patterns_when_none(self):
        """Result should not contain patterns field when pattern_data is None."""
        from server.rival_debrief import analyze_rival_match

        match = _mock_match()
        result = analyze_rival_match(match, "\U0001f916", 1, pattern_data=None)
        assert "patterns" not in result

    def test_no_patterns_when_empty_dict(self):
        """Result should not contain patterns field when pattern_data is empty."""
        from server.rival_debrief import analyze_rival_match

        match = _mock_match()
        result = analyze_rival_match(match, "\U0001f916", 4, pattern_data={})
        assert "patterns" not in result


# ---------------------------------------------------------------------------
# Cycle 3: Debrief endpoint calls record_match_patterns
# ---------------------------------------------------------------------------

class TestDebriefEndpointRecordsPatterns:
    def test_debrief_calls_record_match_patterns(self):
        """Debrief endpoint should call record_match_patterns and pass summary."""
        import json
        import tempfile
        from pathlib import Path
        from unittest.mock import patch

        from fastapi.testclient import TestClient

        from server.app import app
        from server.db import create_api_key, create_player, init_db

        old_db = getattr(app.state, "db", None)
        old_results = getattr(app.state, "results_dir", "results")
        app.state.db = init_db(":memory:")

        create_player(app.state.db, "p1", "Test Player")
        key = create_api_key(app.state.db, "p1")

        match_data = _mock_match()
        with tempfile.TemporaryDirectory() as tmpdir:
            match_path = Path(tmpdir) / "match_001.json"
            match_path.write_text(json.dumps(match_data))
            app.state.results_dir = tmpdir

            mock_table = None

            with patch(
                "server.routes.rival.record_match_patterns"
            ) as mock_record, patch(
                "server.routes.rival.get_pattern_summary"
            ) as mock_summary:
                mock_record.return_value = mock_table
                mock_summary.return_value = {"at_range_1": {"attack": 0.7}}

                client = TestClient(app)
                resp = client.get(
                    "/api/rival/debrief/1", headers={"X-API-Key": key}
                )
                assert resp.status_code == 200
                mock_record.assert_called_once()
                mock_summary.assert_called_once()

        app.state.db = old_db
        app.state.results_dir = old_results

    def test_debrief_returns_patterns_in_response(self):
        """Debrief response should include patterns when summary is non-empty."""
        import json
        import tempfile
        from pathlib import Path
        from unittest.mock import patch

        from fastapi.testclient import TestClient

        from server.app import app
        from server.db import create_api_key, create_player, init_db

        old_db = getattr(app.state, "db", None)
        old_results = getattr(app.state, "results_dir", "results")
        app.state.db = init_db(":memory:")

        create_player(app.state.db, "p1", "Test Player")
        key = create_api_key(app.state.db, "p1")

        match_data = _mock_match()
        with tempfile.TemporaryDirectory() as tmpdir:
            match_path = Path(tmpdir) / "match_001.json"
            match_path.write_text(json.dumps(match_data))
            app.state.results_dir = tmpdir

            pattern_summary = {"at_range_1": {"attack": 0.7, "rest": 0.3}}
            with patch(
                "server.routes.rival.record_match_patterns"
            ) as mock_record, patch(
                "server.routes.rival.get_pattern_summary",
                return_value=pattern_summary,
            ):
                mock_record.return_value = None

                client = TestClient(app)
                resp = client.get(
                    "/api/rival/debrief/1", headers={"X-API-Key": key}
                )
                assert resp.status_code == 200
                data = resp.json()
                assert "patterns" in data
                assert data["patterns"]["at_range_1"]["attack"] == 0.7

        app.state.db = old_db
        app.state.results_dir = old_results
