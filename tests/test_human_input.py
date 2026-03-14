"""Tests for engine/human_input.py — human input adapter interface."""

from typing import Any

from engine.human_input import HumanInputAdapter, MockInputAdapter


class TestHumanInputAdapterABC:
    """HumanInputAdapter defines the get_action interface."""

    def test_is_abstract(self) -> None:
        """Cannot instantiate HumanInputAdapter directly."""
        import pytest

        with pytest.raises(TypeError):
            HumanInputAdapter()  # type: ignore[abstract]

    def test_mock_is_subclass(self) -> None:
        assert issubclass(MockInputAdapter, HumanInputAdapter)

    def test_get_action_signature(self) -> None:
        """get_action accepts state dict and timeout_s float."""
        adapter = MockInputAdapter([("move", "east")])
        state: dict[str, Any] = {"round": 1, "bots": []}
        result = adapter.get_action(state, timeout_s=1.0)
        assert result == ("move", "east")


class TestMockInputAdapter:
    """MockInputAdapter returns pre-configured actions in sequence."""

    def test_returns_first_action(self) -> None:
        adapter = MockInputAdapter([("attack", "north")])
        result = adapter.get_action({}, timeout_s=1.0)
        assert result == ("attack", "north")

    def test_returns_actions_in_order(self) -> None:
        actions = [("move", "east"), ("attack", "south"), ("rest",)]
        adapter = MockInputAdapter(actions)
        assert adapter.get_action({}, 1.0) == ("move", "east")
        assert adapter.get_action({}, 1.0) == ("attack", "south")
        assert adapter.get_action({}, 1.0) == ("rest",)

    def test_returns_none_after_exhausted(self) -> None:
        adapter = MockInputAdapter([("move", "west")])
        adapter.get_action({}, 1.0)
        assert adapter.get_action({}, 1.0) is None

    def test_empty_list_returns_none(self) -> None:
        adapter = MockInputAdapter([])
        assert adapter.get_action({}, 1.0) is None

    def test_none_in_sequence_returned_as_none(self) -> None:
        """None in the action list simulates a timeout."""
        adapter = MockInputAdapter([("move", "east"), None, ("rest",)])
        assert adapter.get_action({}, 1.0) == ("move", "east")
        assert adapter.get_action({}, 1.0) is None
        assert adapter.get_action({}, 1.0) == ("rest",)

    def test_state_dict_is_passed_through(self) -> None:
        """get_action receives the state dict (mock ignores it, but signature must accept it)."""
        adapter = MockInputAdapter([("defend",)])
        state = {"round": 5, "my_hp": 20, "bots": []}
        result = adapter.get_action(state, timeout_s=2.0)
        assert result == ("defend",)

    def test_timeout_param_accepted(self) -> None:
        """timeout_s parameter is accepted even though mock ignores it."""
        adapter = MockInputAdapter([("rest",)])
        result = adapter.get_action({}, timeout_s=0.001)
        assert result == ("rest",)
