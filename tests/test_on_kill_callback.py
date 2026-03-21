"""Tests for on_kill callback wiring in callback_runner + game loop."""

from unittest.mock import MagicMock

from engine.callbacks import CallbackSet
from engine.combat import Bot


def _make_bot(emoji: str, *, on_kill: object = None, alive: bool = True) -> Bot:
    """Create a minimal Bot for testing on_kill wiring."""
    bot = Bot(
        name=f"bot_{emoji}", emoji=emoji, bio="test", author="tester",
        decide_func=lambda s: ("rest",), x=0, y=0,
    )
    bot.alive = alive
    if on_kill is not None:
        bot.callbacks = CallbackSet(on_kill=on_kill)
    return bot


# ── Cycle 1: on_kill fires for combat kills ─────────────────────────


class TestOnKillFiresForCombatKills:
    """on_kill callback should fire when a bot gets a combat kill."""

    def test_on_kill_called_for_combat_elimination(self):
        mock_on_kill = MagicMock()
        killer = _make_bot("K", on_kill=mock_on_kill)
        victim = _make_bot("V", alive=False)
        bots = [killer, victim]
        round_elims = [{"emoji": "V", "round": 5, "killed_by": "K", "cause": "combat"}]

        from engine.callback_runner import run_on_kill_callbacks
        run_on_kill_callbacks(bots, round_elims, round_num=5,
                              grid_size=10, storm_border=0)

        mock_on_kill.assert_called_once()
        args = mock_on_kill.call_args[0]
        # First arg is a state dict, second is victim emoji
        assert isinstance(args[0], dict)
        assert args[1] == "V"

    def test_on_kill_receives_valid_state_dict(self):
        mock_on_kill = MagicMock()
        killer = _make_bot("K", on_kill=mock_on_kill)
        victim = _make_bot("V", alive=False)
        bots = [killer, victim]
        round_elims = [{"emoji": "V", "round": 3, "killed_by": "K", "cause": "combat"}]

        from engine.callback_runner import run_on_kill_callbacks
        run_on_kill_callbacks(bots, round_elims, round_num=3,
                              grid_size=12, storm_border=1)

        state = mock_on_kill.call_args[0][0]
        assert "me" in state
        assert "enemies" in state
        assert state["round"] == 3
        assert state["grid_size"] == 12
        assert state["storm_border"] == 1

    def test_multiple_kills_fire_multiple_callbacks(self):
        mock_on_kill = MagicMock()
        killer = _make_bot("K", on_kill=mock_on_kill)
        victim1 = _make_bot("A", alive=False)
        victim2 = _make_bot("B", alive=False)
        bots = [killer, victim1, victim2]
        round_elims = [
            {"emoji": "A", "round": 5, "killed_by": "K", "cause": "combat"},
            {"emoji": "B", "round": 5, "killed_by": "K", "cause": "combat"},
        ]

        from engine.callback_runner import run_on_kill_callbacks
        run_on_kill_callbacks(bots, round_elims, round_num=5,
                              grid_size=10, storm_border=0)

        assert mock_on_kill.call_count == 2
        victims_received = [call[0][1] for call in mock_on_kill.call_args_list]
        assert set(victims_received) == {"A", "B"}


# ── Cycle 2: non-combat kills do NOT fire on_kill ───────────────────


