"""WebSocket server for real-time human input during copilot mode."""

import asyncio
import json
import logging
from typing import Any

import websockets
from websockets.asyncio.server import Server, ServerConnection

from engine.human_input import HumanInputAdapter

__all__ = ["WebSocketInputAdapter"]

log = logging.getLogger(__name__)


class WebSocketInputAdapter(HumanInputAdapter):
    """Accepts human actions from a WebSocket client.

    Implements the HumanInputAdapter interface. Each call to
    ``get_action_async`` sends the current state to the connected client
    and waits for an action response within the timeout window.
    """

    def __init__(self, host: str = "localhost", port: int = 8765) -> None:
        self._host = host
        self._requested_port = port
        self._server: Server | None = None
        self._client: ServerConnection | None = None
        self._port: int = 0
        self._action_event: asyncio.Event = asyncio.Event()
        self._pending_action: tuple[str, ...] | None = None

    @property
    def port(self) -> int:
        """The actual port the server is listening on."""
        return self._port

    async def start(self) -> None:
        """Start the WebSocket server.

        Note: no origin validation — intended for localhost only. If exposed
        beyond localhost, add an ``origins`` parameter to ``websockets.serve``.
        """
        self._server = await websockets.serve(
            self._handle_connection,
            self._host,
            self._requested_port,
        )
        # Resolve actual port (useful when port=0 for OS-assigned)
        for sock in self._server.sockets:
            self._port = sock.getsockname()[1]
            break

    async def stop(self) -> None:
        """Gracefully close the server and any client connection."""
        if self._client is not None:
            try:
                await self._client.close()
            except Exception:
                pass
            self._client = None
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

    async def _handle_connection(self, websocket: ServerConnection) -> None:
        """Handle a single client connection."""
        if self._client is not None:
            await websocket.close(1008, "Only one client allowed")
            return

        self._client = websocket
        log.info("Human player connected from %s", websocket.remote_address)
        try:
            async for message in websocket:
                self._process_message(str(message))
        except websockets.ConnectionClosed:
            log.info("Human player disconnected")
        finally:
            self._client = None
            # Unblock any pending get_action_async call
            self._pending_action = None
            self._action_event.set()

    def _process_message(self, message: str) -> None:
        """Parse a client message and set the pending action."""
        try:
            data = json.loads(message)
        except (json.JSONDecodeError, ValueError):
            log.warning("Invalid JSON from client: %s", message[:100])
            self._pending_action = None
            self._action_event.set()
            return

        if "action" not in data:
            log.warning("Missing 'action' key in message")
            self._pending_action = None
            self._action_event.set()
            return

        raw = data["action"]
        if raw is None:
            self._pending_action = None
        elif isinstance(raw, list):
            self._pending_action = tuple(str(x) for x in raw)
        else:
            self._pending_action = None

        self._action_event.set()

    async def get_action_async(
        self, state: dict[str, Any], timeout_s: float,
    ) -> tuple[str, ...] | None:
        """Send state to client, await action response within timeout.

        Returns the action tuple or None on timeout/disconnect/error.
        """
        if self._client is None:
            return None

        # Clear event before sending to avoid race where response arrives
        # between send() and clear()
        self._action_event.clear()

        # Send state to client
        msg = json.dumps({"type": "state", "state": state})
        try:
            await self._client.send(msg)
        except (websockets.ConnectionClosed, Exception):
            self._client = None
            return None

        # Wait for client response
        try:
            await asyncio.wait_for(self._action_event.wait(), timeout=timeout_s)
        except asyncio.TimeoutError:
            return None

        action = self._pending_action
        self._pending_action = None
        return action

    def get_action(
        self, state: dict[str, Any], timeout_s: float,
    ) -> tuple[str, ...] | None:
        """Sync wrapper for get_action_async.

        Uses asyncio.run() when called outside an event loop,
        otherwise delegates to the running loop.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop is not None and loop.is_running():
            # Can't use asyncio.run inside a running loop;
            # caller should use get_action_async directly.
            return None
        return asyncio.run(self.get_action_async(state, timeout_s))
