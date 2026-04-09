"""Tests for TV formatting functions — pure dicts, no discord.py dependency."""

from __future__ import annotations

from discord_bot.formatters import (
    format_tv_main_message,
    format_tv_thread_stats,
    format_tv_thread_watcher,
)


# ---------------------------------------------------------------------------
# Sample data builders
# ---------------------------------------------------------------------------

def _ks_episode() -> dict:
    return {
        "metadata": {"game": "kill_switch", "winner": "A", "participants": ["A", "B", "C"]},
        "post_match": {
            "winner": "A",
            "stat_diffs": [
                {"emoji": "A", "kills": 3, "damage_dealt": 150, "damage_taken": 50},
                {"emoji": "B", "kills": 1, "damage_dealt": 80, "damage_taken": 120},
                {"emoji": "C", "kills": 0, "damage_dealt": 40, "damage_taken": 90},
            ],
            "highlights": [
                {"round": 5, "trigger_type": "kill", "participants": ["A", "B"], "drama_score": 8},
                {"round": 8, "trigger_type": "near_death", "participants": ["A"], "drama_score": 7},
            ],
            "standings": [
                {"participant": "A", "points": 45, "tier": "Diamond"},
                {"participant": "B", "points": 30, "tier": "Gold"},
                {"participant": "C", "points": 15, "tier": "Silver"},
            ],
        },
    }


def _cc_episode() -> dict:
    return {
        "metadata": {"game": "code_circuit", "winner": "FastCar", "participants": ["FastCar", "SlowCar"]},
        "post_match": {
            "winner": "FastCar",
            "stat_diffs": [
                {"emoji": "FastCar", "position": 1, "fastest_lap": True},
                {"emoji": "SlowCar", "position": 2, "fastest_lap": False},
            ],
            "highlights": [
                {"round": 10, "trigger_type": "overtake",
                 "participants": ["FastCar", "SlowCar"], "drama_score": 6},
            ],
            "standings": [
                {"participant": "FastCar", "points": 25, "tier": "Diamond"},
                {"participant": "SlowCar", "points": 18, "tier": "Gold"},
            ],
        },
    }


def _watcher_dossiers() -> dict:
    return {
        "A": {
            "player_id": "A",
            "sync_score": 65.3,
            "predictability_change": 0.72,
            "predictions": [
                {"context": "low_hp", "actions": [{"action": "rest", "probability": 0.6}],
                 "counter": "attack"},
            ],
            "text_summary": "Dossier: A\nSync: 65.3%\nContext: low_hp -> rest (60%)",
        },
    }


# ---------------------------------------------------------------------------
# format_tv_main_message
# ---------------------------------------------------------------------------

class TestFormatTvMainMessage:
    def test_ks_title_contains_kill_switch(self) -> None:
        result = format_tv_main_message(_ks_episode())
        assert "Kill Switch" in result["title"]

    def test_cc_title_contains_code_circuit(self) -> None:
        result = format_tv_main_message(_cc_episode())
        assert "Code Circuit" in result["title"]

    def test_description_contains_winner(self) -> None:
        result = format_tv_main_message(_ks_episode())
        assert "A" in result["description"]

    def test_has_highlights_field(self) -> None:
        result = format_tv_main_message(_ks_episode())
        field_names = [f["name"] for f in result["fields"]]
        assert "Top Highlights" in field_names

    def test_has_participants_field(self) -> None:
        result = format_tv_main_message(_ks_episode())
        field_names = [f["name"] for f in result["fields"]]
        assert "Participants" in field_names

    def test_has_gold_color(self) -> None:
        result = format_tv_main_message(_ks_episode())
        assert result["color"] == 0xF1C40F

    def test_no_highlights_graceful(self) -> None:
        ep = _ks_episode()
        ep["post_match"]["highlights"] = []
        result = format_tv_main_message(ep)
        assert isinstance(result, dict)

    def test_highlights_content(self) -> None:
        result = format_tv_main_message(_ks_episode())
        hl_field = next(f for f in result["fields"] if f["name"] == "Top Highlights")
        assert "kill" in hl_field["value"]


# ---------------------------------------------------------------------------
# format_tv_thread_stats
# ---------------------------------------------------------------------------

class TestFormatTvThreadStats:
    def test_has_stats_field(self) -> None:
        result = format_tv_thread_stats(_ks_episode())
        field_names = [f["name"] for f in result["fields"]]
        assert "Stats" in field_names

    def test_has_standings_field(self) -> None:
        result = format_tv_thread_stats(_ks_episode())
        field_names = [f["name"] for f in result["fields"]]
        assert "Season Standings" in field_names

    def test_standings_contains_tiers(self) -> None:
        result = format_tv_thread_stats(_ks_episode())
        standings_field = next(
            f for f in result["fields"] if f["name"] == "Season Standings"
        )
        assert "Diamond" in standings_field["value"]

    def test_stat_diffs_contain_participants(self) -> None:
        result = format_tv_thread_stats(_ks_episode())
        stats_field = next(f for f in result["fields"] if f["name"] == "Stats")
        for emoji in ("A", "B", "C"):
            assert emoji in stats_field["value"]

    def test_cc_stats(self) -> None:
        result = format_tv_thread_stats(_cc_episode())
        stats_field = next(f for f in result["fields"] if f["name"] == "Stats")
        assert "FastCar" in stats_field["value"]
        assert "SlowCar" in stats_field["value"]

    def test_has_blue_color(self) -> None:
        result = format_tv_thread_stats(_ks_episode())
        assert result["color"] == 0x3498DB

    def test_empty_standings_graceful(self) -> None:
        ep = _ks_episode()
        ep["post_match"]["standings"] = []
        result = format_tv_thread_stats(ep)
        field_names = [f["name"] for f in result["fields"]]
        assert "Season Standings" not in field_names


# ---------------------------------------------------------------------------
# format_tv_thread_watcher
# ---------------------------------------------------------------------------

class TestFormatTvThreadWatcher:
    def test_has_dossier_field(self) -> None:
        result = format_tv_thread_watcher(_watcher_dossiers())
        field_names = [f["name"] for f in result["fields"]]
        assert any("Watcher" in n for n in field_names)

    def test_contains_sync_score(self) -> None:
        result = format_tv_thread_watcher(_watcher_dossiers())
        all_values = " ".join(f["value"] for f in result["fields"])
        assert "65.3" in all_values

    def test_empty_dossiers_returns_none(self) -> None:
        result = format_tv_thread_watcher({})
        assert result is None

    def test_has_purple_color(self) -> None:
        result = format_tv_thread_watcher(_watcher_dossiers())
        assert result["color"] == 0x9B59B6
