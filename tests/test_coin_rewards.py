"""Tests for match coin reward distribution."""

from __future__ import annotations

from server.coin_rewards import award_match_coins
from server.cosmetic_db import get_coin_balance
from server.cosmetics import MATCH_COIN_REWARD, WIN_COIN_BONUS
from server.db import create_player, init_db

import pytest


@pytest.fixture()
def db(tmp_path):
    """Fresh DB with all tables."""
    return init_db(str(tmp_path / "coins.db"))


def test_all_participants_get_base_reward(db):
    """Every player in the match receives MATCH_COIN_REWARD."""
    create_player(db, "p1", "Alice")
    create_player(db, "p2", "Bob")

    bot_configs = [
        {"player_id": "p1", "emoji": "A", "name": "AliceBot"},
        {"player_id": "p2", "emoji": "B", "name": "BobBot"},
    ]
    match_data = {"winner": "A", "players": [{"emoji": "A"}, {"emoji": "B"}]}

    award_match_coins(db, match_data, bot_configs)

    assert get_coin_balance(db, "p1") == MATCH_COIN_REWARD + WIN_COIN_BONUS
    assert get_coin_balance(db, "p2") == MATCH_COIN_REWARD


def test_winner_gets_bonus(db):
    """The winner receives MATCH_COIN_REWARD + WIN_COIN_BONUS."""
    create_player(db, "p1", "Alice")
    bot_configs = [{"player_id": "p1", "emoji": "A", "name": "AliceBot"}]
    match_data = {"winner": "A"}

    award_match_coins(db, match_data, bot_configs)
    assert get_coin_balance(db, "p1") == MATCH_COIN_REWARD + WIN_COIN_BONUS


def test_no_winner_still_awards_base(db):
    """When winner is 'none', all players still get base reward."""
    create_player(db, "p1", "Alice")
    bot_configs = [{"player_id": "p1", "emoji": "A", "name": "AliceBot"}]
    match_data = {"winner": "none"}

    award_match_coins(db, match_data, bot_configs)
    assert get_coin_balance(db, "p1") == MATCH_COIN_REWARD


def test_fill_bots_without_player_id_skipped(db):
    """Fill bots (no player_id) don't cause errors."""
    create_player(db, "p1", "Alice")
    bot_configs = [
        {"player_id": "p1", "emoji": "A", "name": "AliceBot"},
        {"emoji": "F", "name": "FillBot"},  # No player_id
    ]
    match_data = {"winner": "F"}

    award_match_coins(db, match_data, bot_configs)
    assert get_coin_balance(db, "p1") == MATCH_COIN_REWARD


def test_coins_accumulate_across_matches(db):
    """Coins stack across multiple matches."""
    create_player(db, "p1", "Alice")
    bot_configs = [{"player_id": "p1", "emoji": "A", "name": "AliceBot"}]
    match_data = {"winner": "none"}

    award_match_coins(db, match_data, bot_configs)
    award_match_coins(db, match_data, bot_configs)

    assert get_coin_balance(db, "p1") == MATCH_COIN_REWARD * 2
