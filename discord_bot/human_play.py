"""Discord button input adapter for human play.

Provides a ``DiscordInputAdapter`` that implements ``HumanInputAdapter``
using ``discord.ui.View`` with directional buttons for movement, attack,
defend, and rest actions.
"""

from __future__ import annotations

import asyncio
from typing import Any

import discord
from discord import ui

from engine.human_input import HumanInputAdapter

__all__ = ["DiscordInputAdapter", "HumanPlayView"]


class HumanPlayView(ui.View):
    """Discord UI view with action buttons for human play.

    Layout:
        Row 0: Move N / Move S / Move E / Move W
        Row 1: Atk N / Atk S / Atk E / Atk W
        Row 2: Defend / Rest
    """

    def __init__(self, user_id: int, *, timeout: float = 30.0) -> None:
        super().__init__(timeout=timeout)
        self.user_id = user_id
        self.action: tuple[str, ...] | None = None
        self._add_buttons()

    def _add_buttons(self) -> None:
        """Create and add all action buttons to the view."""
        move_buttons = [
            ("N", "north", discord.ButtonStyle.primary),
            ("S", "south", discord.ButtonStyle.primary),
            ("E", "east", discord.ButtonStyle.primary),
            ("W", "west", discord.ButtonStyle.primary),
        ]
        for label, direction, style in move_buttons:
            btn = ui.Button(label=f"Move {label}", style=style, row=0)
            btn.callback = self._make_callback(("move", direction))
            self.add_item(btn)

        atk_buttons = [
            ("N", "north", discord.ButtonStyle.danger),
            ("S", "south", discord.ButtonStyle.danger),
            ("E", "east", discord.ButtonStyle.danger),
            ("W", "west", discord.ButtonStyle.danger),
        ]
        for label, direction, style in atk_buttons:
            btn = ui.Button(label=f"Atk {label}", style=style, row=1)
            btn.callback = self._make_callback(("attack", direction))
            self.add_item(btn)

        defend_btn = ui.Button(
            label="Defend", style=discord.ButtonStyle.secondary, row=2,
        )
        defend_btn.callback = self._make_callback(("defend",))
        self.add_item(defend_btn)

        rest_btn = ui.Button(
            label="Rest", style=discord.ButtonStyle.success, row=2,
        )
        rest_btn.callback = self._make_callback(("rest",))
        self.add_item(rest_btn)

    def _make_callback(
        self, action: tuple[str, ...],
    ) -> Any:
        """Return an async callback that sets the action and stops the view."""

        async def callback(interaction: discord.Interaction) -> None:
            await self._handle_button(interaction, action)

        return callback

    async def _handle_button(
        self,
        interaction: discord.Interaction,
        action: tuple[str, ...],
    ) -> None:
        """Process a button press: verify user, set action, stop view."""
        if interaction.user.id != self.user_id:  # type: ignore[union-attr]
            await interaction.response.defer()
            return
        self.action = action
        await interaction.response.defer()
        self.stop()


class DiscordInputAdapter(HumanInputAdapter):
    """Human input adapter that collects actions via Discord buttons.

    Args:
        interaction: The Discord interaction to send button views to.
        user_id: The Discord user ID of the human player.
    """

    def __init__(
        self, interaction: discord.Interaction, user_id: int,
    ) -> None:
        self._interaction = interaction
        self.user_id = user_id

    def get_action(
        self, state: dict[str, Any], timeout_s: float,
    ) -> tuple[str, ...] | None:
        """Sync wrapper around get_action_async.

        Uses a background thread when called from within a running event
        loop (e.g. from a Discord command handler).
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop is not None and loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(
                    asyncio.run,
                    self.get_action_async(state, timeout_s),
                ).result()
        return asyncio.run(self.get_action_async(state, timeout_s))

    async def get_action_async(
        self, state: dict[str, Any], timeout_s: float,
    ) -> tuple[str, ...] | None:
        """Send button view and wait for the human player's choice.

        Returns the chosen action tuple, or ``None`` on timeout.
        """
        view = HumanPlayView(user_id=self.user_id, timeout=timeout_s)
        await self._interaction.followup.send(
            "Choose your action:", view=view, ephemeral=True,
        )
        timed_out = await view.wait()
        if timed_out:
            return None
        return view.action
