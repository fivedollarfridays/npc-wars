"""Tests for score/momentum fields in match JSON output."""

from engine.match_writer import build_match_data


def _two_bot_stats() -> dict:
    """Stats dict with score and momentum fields for two bots."""
    return {
        "\U0001f916": {
            "kills": 2, "damage_dealt": 50, "damage_taken": 20,
            "rounds_survived": 10, "score": 35,
            "momentum_tier": 2, "momentum_name": "Rising",
        },
        "\U0001f3af": {
            "kills": 0, "damage_dealt": 10, "damage_taken": 60,
            "rounds_survived": 8, "score": 12,
            "momentum_tier": 0, "momentum_name": "",
        },
    }


def _make_match(stats: dict | None = None, carryover: dict | None = None) -> dict:
    s = stats or _two_bot_stats()
    return build_match_data(
        match_id=1,
        grid_size=10,
        players=[
            {"emoji": "\U0001f916", "name": "Bot", "bio": "", "author": "t"},
            {"emoji": "\U0001f3af", "name": "Rival", "bio": "", "author": "t"},
        ],
        rounds=[{"round": 1, "storm_border": 0, "positions": [], "events": [],
                 "score_events": [{"emoji": "\U0001f916", "source": "survival", "points": 1}]}],
        eliminations=[],
        winner_emoji="\U0001f916",
        stats=s,
        duration_rounds=10,
        carryover=carryover or {},
    )


class TestStatsScoreFields:
    """Match JSON stats include score and momentum per bot."""

    def test_stats_have_score(self):
        data = _make_match()
        for emoji in ("\U0001f916", "\U0001f3af"):
            assert "score" in data["stats"][emoji]

    def test_stats_score_values(self):
        data = _make_match()
        assert data["stats"]["\U0001f916"]["score"] == 35
        assert data["stats"]["\U0001f3af"]["score"] == 12

    def test_stats_have_momentum_tier(self):
        data = _make_match()
        for emoji in ("\U0001f916", "\U0001f3af"):
            assert "momentum_tier" in data["stats"][emoji]

    def test_stats_have_momentum_name(self):
        data = _make_match()
        for emoji in ("\U0001f916", "\U0001f3af"):
            assert "momentum_name" in data["stats"][emoji]


class TestCarryover:
    """Match JSON has carryover dict at root level."""

    def test_carryover_key_exists(self):
        data = _make_match(carryover={"\U0001f916": 17})
        assert "carryover" in data

    def test_carryover_value(self):
        data = _make_match(carryover={"\U0001f916": 17})
        assert data["carryover"] == {"\U0001f916": 17}

    def test_empty_carryover(self):
        data = _make_match(carryover={})
        assert data["carryover"] == {}


class TestRoundScoreEvents:
    """Round data includes score_events list (wired by T25.1)."""

    def test_round_has_score_events(self):
        data = _make_match()
        assert "score_events" in data["rounds"][0]

    def test_score_events_is_list(self):
        data = _make_match()
        assert isinstance(data["rounds"][0]["score_events"], list)

    def test_score_event_structure(self):
        data = _make_match()
        evt = data["rounds"][0]["score_events"][0]
        assert set(evt.keys()) == {"emoji", "source", "points"}
