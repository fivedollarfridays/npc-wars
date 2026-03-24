"""Tests for tournament bracket engine."""

from __future__ import annotations

import pytest

from server.tournament import VALID_SIZES, Tournament


class TestTournamentConstruction:
    """Cycle 1: construction and validation."""

    def test_valid_sizes(self) -> None:
        assert VALID_SIZES == (8, 16, 32)

    def test_create_8_player(self) -> None:
        t = Tournament("test", 8)
        assert t.name == "test"
        assert t.size == 8
        assert t.status == "open"
        assert t.winner is None

    def test_create_16_player(self) -> None:
        t = Tournament("big", 16)
        assert t.size == 16

    def test_invalid_size_raises(self) -> None:
        with pytest.raises(ValueError, match="Size must be one of"):
            Tournament("bad", 7)


class TestPlayerManagement:
    """Cycle 2: adding players."""

    def test_add_player_succeeds(self) -> None:
        t = Tournament("test", 8)
        assert t.add_player("p1") is True
        assert "p1" in t.players

    def test_add_duplicate_fails(self) -> None:
        t = Tournament("test", 8)
        t.add_player("p1")
        assert t.add_player("p1") is False

    def test_add_to_full_tournament_fails(self) -> None:
        t = Tournament("test", 8)
        for i in range(8):
            t.add_player(f"p{i}")
        assert t.is_full()
        assert t.add_player("p99") is False

    def test_add_to_running_tournament_fails(self) -> None:
        t = Tournament("test", 8)
        t.status = "running"
        assert t.add_player("p1") is False


def _make_tournament(size: int = 8, seed: int = 42) -> Tournament:
    """Helper: create a full tournament ready to seed."""
    t = Tournament("test", size, seed=seed)
    for i in range(size):
        t.add_player(f"p{i}")
    return t


class TestSeeding:
    """Cycle 3: bracket seeding and group generation."""

    def test_seed_creates_groups_of_4(self) -> None:
        t = _make_tournament(8)
        t.seed_bracket()
        assert len(t.rounds) == 1
        assert len(t.rounds[0]) == 2  # 8 / 4 = 2 groups
        for match in t.rounds[0]:
            assert len(match["group"]) == 4

    def test_seed_16_creates_4_groups(self) -> None:
        t = _make_tournament(16)
        t.seed_bracket()
        assert len(t.rounds[0]) == 4

    def test_seed_sets_status_running(self) -> None:
        t = _make_tournament(8)
        t.seed_bracket()
        assert t.status == "running"

    def test_seed_is_deterministic(self) -> None:
        t1 = _make_tournament(8, seed=99)
        t1.seed_bracket()
        t2 = _make_tournament(8, seed=99)
        t2.seed_bracket()
        assert t1.rounds[0] == t2.rounds[0]

    def test_seed_noop_if_not_open(self) -> None:
        t = _make_tournament(8)
        t.status = "running"
        t.seed_bracket()
        assert t.rounds == []

    def test_get_pending_matches(self) -> None:
        t = _make_tournament(8)
        t.seed_bracket()
        pending = t.get_pending_matches()
        assert len(pending) == 2
        assert all(m["results"] is None for m in pending)

    def test_get_current_round(self) -> None:
        t = _make_tournament(8)
        t.seed_bracket()
        assert t.get_current_round() == 0


def _play_match(
    t: Tournament, match_idx: int, match_id: int = 1
) -> None:
    """Helper: record a result for a match, top 2 advance."""
    group = t.rounds[t.get_current_round()][match_idx]["group"]
    placements = list(group)  # 1st, 2nd, 3rd, 4th in group order
    t.record_result(
        match_idx,
        {"winner": placements[0], "placements": placements},
        match_id,
    )


class TestResults:
    """Cycle 4: recording results and advancement."""

    def test_record_result_sets_advancing(self) -> None:
        t = _make_tournament(8)
        t.seed_bracket()
        group = t.rounds[0][0]["group"]
        t.record_result(
            0,
            {"winner": group[0], "placements": group},
            match_id=100,
        )
        match = t.rounds[0][0]
        assert match["results"] is not None
        assert match["match_id"] == 100
        assert match["advancing"] == group[:2]

    def test_pending_decreases_after_result(self) -> None:
        t = _make_tournament(8)
        t.seed_bracket()
        assert len(t.get_pending_matches()) == 2
        _play_match(t, 0)
        assert len(t.get_pending_matches()) == 1

    def test_round_complete_creates_next_round(self) -> None:
        t = _make_tournament(8)
        t.seed_bracket()
        _play_match(t, 0, match_id=1)
        _play_match(t, 1, match_id=2)
        # 8 players -> round 1 done -> final round created
        assert len(t.rounds) == 2
        assert t.get_current_round() == 1

    def test_final_round_has_4_players(self) -> None:
        t = _make_tournament(8)
        t.seed_bracket()
        _play_match(t, 0, match_id=1)
        _play_match(t, 1, match_id=2)
        final_group = t.rounds[1][0]["group"]
        assert len(final_group) == 4


class TestFullTournament:
    """Cycle 5: end-to-end flows and serialization."""

    def test_8_player_tournament_completes_in_2_rounds(self) -> None:
        t = _make_tournament(8)
        t.seed_bracket()
        # Round 1: 2 matches
        _play_match(t, 0, match_id=1)
        _play_match(t, 1, match_id=2)
        assert len(t.rounds) == 2
        # Final
        _play_match(t, 0, match_id=3)
        assert t.is_complete()
        assert t.get_winner() is not None
        assert len(t.rounds) == 2

    def test_16_player_tournament_completes_in_3_rounds(self) -> None:
        t = _make_tournament(16)
        t.seed_bracket()
        # Round 1: 4 matches
        for i in range(4):
            _play_match(t, i, match_id=i + 1)
        assert len(t.rounds) == 2
        # Round 2: 2 matches
        for i in range(2):
            _play_match(t, i, match_id=i + 10)
        assert len(t.rounds) == 3
        # Final: 1 match
        _play_match(t, 0, match_id=99)
        assert t.is_complete()
        assert t.get_winner() is not None
        assert len(t.rounds) == 3

    def test_to_dict_roundtrip(self) -> None:
        t = _make_tournament(8)
        t.seed_bracket()
        _play_match(t, 0, match_id=1)
        data = t.to_dict()
        t2 = Tournament.from_dict(data)
        assert t2.name == t.name
        assert t2.size == t.size
        assert t2.seed == t.seed
        assert t2.players == t.players
        assert t2.rounds == t.rounds
        assert t2.status == t.status
        assert t2.winner == t.winner

    def test_to_dict_contains_all_fields(self) -> None:
        t = _make_tournament(8)
        data = t.to_dict()
        expected_keys = {"name", "size", "seed", "players", "rounds", "status", "winner"}
        assert set(data.keys()) == expected_keys

    def test_winner_comes_from_final_placements(self) -> None:
        t = _make_tournament(8)
        t.seed_bracket()
        _play_match(t, 0, match_id=1)
        _play_match(t, 1, match_id=2)
        # Get the final group and pick a specific winner
        final_group = t.rounds[1][0]["group"]
        chosen_winner = final_group[2]  # 3rd player wins the final
        custom_placements = [chosen_winner] + [
            p for p in final_group if p != chosen_winner
        ]
        t.record_result(
            0,
            {"winner": chosen_winner, "placements": custom_placements},
            match_id=99,
        )
        assert t.is_complete()
        assert t.get_winner() == chosen_winner
