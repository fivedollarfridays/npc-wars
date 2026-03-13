"""Tests for engine/state.py — build_state dict for bot decide()."""

from tests.conftest import make_bot

from engine.state import build_state


class TestBuildState:
    def test_top_level_keys(self):
        bot = make_bot()
        state = build_state(bot, [bot], round_num=1, grid_size=10, storm_border=0)
        assert set(state.keys()) == {"me", "enemies", "round", "grid_size", "storm_border", "bumps_last_round"}

    def test_round_and_grid_values(self):
        bot = make_bot()
        state = build_state(bot, [bot], round_num=15, grid_size=12, storm_border=3)
        assert state["round"] == 15
        assert state["grid_size"] == 12
        assert state["storm_border"] == 3

    def test_me_contains_self_stats(self):
        bot = make_bot(x=3, y=7, hp=80, energy=60)
        state = build_state(bot, [bot], round_num=1, grid_size=10, storm_border=0)
        me = state["me"]
        assert me["x"] == 3
        assert me["y"] == 7
        assert me["hp"] == 80
        assert me["energy"] == 60
        assert "attack_power" in me
        assert "defense" in me

    def test_enemies_excludes_self(self):
        bot_a = make_bot(emoji="🅰️")
        bot_b = make_bot(emoji="🅱️")
        state = build_state(bot_a, [bot_a, bot_b], round_num=1, grid_size=10, storm_border=0)
        assert len(state["enemies"]) == 1
        assert state["enemies"][0]["emoji"] == "🅱️"

    def test_enemies_excludes_dead_bots(self):
        bot_a = make_bot(emoji="🅰️")
        bot_dead = make_bot(emoji="💀", alive=False)
        state = build_state(bot_a, [bot_a, bot_dead], round_num=1, grid_size=10, storm_border=0)
        assert len(state["enemies"]) == 0

    def test_enemy_dict_hides_energy(self):
        bot_a = make_bot(emoji="🅰️")
        bot_b = make_bot(emoji="🅱️", energy=42)
        state = build_state(bot_a, [bot_a, bot_b], round_num=1, grid_size=10, storm_border=0)
        assert "energy" not in state["enemies"][0]

    def test_multiple_enemies(self):
        bots = [make_bot(emoji=e) for e in ["🅰️", "🅱️", "🅾️"]]
        state = build_state(bots[0], bots, round_num=1, grid_size=10, storm_border=0)
        assert len(state["enemies"]) == 2
        enemy_emojis = {e["emoji"] for e in state["enemies"]}
        assert enemy_emojis == {"🅱️", "🅾️"}

    def test_last_bot_alive_no_enemies(self):
        survivor = make_bot(emoji="🏆")
        dead1 = make_bot(emoji="💀", alive=False)
        dead2 = make_bot(emoji="☠️", alive=False)
        state = build_state(survivor, [survivor, dead1, dead2], round_num=50, grid_size=10, storm_border=5)
        assert state["enemies"] == []


class TestBumpsLastRound:
    def test_bumps_last_round_key_exists(self):
        bot = make_bot()
        state = build_state(bot, [bot], round_num=1, grid_size=10, storm_border=0, bumps_last_round=[])
        assert "bumps_last_round" in state

    def test_bumps_last_round_empty_by_default(self):
        bot = make_bot()
        state = build_state(bot, [bot], round_num=1, grid_size=10, storm_border=0)
        assert state["bumps_last_round"] == []

    def test_bumps_last_round_contains_events(self):
        bot = make_bot()
        bump_events = [
            {"type": "bump", "bumper": "🅰️", "bumped": "🅱️", "from": [3, 4], "to": [3, 5]},
            {"type": "wall_splat", "bot": "🅱️", "damage": 10},
        ]
        state = build_state(bot, [bot], round_num=5, grid_size=10, storm_border=1, bumps_last_round=bump_events)
        assert state["bumps_last_round"] == bump_events
        assert len(state["bumps_last_round"]) == 2
