"""Tests for episode generator (T62.1)."""
from __future__ import annotations

from engine.episode import build_episode


# -- Helpers -----------------------------------------------------------------


def _ks_match(winner="A", rounds=3):
    """Minimal Kill Switch match data."""
    return {
        "game": "kill_switch",
        "winner": winner,
        "players": [
            {"emoji": "A", "name": "BotA"},
            {"emoji": "B", "name": "BotB"},
        ],
        "rounds": [
            {
                "round": i + 1,
                "events": [{"type": "hit", "attacker": "A", "victim": "B"}],
                "positions": [
                    {"emoji": "A", "hp": 30, "alive": True},
                    {"emoji": "B", "hp": 20, "alive": True},
                ],
            }
            for i in range(rounds)
        ],
        "stats": {
            "A": {"kills": 1, "damage_dealt": 30, "score": 100},
            "B": {"kills": 0, "damage_dealt": 10, "score": 40},
        },
    }


def _cc_match(winner="CarX"):
    """Minimal Code Circuit replay-shaped match data."""
    return {
        "game": "code_circuit",
        "winner": winner,
        "players": [
            {"emoji": "CarX", "name": "CarX"},
            {"emoji": "CarY", "name": "CarY"},
        ],
        "results": {
            "CarX": {"position": 1, "points": 25, "fastest_lap": True},
            "CarY": {"position": 2, "points": 18, "fastest_lap": False},
        },
        "stats": {
            "CarX": {"points": 25, "position": 1},
            "CarY": {"points": 18, "position": 2},
        },
    }


def _commentary():
    return [
        {"timestamp": 1, "text": "And we're off!", "tone": "calm", "line_type": "play_by_play"},
        {"timestamp": 2, "text": "Big hit!", "tone": "intense", "line_type": "play_by_play"},
    ]


def _highlights():
    return [
        {
            "round_range": (1, 3),
            "trigger_type": "kill",
            "participants": ["A", "B"],
            "drama_score": 15,
            "commentary": ["A eliminates B"],
        }
    ]


def _profiles():
    return {
        "A": {"traits": ["aggressive"], "archetype_variant": "Berserker", "bio": "Hits hard."},
        "B": {"traits": ["defensive"], "archetype_variant": "Tank", "bio": "Takes hits."},
    }


def _rivalries():
    return [
        {
            "emoji_a": "A", "emoji_b": "B",
            "wins_a": 3, "wins_b": 1, "matches": 4,
            "streak": 2, "streak_holder": "A",
            "rivalry_score": 65,
            "narrative_hooks": ["A dominates the head-to-head"],
        }
    ]


def _standings():
    return [
        {"emoji": "A", "wins": 5, "losses": 1, "points": 150},
        {"emoji": "B", "wins": 3, "losses": 3, "points": 90},
    ]


# -- build_episode returns correct shape -------------------------------------


class TestEpisodeShape:
    """build_episode returns dict with all four sections."""

    def test_returns_dict(self):
        ep = build_episode(_ks_match(), _commentary(), _highlights(), _profiles(), _rivalries(), _standings())
        assert isinstance(ep, dict)

    def test_has_four_sections(self):
        ep = build_episode(_ks_match(), _commentary(), _highlights(), _profiles(), _rivalries(), _standings())
        for key in ("cold_open", "pre_match", "match_commentary", "post_match"):
            assert key in ep, f"Missing section: {key}"

    def test_has_metadata(self):
        ep = build_episode(_ks_match(), _commentary(), _highlights(), _profiles(), _rivalries(), _standings())
        assert "metadata" in ep
        assert "game" in ep["metadata"]


# -- Cold Open ---------------------------------------------------------------


class TestColdOpen:
    """Cold open generates rivalry recap text."""

    def test_previously_on_text(self):
        ep = build_episode(_ks_match(), _commentary(), _highlights(), _profiles(), _rivalries(), _standings())
        assert "Previously on" in ep["cold_open"]["text"]

    def test_includes_rivalry_hooks(self):
        ep = build_episode(_ks_match(), _commentary(), _highlights(), _profiles(), _rivalries(), _standings())
        # Should reference rivalry narrative
        assert ep["cold_open"]["rivalries"]

    def test_no_rivalry_data(self):
        """First episode with no rivalry history."""
        ep = build_episode(_ks_match(), _commentary(), _highlights(), _profiles(), [], _standings())
        assert ep["cold_open"]["text"]  # Still has text
        assert ep["cold_open"]["rivalries"] == []


# -- Pre-Match ---------------------------------------------------------------


