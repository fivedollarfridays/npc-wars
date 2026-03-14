"""Tests for realtime/server.py — WebSocket input adapter."""

import asyncio
import json

import pytest
import pytest_asyncio
import websockets

from realtime.server import WebSocketInputAdapter


@pytest_asyncio.fixture
async def adapter():
    """Start a WebSocketInputAdapter, yield it, then stop."""
    ws_adapter = WebSocketInputAdapter(host="localhost", port=0)
    await ws_adapter.start()
    yield ws_adapter
    await ws_adapter.stop()


def _get_port(adapter: WebSocketInputAdapter) -> int:
    """Get the actual port the server bound to."""
    return adapter.port


class TestWebSocketServerStartup:
    """Server starts and accepts connections."""

    @pytest.mark.asyncio
    async def test_server_starts(self, adapter: WebSocketInputAdapter) -> None:
        assert adapter.port > 0

    @pytest.mark.asyncio
    async def test_accepts_connection(self, adapter: WebSocketInputAdapter) -> None:
        port = _get_port(adapter)
        async with websockets.connect(f"ws://localhost:{port}") as ws:
            assert ws.protocol.state.name == "OPEN"


class TestActionReceive:
    """Server receives action JSON from client."""

    @pytest.mark.asyncio
    async def test_receives_move_action(self, adapter: WebSocketInputAdapter) -> None:
        port = _get_port(adapter)
        async with websockets.connect(f"ws://localhost:{port}") as ws:
            # get_action sends state and waits for response
            state = {"round": 1, "bots": []}

            async def client_respond():
                msg = await ws.recv()
                data = json.loads(msg)
                assert data["type"] == "state"
                await ws.send(json.dumps({"action": ["move", "east"]}))

            result, _ = await asyncio.gather(
                adapter.get_action_async(state, timeout_s=2.0),
                client_respond(),
            )
            assert result == ("move", "east")

    @pytest.mark.asyncio
    async def test_receives_attack_action(self, adapter: WebSocketInputAdapter) -> None:
        port = _get_port(adapter)
        async with websockets.connect(f"ws://localhost:{port}") as ws:
            async def client_respond():
                await ws.recv()
                await ws.send(json.dumps({"action": ["attack", "north"]}))

            result, _ = await asyncio.gather(
                adapter.get_action_async({"round": 1}, timeout_s=2.0),
                client_respond(),
            )
            assert result == ("attack", "north")

    @pytest.mark.asyncio
    async def test_null_action_returns_none(self, adapter: WebSocketInputAdapter) -> None:
        port = _get_port(adapter)
        async with websockets.connect(f"ws://localhost:{port}") as ws:
            async def client_respond():
                await ws.recv()
                await ws.send(json.dumps({"action": None}))

            result, _ = await asyncio.gather(
                adapter.get_action_async({"round": 1}, timeout_s=2.0),
                client_respond(),
            )
            assert result is None


class TestStateUpdate:
    """Server sends state dict to client each round."""

    @pytest.mark.asyncio
    async def test_sends_state_with_round(self, adapter: WebSocketInputAdapter) -> None:
        port = _get_port(adapter)
        async with websockets.connect(f"ws://localhost:{port}") as ws:
            state = {"round": 5, "my_hp": 42, "bots": []}

            async def client_respond():
                msg = await ws.recv()
                data = json.loads(msg)
                assert data["type"] == "state"
                assert data["state"]["round"] == 5
                assert data["state"]["my_hp"] == 42
                await ws.send(json.dumps({"action": ["rest"]}))

            await asyncio.gather(
                adapter.get_action_async(state, timeout_s=2.0),
                client_respond(),
            )


class TestTimeout:
    """Returns None when client doesn't respond in time."""

    @pytest.mark.asyncio
    async def test_timeout_returns_none(self, adapter: WebSocketInputAdapter) -> None:
        port = _get_port(adapter)
        async with websockets.connect(f"ws://localhost:{port}"):
            result = await adapter.get_action_async({"round": 1}, timeout_s=0.1)
            assert result is None


class TestDisconnect:
    """Handles client disconnect gracefully."""

    @pytest.mark.asyncio
    async def test_disconnect_returns_none(self, adapter: WebSocketInputAdapter) -> None:
        port = _get_port(adapter)
        ws = await websockets.connect(f"ws://localhost:{port}")
        await ws.close()
        await asyncio.sleep(0.05)
        result = await adapter.get_action_async({"round": 1}, timeout_s=0.2)
        assert result is None

    @pytest.mark.asyncio
    async def test_no_client_returns_none(self, adapter: WebSocketInputAdapter) -> None:
        """No client connected — get_action returns None."""
        result = await adapter.get_action_async({"round": 1}, timeout_s=0.1)
        assert result is None


class TestInvalidInput:
    """Handles invalid JSON from client."""

    @pytest.mark.asyncio
    async def test_invalid_json_returns_none(self, adapter: WebSocketInputAdapter) -> None:
        port = _get_port(adapter)
        async with websockets.connect(f"ws://localhost:{port}") as ws:
            async def client_respond():
                await ws.recv()
                await ws.send("not valid json!!!")

            result, _ = await asyncio.gather(
                adapter.get_action_async({"round": 1}, timeout_s=0.5),
                client_respond(),
            )
            assert result is None

    @pytest.mark.asyncio
    async def test_missing_action_key_returns_none(self, adapter: WebSocketInputAdapter) -> None:
        port = _get_port(adapter)
        async with websockets.connect(f"ws://localhost:{port}") as ws:
            async def client_respond():
                await ws.recv()
                await ws.send(json.dumps({"wrong_key": "data"}))

            result, _ = await asyncio.gather(
                adapter.get_action_async({"round": 1}, timeout_s=0.5),
                client_respond(),
            )
            assert result is None


class TestSyncInterface:
    """get_action (sync) wraps the async version for HumanInputAdapter compatibility."""

    @pytest.mark.asyncio
    async def test_is_human_input_adapter(self) -> None:
        from engine.human_input import HumanInputAdapter

        assert issubclass(WebSocketInputAdapter, HumanInputAdapter)
