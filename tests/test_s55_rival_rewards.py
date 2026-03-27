"""Tests for T55.2: XP + coin bonuses for rival tier clears."""

from __future__ import annotations

import pytest

from engine.xp import RIVAL_GRADUATION_XP, RIVAL_TIER_CLEAR_XP
from server.coin_rewards import (
    RIVAL_GRADUATION_COINS,
    RIVAL_TIER_CLEAR_COINS,
    award_rival_clear,
)
from server.cosmetic_db import get_coin_balance
from server.db import create_player, init_db


@pytest.fixture()
def conn():
    return init_db(":memory:")


class TestXPConstants:
    def test_tier_clear_xp_exists(self):
        assert RIVAL_TIER_CLEAR_XP > 0

    def test_graduation_xp_greater_than_tier_clear(self):
        assert RIVAL_GRADUATION_XP > RIVAL_TIER_CLEAR_XP


class TestCoinConstants:
    def test_tier_clear_coins_exists(self):
        assert RIVAL_TIER_CLEAR_COINS > 0

    def test_graduation_coins_greater_than_tier_clear(self):
        assert RIVAL_GRADUATION_COINS > RIVAL_TIER_CLEAR_COINS


class TestAwardRivalClear:
    def test_awards_coins_on_tier_clear(self, conn):
        create_player(conn, "p1", "Test")
        award_rival_clear(conn, "p1", graduated=False)
        balance = get_coin_balance(conn, "p1")
        assert balance == RIVAL_TIER_CLEAR_COINS

    def test_awards_extra_on_graduation(self, conn):
        create_player(conn, "p1", "Test")
        award_rival_clear(conn, "p1", graduated=True)
        balance = get_coin_balance(conn, "p1")
        assert balance == RIVAL_TIER_CLEAR_COINS + RIVAL_GRADUATION_COINS

    def test_no_coins_without_call(self, conn):
        create_player(conn, "p1", "Test")
        balance = get_coin_balance(conn, "p1")
        assert balance == 0

    def test_multiple_tier_clears_accumulate(self, conn):
        create_player(conn, "p1", "Test")
        award_rival_clear(conn, "p1", graduated=False)
        award_rival_clear(conn, "p1", graduated=False)
        balance = get_coin_balance(conn, "p1")
        assert balance == RIVAL_TIER_CLEAR_COINS * 2
