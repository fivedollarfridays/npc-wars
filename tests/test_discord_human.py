"""Tests for discord_bot/human_play.py — Discord button input for human play."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from discord_bot.human_play import DiscordInputAdapter, HumanPlayView
from engine.human_input import HumanInputAdapter


def _fake_interaction(user_id: int) -> MagicMock:
    """Build a mock discord.Interaction with the given user id."""
    interaction = MagicMock()
    interaction.user = MagicMock()
    interaction.user.id = user_id
    interaction.response = AsyncMock()
    return interaction


def _press_button(
    view: HumanPlayView, interaction: MagicMock, action: tuple[str, ...],
) -> None:
    """Simulate a button press by calling _handle_button synchronously."""
    asyncio.run(view._handle_button(interaction, action))


class TestDiscordInputAdapterInterface:
    """DiscordInputAdapter implements HumanInputAdapter ABC."""

    def test_is_subclass_of_human_input_adapter(self) -> None:
        assert issubclass(DiscordInputAdapter, HumanInputAdapter)

    def test_constructor_accepts_interaction_and_user_id(self) -> None:
        interaction = MagicMock()
        adapter = DiscordInputAdapter(interaction=interaction, user_id=12345)
        assert adapter.user_id == 12345


class TestHumanPlayViewButtons:
    """HumanPlayView produces correct action tuples from button presses."""

    def test_move_north_button(self) -> None:
        view = HumanPlayView(user_id=1)
        _press_button(view, _fake_interaction(1), ("move", "north"))
        assert view.action == ("move", "north")

    def test_attack_east_button(self) -> None:
        view = HumanPlayView(user_id=1)
        _press_button(view, _fake_interaction(1), ("attack", "east"))
        assert view.action == ("attack", "east")

    def test_defend_button(self) -> None:
        view = HumanPlayView(user_id=1)
        _press_button(view, _fake_interaction(1), ("defend",))
        assert view.action == ("defend",)

    def test_rest_button(self) -> None:
        view = HumanPlayView(user_id=1)
        _press_button(view, _fake_interaction(1), ("rest",))
        assert view.action == ("rest",)

    def test_wrong_user_ignored(self) -> None:
        """Button press from a different user is ignored."""
        view = HumanPlayView(user_id=1)
        _press_button(view, _fake_interaction(999), ("move", "south"))
        assert view.action is None

    def test_all_move_directions(self) -> None:
        """All four move directions produce correct tuples."""
        for direction in ("north", "south", "east", "west"):
            view = HumanPlayView(user_id=1)
            _press_button(view, _fake_interaction(1), ("move", direction))
            assert view.action == ("move", direction), f"Failed for {direction}"

    def test_all_attack_directions(self) -> None:
        """All four attack directions produce correct tuples."""
        for direction in ("north", "south", "east", "west"):
            view = HumanPlayView(user_id=1)
            _press_button(view, _fake_interaction(1), ("attack", direction))
            assert view.action == ("attack", direction), f"Failed for {direction}"


class TestDiscordInputAdapterAsync:
    """get_action_async sends view and waits for button press."""

    def _make_adapter(self) -> tuple[DiscordInputAdapter, MagicMock]:
        interaction = MagicMock()
        interaction.followup = AsyncMock()
        return DiscordInputAdapter(interaction=interaction, user_id=1), interaction

    @pytest.mark.asyncio
    async def test_returns_action_on_button_press(self) -> None:
        adapter, _ = self._make_adapter()
        with patch("discord_bot.human_play.HumanPlayView") as MockView:
            mock_view = MagicMock()
            mock_view.action = ("move", "north")
            mock_view.wait = AsyncMock(return_value=False)
            MockView.return_value = mock_view
            result = await adapter.get_action_async({"round": 1}, timeout_s=5.0)
        assert result == ("move", "north")

    @pytest.mark.asyncio
    async def test_returns_none_on_timeout(self) -> None:
        adapter, _ = self._make_adapter()
        with patch("discord_bot.human_play.HumanPlayView") as MockView:
            mock_view = MagicMock()
            mock_view.action = None
            mock_view.wait = AsyncMock(return_value=True)
            MockView.return_value = mock_view
            result = await adapter.get_action_async({"round": 1}, timeout_s=0.1)
        assert result is None

    @pytest.mark.asyncio
    async def test_sends_ephemeral_followup(self) -> None:
        adapter, interaction = self._make_adapter()
        with patch("discord_bot.human_play.HumanPlayView") as MockView:
            mock_view = MagicMock()
            mock_view.action = ("rest",)
            mock_view.wait = AsyncMock(return_value=False)
            MockView.return_value = mock_view
            await adapter.get_action_async({"round": 1}, timeout_s=5.0)
        interaction.followup.send.assert_awaited_once()
        assert interaction.followup.send.call_args.kwargs.get("ephemeral") is True

    def test_get_action_sync_delegates_to_async(self) -> None:
        """get_action (sync) wraps get_action_async via asyncio."""
        adapter, _ = self._make_adapter()
        with patch.object(
            adapter, "get_action_async", new_callable=AsyncMock,
        ) as mock_async:
            mock_async.return_value = ("defend",)
            result = adapter.get_action({"round": 1}, timeout_s=5.0)
        assert result == ("defend",)


class TestHumanPlayViewStructure:
    """HumanPlayView has the correct button layout."""

    def test_view_has_buttons(self) -> None:
        view = HumanPlayView(user_id=1)
        assert len(view.children) > 0

    def test_view_default_action_is_none(self) -> None:
        view = HumanPlayView(user_id=1)
        assert view.action is None

    def test_view_has_ten_buttons(self) -> None:
        """4 move + 4 attack + defend + rest = 10 buttons."""
        view = HumanPlayView(user_id=1)
        assert len(view.children) == 10


class TestExports:
    """Module exports."""

    def test_discord_input_adapter_in_all(self) -> None:
        import discord_bot.human_play as mod

        assert "DiscordInputAdapter" in mod.__all__

    def test_human_play_view_in_all(self) -> None:
        import discord_bot.human_play as mod

        assert "HumanPlayView" in mod.__all__