class TestPreMatch:
    """Pre-match generates participant intro cards."""

    def test_intro_cards_present(self):
        ep = build_episode(_ks_match(), _commentary(), _highlights(), _profiles(), _rivalries(), _standings())
        assert len(ep["pre_match"]["intros"]) >= 2

    def test_intro_has_profile_fields(self):
        ep = build_episode(_ks_match(), _commentary(), _highlights(), _profiles(), _rivalries(), _standings())
        intro = ep["pre_match"]["intros"][0]
        assert "emoji" in intro
        assert "variant" in intro
        assert "traits" in intro
        assert "bio" in intro

    def test_unknown_profile_gets_default(self):
        """Participants without profiles get a default intro."""
        sparse_profiles = {"A": _profiles()["A"]}  # only A
        ep = build_episode(_ks_match(), _commentary(), _highlights(), sparse_profiles, _rivalries(), _standings())
        assert len(ep["pre_match"]["intros"]) >= 2


# -- Match Commentary --------------------------------------------------------


class TestMatchCommentary:
    """Match section contains indexed commentary track."""

    def test_commentary_track(self):
        ep = build_episode(_ks_match(), _commentary(), _highlights(), _profiles(), _rivalries(), _standings())
        assert ep["match_commentary"]["lines"] == _commentary()

    def test_empty_commentary(self):
        ep = build_episode(_ks_match(), [], _highlights(), _profiles(), _rivalries(), _standings())
        assert ep["match_commentary"]["lines"] == []


# -- Post-Match --------------------------------------------------------------


class TestPostMatch:
    """Post-match includes stat diffs, highlights, standings."""

    def test_stat_diffs(self):
        ep = build_episode(_ks_match(), _commentary(), _highlights(), _profiles(), _rivalries(), _standings())
        assert "stat_diffs" in ep["post_match"]
        assert len(ep["post_match"]["stat_diffs"]) > 0

    def test_highlight_manifest(self):
        ep = build_episode(_ks_match(), _commentary(), _highlights(), _profiles(), _rivalries(), _standings())
        assert ep["post_match"]["highlights"] == _highlights()

    def test_season_standings(self):
        ep = build_episode(_ks_match(), _commentary(), _highlights(), _profiles(), _rivalries(), _standings())
        assert ep["post_match"]["standings"] == _standings()

    def test_winner(self):
        ep = build_episode(_ks_match(), _commentary(), _highlights(), _profiles(), _rivalries(), _standings())
        assert ep["post_match"]["winner"] == "A"


# -- Cross-game compatibility ------------------------------------------------


class TestCrossGame:
    """Works with both Kill Switch and Code Circuit match data."""

    def test_kill_switch_game_tag(self):
        ep = build_episode(_ks_match(), _commentary(), _highlights(), _profiles(), _rivalries(), _standings())
        assert ep["metadata"]["game"] == "kill_switch"

    def test_code_circuit_game_tag(self):
        ep = build_episode(_cc_match(), _commentary(), [], {}, [], _standings())
        assert ep["metadata"]["game"] == "code_circuit"

    def test_cc_stat_diffs(self):
        ep = build_episode(_cc_match(), _commentary(), [], {}, [], _standings())
        assert "stat_diffs" in ep["post_match"]


# -- Scenario coverage: first, mid-season, finale ---------------------------


class TestScenarios:
    """Tests for first episode, mid-season, season finale."""

    def test_first_episode_no_history(self):
        """First episode: no rivalries, no standings, no highlights."""
        ep = build_episode(_ks_match(), _commentary(), [], {}, [], [])
        assert ep["cold_open"]["rivalries"] == []
        assert ep["post_match"]["highlights"] == []
        assert ep["post_match"]["standings"] == []

    def test_mid_season(self):
        """Mid-season: rivalries exist, standings populated."""
        ep = build_episode(
            _ks_match(), _commentary(), _highlights(),
            _profiles(), _rivalries(), _standings(),
        )
        assert len(ep["cold_open"]["rivalries"]) > 0
        assert len(ep["post_match"]["standings"]) > 0

    def test_season_finale(self):
        """Season finale: tight standings, many rivalries."""
        tight_standings = [
            {"emoji": "A", "wins": 10, "losses": 2, "points": 300},
            {"emoji": "B", "wins": 10, "losses": 2, "points": 298},
        ]
        many_rivalries = [
            {**_rivalries()[0], "matches": 12, "rivalry_score": 90},
        ]
        ep = build_episode(
            _ks_match(), _commentary(), _highlights(),
            _profiles(), many_rivalries, tight_standings,
        )
        assert ep["post_match"]["standings"] == tight_standings
        assert len(ep["cold_open"]["rivalries"]) > 0
