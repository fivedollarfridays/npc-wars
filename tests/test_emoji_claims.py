"""Tests for data/emoji_claims.py — CRUD, uniqueness, per-user limits, persistence."""

import json


from data.emoji_claims import (
    claim_emoji,
    get_claims,
    get_user_claims,
    is_claimed,
    load_claims,
    save_claims,
    unclaim_emoji,
)


# --- claim_emoji ---


class TestClaimEmoji:
    def test_claim_returns_success(self):
        state = {}
        result, ok, _ = claim_emoji(state, "alice", "🎯")
        assert ok is True

    def test_claim_adds_to_state(self):
        state = {}
        result, ok, _ = claim_emoji(state, "alice", "🎯")
        assert result["🎯"] == "alice"

    def test_claim_does_not_mutate_original(self):
        state = {}
        claim_emoji(state, "alice", "🎯")
        assert state == {}

    def test_duplicate_emoji_fails(self):
        state = {"🎯": "alice"}
        _, ok, reason = claim_emoji(state, "bob", "🎯")
        assert ok is False
        assert "claimed" in reason.lower()

    def test_same_user_reclaims_same_emoji_fails(self):
        state = {"🎯": "alice"}
        _, ok, _ = claim_emoji(state, "alice", "🎯")
        assert ok is False

    def test_user_limit_three_emojis(self):
        state = {"🅰️": "alice", "🅱️": "alice", "🅾️": "alice"}
        _, ok, reason = claim_emoji(state, "alice", "🆕")
        assert ok is False
        assert "limit" in reason.lower()

    def test_user_can_claim_up_to_three(self):
        state = {}
        state, _, _ = claim_emoji(state, "alice", "🅰️")
        state, _, _ = claim_emoji(state, "alice", "🅱️")
        state, ok, _ = claim_emoji(state, "alice", "🅾️")
        assert ok is True
        assert len(get_user_claims(state, "alice")) == 3

    def test_different_users_can_claim_different_emojis(self):
        state = {}
        state, _, _ = claim_emoji(state, "alice", "🎯")
        state, ok, _ = claim_emoji(state, "bob", "🚀")
        assert ok is True
        assert state["🚀"] == "bob"


# --- unclaim_emoji ---


class TestUnclaimEmoji:
    def test_unclaim_removes_entry(self):
        state = {"🎯": "alice"}
        result, ok, _ = unclaim_emoji(state, "alice", "🎯")
        assert ok is True
        assert "🎯" not in result

    def test_unclaim_does_not_mutate_original(self):
        state = {"🎯": "alice"}
        unclaim_emoji(state, "alice", "🎯")
        assert "🎯" in state

    def test_unclaim_wrong_user_fails(self):
        state = {"🎯": "alice"}
        _, ok, reason = unclaim_emoji(state, "bob", "🎯")
        assert ok is False
        assert "not" in reason.lower() or "owner" in reason.lower()

    def test_unclaim_nonexistent_emoji_fails(self):
        state = {}
        _, ok, _ = unclaim_emoji(state, "alice", "🎯")
        assert ok is False

    def test_claim_unclaim_roundtrip(self):
        state = {}
        state, _, _ = claim_emoji(state, "alice", "🎯")
        state, ok, _ = unclaim_emoji(state, "alice", "🎯")
        assert ok is True
        assert is_claimed(state, "🎯") is False


# --- get_claims / get_user_claims / is_claimed ---


class TestQueryFunctions:
    def test_get_claims_returns_copy(self):
        state = {"🎯": "alice"}
        claims = get_claims(state)
        claims["🚀"] = "bob"
        assert "🚀" not in state

    def test_get_user_claims_empty(self):
        assert get_user_claims({}, "alice") == []

    def test_get_user_claims_filters_by_user(self):
        state = {"🎯": "alice", "🚀": "bob", "🏆": "alice"}
        result = get_user_claims(state, "alice")
        assert set(result) == {"🎯", "🏆"}

    def test_is_claimed_true(self):
        assert is_claimed({"🎯": "alice"}, "🎯") is True

    def test_is_claimed_false(self):
        assert is_claimed({}, "🎯") is False


# --- File persistence ---


class TestPersistence:
    def test_save_and_load_roundtrip(self, tmp_path):
        state = {"🎯": "alice", "🚀": "bob"}
        path = str(tmp_path / "claims.json")
        save_claims(state, path)
        loaded = load_claims(path)
        assert loaded == state

    def test_load_missing_file_returns_empty(self, tmp_path):
        path = str(tmp_path / "nonexistent.json")
        assert load_claims(path) == {}

    def test_save_creates_valid_json(self, tmp_path):
        state = {"🎯": "alice"}
        path = str(tmp_path / "claims.json")
        save_claims(state, path)
        with open(path) as f:
            data = json.load(f)
        assert data == state
