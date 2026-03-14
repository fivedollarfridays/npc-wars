"""Tests for PatternTable — frequency counter for human behavioral patterns."""

from engine.watcher_memory import CONTEXTS, GLOBAL_PROFILE, PatternTable


class TestPatternTableEmpty:
    """Cycle 1: Empty table behavior."""

    def test_predict_unknown_player_returns_empty_dict(self):
        table = PatternTable()
        result = table.predict("unknown_player", "after_damage")
        assert result == {}

    def test_get_raw_counts_unknown_player_returns_empty_dict(self):
        table = PatternTable()
        result = table.get_raw_counts("unknown_player", "after_damage")
        assert result == {}

    def test_players_empty_table_returns_empty_set(self):
        table = PatternTable()
        assert table.players() == set()


class TestPatternTableRecord:
    """Cycle 2: Recording and accumulation."""

    def test_record_single_action_creates_count(self):
        table = PatternTable()
        table.record("alice", "after_damage", "retreat")
        counts = table.get_raw_counts("alice", "after_damage")
        assert counts == {"retreat": 1}

    def test_record_same_action_twice_increments(self):
        table = PatternTable()
        table.record("alice", "after_damage", "retreat")
        table.record("alice", "after_damage", "retreat")
        counts = table.get_raw_counts("alice", "after_damage")
        assert counts == {"retreat": 2}

    def test_record_different_actions_accumulate(self):
        table = PatternTable()
        table.record("alice", "after_damage", "retreat")
        table.record("alice", "after_damage", "attack")
        table.record("alice", "after_damage", "retreat")
        counts = table.get_raw_counts("alice", "after_damage")
        assert counts == {"retreat": 2, "attack": 1}

    def test_record_adds_player_to_players_set(self):
        table = PatternTable()
        table.record("alice", "after_damage", "retreat")
        assert "alice" in table.players()


class TestPatternTablePredict:
    """Cycle 3: Probability distribution from predict()."""

    def test_predict_single_action_returns_probability_1(self):
        table = PatternTable()
        table.record("alice", "after_damage", "retreat")
        probs = table.predict("alice", "after_damage")
        assert probs == {"retreat": 1.0}

    def test_predict_two_actions_sums_to_one(self):
        table = PatternTable()
        table.record("alice", "after_damage", "retreat")
        table.record("alice", "after_damage", "retreat")
        table.record("alice", "after_damage", "attack")
        probs = table.predict("alice", "after_damage")
        assert probs == {"retreat": 2 / 3, "attack": 1 / 3}
        assert abs(sum(probs.values()) - 1.0) < 1e-9

    def test_predict_different_context_returns_empty(self):
        table = PatternTable()
        table.record("alice", "after_damage", "retreat")
        probs = table.predict("alice", "at_range_1")
        assert probs == {}


class TestPatternTableIsolation:
    """Cycle 4: Player isolation and global profile."""

    def test_different_players_have_isolated_profiles(self):
        table = PatternTable()
        table.record("alice", "after_damage", "retreat")
        table.record("bob", "after_damage", "attack")
        assert table.get_raw_counts("alice", "after_damage") == {"retreat": 1}
        assert table.get_raw_counts("bob", "after_damage") == {"attack": 1}

    def test_global_profile_updated_on_every_record(self):
        table = PatternTable()
        table.record("alice", "after_damage", "retreat")
        table.record("bob", "after_damage", "attack")
        global_counts = table.get_raw_counts(GLOBAL_PROFILE, "after_damage")
        assert global_counts == {"retreat": 1, "attack": 1}

    def test_global_profile_not_in_players(self):
        table = PatternTable()
        table.record("alice", "after_damage", "retreat")
        assert GLOBAL_PROFILE not in table.players()
        assert "alice" in table.players()

    def test_multiple_players_tracked(self):
        table = PatternTable()
        table.record("alice", "after_damage", "retreat")
        table.record("bob", "at_range_1", "attack")
        table.record("charlie", "below_30_hp", "heal")
        assert table.players() == {"alice", "bob", "charlie"}


class TestPatternTableContexts:
    """Cycle 5: Context constants and cross-context behavior."""

    def test_supported_contexts_list(self):
        expected = [
            "after_damage",
            "at_range_1",
            "below_30_hp",
            "storm_closing",
            "override_detected",
        ]
        assert CONTEXTS == expected

    def test_record_works_for_all_supported_contexts(self):
        table = PatternTable()
        for ctx in CONTEXTS:
            table.record("alice", ctx, "attack")
        for ctx in CONTEXTS:
            assert table.get_raw_counts("alice", ctx) == {"attack": 1}

    def test_global_profile_constant(self):
        assert GLOBAL_PROFILE == "__global__"