class TestOnKillSkipsNonCombatKills:
    """Storm, plague, and tiebreaker kills should not trigger on_kill."""

    def test_storm_kill_skipped(self):
        mock_on_kill = MagicMock()
        killer = _make_bot("K", on_kill=mock_on_kill)
        victim = _make_bot("V", alive=False)
        bots = [killer, victim]
        round_elims = [{"emoji": "V", "round": 5, "killed_by": "storm", "cause": "storm"}]

        from engine.callback_runner import run_on_kill_callbacks
        run_on_kill_callbacks(bots, round_elims, round_num=5,
                              grid_size=10, storm_border=0)

        mock_on_kill.assert_not_called()

    def test_plague_kill_skipped(self):
        mock_on_kill = MagicMock()
        killer = _make_bot("K", on_kill=mock_on_kill)
        victim = _make_bot("V", alive=False)
        bots = [killer, victim]
        round_elims = [{"emoji": "V", "round": 5, "killed_by": "plague", "cause": "plague"}]

        from engine.callback_runner import run_on_kill_callbacks
        run_on_kill_callbacks(bots, round_elims, round_num=5,
                              grid_size=10, storm_border=0)

        mock_on_kill.assert_not_called()

    def test_tiebreaker_kill_skipped(self):
        mock_on_kill = MagicMock()
        killer = _make_bot("K", on_kill=mock_on_kill)
        victim = _make_bot("V", alive=False)
        bots = [killer, victim]
        round_elims = [{"emoji": "V", "round": 5, "killed_by": "tiebreaker", "cause": "tiebreaker"}]

        from engine.callback_runner import run_on_kill_callbacks
        run_on_kill_callbacks(bots, round_elims, round_num=5,
                              grid_size=10, storm_border=0)

        mock_on_kill.assert_not_called()

    def test_unknown_killer_skipped(self):
        mock_on_kill = MagicMock()
        killer = _make_bot("K", on_kill=mock_on_kill)
        victim = _make_bot("V", alive=False)
        bots = [killer, victim]
        round_elims = [{"emoji": "V", "round": 5, "killed_by": "unknown", "cause": "unknown"}]

        from engine.callback_runner import run_on_kill_callbacks
        run_on_kill_callbacks(bots, round_elims, round_num=5,
                              grid_size=10, storm_border=0)

        mock_on_kill.assert_not_called()

    def test_empty_killer_skipped(self):
        mock_on_kill = MagicMock()
        killer = _make_bot("K", on_kill=mock_on_kill)
        victim = _make_bot("V", alive=False)
        bots = [killer, victim]
        round_elims = [{"emoji": "V", "round": 5, "killed_by": "", "cause": ""}]

        from engine.callback_runner import run_on_kill_callbacks
        run_on_kill_callbacks(bots, round_elims, round_num=5,
                              grid_size=10, storm_border=0)

        mock_on_kill.assert_not_called()


# ── Cycle 3: exception safety + edge cases ──────────────────────────


class TestOnKillExceptionSafety:
    """Exceptions in on_kill must not crash the match."""

    def test_exception_in_on_kill_does_not_raise(self):
        def bad_on_kill(state, victim):
            raise RuntimeError("bot bug")

        killer = _make_bot("K", on_kill=bad_on_kill)
        victim = _make_bot("V", alive=False)
        bots = [killer, victim]
        round_elims = [{"emoji": "V", "round": 5, "killed_by": "K", "cause": "combat"}]

        from engine.callback_runner import run_on_kill_callbacks
        # Must not raise
        run_on_kill_callbacks(bots, round_elims, round_num=5,
                              grid_size=10, storm_border=0)

    def test_no_on_kill_callback_skips_silently(self):
        killer = _make_bot("K")  # No on_kill callback
        victim = _make_bot("V", alive=False)
        bots = [killer, victim]
        round_elims = [{"emoji": "V", "round": 5, "killed_by": "K", "cause": "combat"}]

        from engine.callback_runner import run_on_kill_callbacks
        # Must not raise
        run_on_kill_callbacks(bots, round_elims, round_num=5,
                              grid_size=10, storm_border=0)

    def test_empty_round_elims_is_noop(self):
        mock_on_kill = MagicMock()
        killer = _make_bot("K", on_kill=mock_on_kill)
        bots = [killer]

        from engine.callback_runner import run_on_kill_callbacks
        run_on_kill_callbacks(bots, [], round_num=5,
                              grid_size=10, storm_border=0)

        mock_on_kill.assert_not_called()

    def test_killer_not_in_bots_list_skipped(self):
        """If killed_by references an emoji not in bots, skip gracefully."""
        mock_on_kill = MagicMock()
        bot_a = _make_bot("A", on_kill=mock_on_kill)
        bots = [bot_a]
        round_elims = [{"emoji": "V", "round": 5, "killed_by": "Z", "cause": "combat"}]

        from engine.callback_runner import run_on_kill_callbacks
        run_on_kill_callbacks(bots, round_elims, round_num=5,
                              grid_size=10, storm_border=0)

        mock_on_kill.assert_not_called()
