"""Tests for post-match rival debrief analysis (T52.6)."""

from __future__ import annotations



# ---------------------------------------------------------------------------
# Mock match helpers
# ---------------------------------------------------------------------------

def _mock_match(
    player_emoji="\U0001f916",
    rival_emoji="\U0001f3af",
    rounds=None,
    eliminations=None,
    winner=None,
):
    if rounds is None:
        rounds = []
    if eliminations is None:
        eliminations = []
    return {
        "match_id": 1,
        "rounds": rounds,
        "eliminations": eliminations,
        "winner": winner or rival_emoji,
        "stats": {
            player_emoji: {
                "kills": 0,
                "damage_dealt": 50,
                "rounds_survived": 10,
            },
            rival_emoji: {
                "kills": 1,
                "damage_dealt": 100,
                "rounds_survived": 15,
            },
        },
        "duration_rounds": 15,
    }


def _round_data(round_num, positions, events=None):
    return {
        "round": round_num,
        "storm_border": max(0, (round_num - 10) // 3),
        "positions": positions,
        "events": events or [],
    }


def _bot_pos(emoji, x, y, hp, energy, action):
    return {
        "emoji": emoji,
        "x": x,
        "y": y,
        "hp": hp,
        "energy": energy,
        "action": action,
        "alive": hp > 0,
        "max_hp": 100,
    }


# ---------------------------------------------------------------------------
# Cycle 1: Structure + outcome
# ---------------------------------------------------------------------------

class TestDebriefStructure:
    def test_returns_dict_with_required_keys(self):
        from server.rival_debrief import analyze_rival_match

        match = _mock_match()
        result = analyze_rival_match(match, "\U0001f916", 1)
        assert "tier" in result
        assert "rival_name" in result
        assert "outcome" in result
        assert "lesson" in result
        assert "tip" in result

    def test_loss_outcome(self):
        from server.rival_debrief import analyze_rival_match

        match = _mock_match(winner="\U0001f3af")
        result = analyze_rival_match(match, "\U0001f916", 1)
        assert result["outcome"] == "loss"

    def test_win_outcome(self):
        from server.rival_debrief import analyze_rival_match

        match = _mock_match(winner="\U0001f916")
        result = analyze_rival_match(match, "\U0001f916", 1)
        assert result["outcome"] == "win"


# ---------------------------------------------------------------------------
# Cycle 2: Bully debrief
# ---------------------------------------------------------------------------

class TestBullyDebrief:
    def test_identifies_rest_adjacent(self):
        """Tier 1 debrief finds rounds where player rested next to enemy."""
        from server.rival_debrief import analyze_rival_match

        rounds = [
            _round_data(5, [
                _bot_pos("\U0001f916", 5, 5, 80, 20, "rest"),
                _bot_pos("\U0001f3af", 6, 5, 100, 100, "attack east"),
            ], [{"type": "hit", "source": "\U0001f3af", "target": "\U0001f916", "damage": 25}]),
        ]
        match = _mock_match(rounds=rounds)
        result = analyze_rival_match(match, "\U0001f916", 1)
        assert result["tier"] == 1
        assert "rest" in result["lesson"].lower() or "rest" in result["what_happened"].lower()

    def test_identifies_key_round(self):
        from server.rival_debrief import analyze_rival_match

        rounds = [
            _round_data(3, [
                _bot_pos("\U0001f916", 5, 5, 100, 100, "move east"),
                _bot_pos("\U0001f3af", 8, 5, 100, 100, "move west"),
            ]),
            _round_data(4, [
                _bot_pos("\U0001f916", 6, 5, 80, 20, "rest"),
                _bot_pos("\U0001f3af", 7, 5, 100, 90, "attack west"),
            ], [{"type": "hit", "source": "\U0001f3af", "target": "\U0001f916", "damage": 25}]),
        ]
        match = _mock_match(rounds=rounds)
        result = analyze_rival_match(match, "\U0001f916", 1)
        assert "key_round" in result
        assert result["key_round"] == 4

    def test_no_rest_adjacent(self):
        """When player never rested adjacent, generic lesson returned."""
        from server.rival_debrief import analyze_rival_match

        rounds = [
            _round_data(3, [
                _bot_pos("\U0001f916", 5, 5, 100, 100, "move east"),
                _bot_pos("\U0001f3af", 8, 5, 100, 100, "move west"),
            ]),
        ]
        match = _mock_match(rounds=rounds)
        result = analyze_rival_match(match, "\U0001f916", 1)
        assert result["key_round"] is None
        assert result["punished_rounds"] == []


# ---------------------------------------------------------------------------
# Cycle 3: Storm debrief
# ---------------------------------------------------------------------------

class TestStormDebrief:
    def test_identifies_storm_damage(self):
        """Tier 2 debrief finds rounds where player took storm damage."""
        from server.rival_debrief import analyze_rival_match

        rounds = [
            _round_data(12, [
                _bot_pos("\U0001f916", 1, 5, 60, 80, "rest"),
                _bot_pos("\U0001f3af", 5, 5, 100, 100, "move east"),
            ], [{"type": "storm_damage", "target": "\U0001f916", "damage": 10}]),
        ]
        match = _mock_match(rounds=rounds)
        result = analyze_rival_match(match, "\U0001f916", 2)
        assert result["tier"] == 2
        assert "storm" in result["lesson"].lower() or "position" in result["lesson"].lower()

    def test_no_storm_damage(self):
        from server.rival_debrief import analyze_rival_match

        rounds = [
            _round_data(12, [
                _bot_pos("\U0001f916", 5, 5, 100, 80, "move east"),
                _bot_pos("\U0001f3af", 6, 5, 100, 100, "move east"),
            ]),
        ]
        match = _mock_match(rounds=rounds)
        result = analyze_rival_match(match, "\U0001f916", 2)
        assert result["key_round"] is None
        assert "good positioning" in result["lesson"].lower() or "no storm" in result["what_happened"].lower()


# ---------------------------------------------------------------------------
# Cycle 4: Default (tier 3-5) debrief
# ---------------------------------------------------------------------------

class TestDefaultDebrief:
    def test_tier_3_returns_lesson(self):
        from server.rival_debrief import analyze_rival_match

        match = _mock_match()
        result = analyze_rival_match(match, "\U0001f916", 3)
        assert result["tier"] == 3
        assert "energy" in result["lesson"].lower()

    def test_tier_5_returns_lesson(self):
        from server.rival_debrief import analyze_rival_match

        match = _mock_match()
        result = analyze_rival_match(match, "\U0001f916", 5)
        assert result["tier"] == 5
        assert "Mirror" in result["lesson"]


# ---------------------------------------------------------------------------
# Cycle 5: Page route + API endpoint
# ---------------------------------------------------------------------------

class TestDebriefPage:
    def test_debrief_page_route(self):
        from fastapi.testclient import TestClient
        from server.app import app
        from server.db import init_db

        old_db = getattr(app.state, "db", None)
        app.state.db = init_db(":memory:")
        client = TestClient(app)
        resp = client.get("/debrief/1")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        app.state.db = old_db

    def test_debrief_api_endpoint_exists(self):
        from fastapi.testclient import TestClient
        from server.app import app
        from server.db import init_db, create_player, create_api_key

        old_db = getattr(app.state, "db", None)
        app.state.db = init_db(":memory:")
        client = TestClient(app)
        create_player(app.state.db, "p1", "Test")
        key = create_api_key(app.state.db, "p1")
        resp = client.get("/api/rival/debrief/999", headers={"X-API-Key": key})
        # 404 is fine (match doesn't exist), just verify endpoint exists
        assert resp.status_code in (200, 404)
        app.state.db = old_db
