"""Tests for discord_bot.formatters — pure formatting, no discord.py dependency."""

from __future__ import annotations

import importlib
import sys


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _players(emojis: list[str]) -> list[dict]:
    return [{"emoji": e, "name": f"bot_{i}"} for i, e in enumerate(emojis)]


def _match_data(
    match_id: int = 1,
    winner: str = "A",
    duration_rounds: int = 10,
    eliminations: list[dict] | None = None,
) -> dict:
    return {
        "match_id": match_id,
        "winner": winner,
        "duration_rounds": duration_rounds,
        "eliminations": eliminations or [],
    }


# ---------------------------------------------------------------------------
# format_match_start
# ---------------------------------------------------------------------------

class TestFormatMatchStart:
    def test_format_match_start_has_title(self) -> None:
        from discord_bot.formatters import format_match_start

        result = format_match_start(42, _players(["A", "B"]), seed=None)
        assert "Match" in result["title"]
        assert "42" in result["title"]

    def test_format_match_start_lists_players(self) -> None:
        from discord_bot.formatters import format_match_start

        result = format_match_start(1, _players(["X", "Y", "Z"]), seed=None)
        players_field = next(f for f in result["fields"] if f["name"] == "Players")
        for emoji in ("X", "Y", "Z"):
            assert emoji in players_field["value"]

    def test_format_match_start_shows_seed(self) -> None:
        from discord_bot.formatters import format_match_start

        result = format_match_start(1, _players(["A"]), seed=9999)
        seed_field = next(f for f in result["fields"] if f["name"] == "Seed")
        assert "9999" in seed_field["value"]

    def test_format_match_start_no_seed_field_when_none(self) -> None:
        from discord_bot.formatters import format_match_start

        result = format_match_start(1, _players(["A"]), seed=None)
        field_names = [f["name"] for f in result["fields"]]
        assert "Seed" not in field_names


# ---------------------------------------------------------------------------
# format_match_end
# ---------------------------------------------------------------------------

class TestFormatMatchEnd:
    def test_format_match_end_has_winner(self) -> None:
        from discord_bot.formatters import format_match_end

        data = _match_data(winner="W")
        result = format_match_end(data)
        assert "W" in result["description"]

    def test_format_match_end_has_duration(self) -> None:
        from discord_bot.formatters import format_match_end

        data = _match_data(duration_rounds=25)
        result = format_match_end(data)
        dur_field = next(f for f in result["fields"] if f["name"] == "Duration")
        assert "25" in dur_field["value"]

    def test_format_match_end_has_eliminations(self) -> None:
        from discord_bot.formatters import format_match_end

        elims = [
            {"round": 5, "killed_by": "A", "emoji": "B", "cause": "attack"},
            {"round": 8, "killed_by": "A", "emoji": "C", "cause": "storm"},
        ]
        data = _match_data(eliminations=elims)
        result = format_match_end(data)
        kills_field = next(f for f in result["fields"] if f["name"] == "Final Kills")
        assert "B" in kills_field["value"]
        assert "storm" in kills_field["value"]


# ---------------------------------------------------------------------------
# format_results
# ---------------------------------------------------------------------------

class TestFormatResults:
    def test_format_results_has_placements(self) -> None:
        from discord_bot.formatters import format_results

        elims = [
            {"round": 3, "emoji": "C"},
            {"round": 7, "emoji": "B"},
        ]
        data = _match_data(winner="A", eliminations=elims)
        result = format_results(data)
        place_field = next(f for f in result["fields"] if f["name"] == "Placements")
        assert "1. A" in place_field["value"]
        assert "2. B" in place_field["value"]
        assert "3. C" in place_field["value"]


# ---------------------------------------------------------------------------
# format_leaderboard
# ---------------------------------------------------------------------------

class TestFormatLeaderboard:
    def test_format_leaderboard_has_rankings(self) -> None:
        from discord_bot.formatters import format_leaderboard

        rankings = [
            {"emoji": "X", "wins": 5, "kills": 10},
            {"emoji": "Y", "wins": 3, "kills": 7},
        ]
        result = format_leaderboard(rankings, page=1)
        for emoji in ("X", "Y"):
            assert emoji in result["description"]

    def test_format_leaderboard_page_footer(self) -> None:
        from discord_bot.formatters import format_leaderboard

        rankings = [{"emoji": f"E{i}", "wins": i, "kills": i} for i in range(25)]
        result = format_leaderboard(rankings, page=2)
        assert result["footer"] == "Page 2/3"


# ---------------------------------------------------------------------------
# format_claim_response / format_unclaim_response
# ---------------------------------------------------------------------------

class TestClaimResponses:
    def test_format_claim_success(self) -> None:
        from discord_bot.formatters import format_claim_response

        result = format_claim_response("Z", ok=True, reason="")
        assert "Claimed" in result["title"] or "claimed" in result["title"].lower()
        assert result["color"] == 0x2ECC71  # green

    def test_format_claim_failure(self) -> None:
        from discord_bot.formatters import format_claim_response

        result = format_claim_response("Z", ok=False, reason="Already taken")
        assert "Failed" in result["title"] or "failed" in result["title"].lower()
        assert "Already taken" in result["description"]
        assert result["color"] == 0xE74C3C  # red

    def test_format_unclaim_success(self) -> None:
        from discord_bot.formatters import format_unclaim_response

        result = format_unclaim_response("Z", ok=True, reason="")
        assert "Released" in result["title"] or "released" in result["title"].lower()

    def test_format_unclaim_failure(self) -> None:
        from discord_bot.formatters import format_unclaim_response

        result = format_unclaim_response("Z", ok=False, reason="Not yours")
        assert "Failed" in result["title"] or "failed" in result["title"].lower()


# ---------------------------------------------------------------------------
# No discord import
# ---------------------------------------------------------------------------

class TestNoDiscordImport:
    def test_no_discord_import(self) -> None:
        """Importing discord_bot.formatters must not pull in discord."""
        # Remove from cache if previously imported
        mod_name = "discord_bot.formatters"
        if mod_name in sys.modules:
            del sys.modules[mod_name]

        # Temporarily block discord
        sentinel = object()
        original = sys.modules.get("discord", sentinel)
        sys.modules["discord"] = None  # type: ignore[assignment]
        try:
            mod = importlib.import_module(mod_name)
            # Module loaded fine without discord
            assert hasattr(mod, "format_match_start")
        finally:
            if original is sentinel:
                sys.modules.pop("discord", None)
            else:
                sys.modules["discord"] = original  # type: ignore[assignment]
