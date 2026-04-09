"""Tests for Discord match JSON submission ingestion."""

import json
import time
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest


# ---------------------------------------------------------------------------
# Sample data builders
# ---------------------------------------------------------------------------

def _ks_match() -> dict:
    """Minimal valid Kill Switch match JSON."""
    return {
        "match_id": 42,
        "rounds": [{"round": 1, "positions": []}],
        "stats": {"bot_a": {"kills": 1}},
    }


def _cc_race() -> dict:
    """Minimal valid Code Circuit race JSON."""
    return {
        "frames": [{"tick": 0, "cars": []}],
        "results": [{"car": "A", "position": 1}],
    }


def _make_attachment(content: bytes, filename: str = "match.json") -> MagicMock:
    att = MagicMock(spec=discord.Attachment)
    att.filename = filename
    att.read = AsyncMock(return_value=content)
    return att


def _make_message(
    user_id: int = 1001,
    attachments: list | None = None,
    channel_id: int = 555,
) -> MagicMock:
    msg = MagicMock(spec=discord.Message)
    msg.author = MagicMock()
    msg.author.id = user_id
    msg.author.bot = False
    msg.author.send = AsyncMock()
    msg.channel = MagicMock()
    msg.channel.id = channel_id
    msg.attachments = attachments or []
    msg.add_reaction = AsyncMock()
    return msg


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------

class TestSchemaValidation:
    def test_module_exists(self):
        from discord_bot.commands.submissions import validate_match_json  # noqa: F401

    def test_valid_kill_switch(self):
        from discord_bot.commands.submissions import validate_match_json
        ok, game, err = validate_match_json(_ks_match())
        assert ok is True
        assert game == "kill_switch"
        assert err is None

    def test_valid_code_circuit(self):
        from discord_bot.commands.submissions import validate_match_json
        ok, game, err = validate_match_json(_cc_race())
        assert ok is True
        assert game == "code_circuit"
        assert err is None

    def test_missing_ks_fields(self):
        from discord_bot.commands.submissions import validate_match_json
        data = {"match_id": 1, "rounds": []}  # missing stats
        ok, game, err = validate_match_json(data)
        assert ok is False
        assert err is not None

    def test_missing_cc_fields(self):
        from discord_bot.commands.submissions import validate_match_json
        data = {"frames": []}  # missing results
        ok, game, err = validate_match_json(data)
        assert ok is False
        assert err is not None

    def test_empty_dict(self):
        from discord_bot.commands.submissions import validate_match_json
        ok, game, err = validate_match_json({})
        assert ok is False

    def test_not_a_dict(self):
        from discord_bot.commands.submissions import validate_match_json
        ok, game, err = validate_match_json([1, 2, 3])
        assert ok is False


# ---------------------------------------------------------------------------
# Message handler (on_message hook)
# ---------------------------------------------------------------------------

class TestOnSubmission:
    @pytest.fixture(autouse=True)
    def _clear_rate_limits(self):
        from discord_bot.commands.submissions import _rate_limits
        _rate_limits.clear()

    @pytest.mark.asyncio
    async def test_valid_ks_match_queued(self, tmp_path):
        from discord_bot.commands.submissions import handle_submission
        msg = _make_message(attachments=[
            _make_attachment(json.dumps(_ks_match()).encode()),
        ])
        await handle_submission(msg, queue_dir=str(tmp_path), channel_id=msg.channel.id)
        queued = list(tmp_path.glob("*.json"))
        assert len(queued) == 1
        data = json.loads(queued[0].read_text())
        assert data["match_id"] == 42

    @pytest.mark.asyncio
    async def test_valid_cc_race_queued(self, tmp_path):
        from discord_bot.commands.submissions import handle_submission
        msg = _make_message(attachments=[
            _make_attachment(json.dumps(_cc_race()).encode()),
        ])
        await handle_submission(msg, queue_dir=str(tmp_path), channel_id=msg.channel.id)
        queued = list(tmp_path.glob("*.json"))
        assert len(queued) == 1

    @pytest.mark.asyncio
    async def test_valid_match_gets_checkmark(self, tmp_path):
        from discord_bot.commands.submissions import handle_submission
        msg = _make_message(attachments=[
            _make_attachment(json.dumps(_ks_match()).encode()),
        ])
        await handle_submission(msg, queue_dir=str(tmp_path), channel_id=msg.channel.id)
        msg.add_reaction.assert_any_await("\u2705")

    @pytest.mark.asyncio
    async def test_malformed_json_rejected(self, tmp_path):
        from discord_bot.commands.submissions import handle_submission
        msg = _make_message(attachments=[
            _make_attachment(b"not json at all"),
        ])
        await handle_submission(msg, queue_dir=str(tmp_path), channel_id=msg.channel.id)
        msg.add_reaction.assert_any_await("\u274c")
        msg.author.send.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_missing_fields_rejected(self, tmp_path):
        from discord_bot.commands.submissions import handle_submission
        bad = {"match_id": 1}  # missing rounds and stats
        msg = _make_message(attachments=[
            _make_attachment(json.dumps(bad).encode()),
        ])
        await handle_submission(msg, queue_dir=str(tmp_path), channel_id=msg.channel.id)
        msg.add_reaction.assert_any_await("\u274c")
        msg.author.send.assert_awaited_once()
        assert len(list(tmp_path.glob("*.json"))) == 0

    @pytest.mark.asyncio
    async def test_non_json_file_ignored(self, tmp_path):
        from discord_bot.commands.submissions import handle_submission
        msg = _make_message(attachments=[
            _make_attachment(b"hello", filename="notes.txt"),
        ])
        await handle_submission(msg, queue_dir=str(tmp_path), channel_id=msg.channel.id)
        assert len(list(tmp_path.glob("*.json"))) == 0
        msg.add_reaction.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_wrong_channel_ignored(self, tmp_path):
        from discord_bot.commands.submissions import handle_submission
        msg = _make_message(channel_id=999, attachments=[
            _make_attachment(json.dumps(_ks_match()).encode()),
        ])
        await handle_submission(msg, queue_dir=str(tmp_path), channel_id=555)
        assert len(list(tmp_path.glob("*.json"))) == 0

    @pytest.mark.asyncio
    async def test_bot_messages_ignored(self, tmp_path):
        from discord_bot.commands.submissions import handle_submission
        msg = _make_message(attachments=[
            _make_attachment(json.dumps(_ks_match()).encode()),
        ])
        msg.author.bot = True
        await handle_submission(msg, queue_dir=str(tmp_path), channel_id=msg.channel.id)
        assert len(list(tmp_path.glob("*.json"))) == 0


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------

class TestRateLimit:
    @pytest.mark.asyncio
    async def test_rate_limit_blocks_second_upload(self, tmp_path):
        from discord_bot.commands.submissions import handle_submission, _rate_limits
        _rate_limits.clear()
        msg1 = _make_message(user_id=42, attachments=[
            _make_attachment(json.dumps(_ks_match()).encode()),
        ])
        await handle_submission(msg1, queue_dir=str(tmp_path), channel_id=msg1.channel.id)
        msg2 = _make_message(user_id=42, attachments=[
            _make_attachment(json.dumps(_ks_match()).encode()),
        ])
        await handle_submission(msg2, queue_dir=str(tmp_path), channel_id=msg2.channel.id)
        assert len(list(tmp_path.glob("*.json"))) == 1
        msg2.add_reaction.assert_any_await("\u23f3")

    @pytest.mark.asyncio
    async def test_rate_limit_allows_different_users(self, tmp_path):
        from discord_bot.commands.submissions import handle_submission, _rate_limits
        _rate_limits.clear()
        msg1 = _make_message(user_id=1, attachments=[
            _make_attachment(json.dumps(_ks_match()).encode()),
        ])
        msg2 = _make_message(user_id=2, attachments=[
            _make_attachment(json.dumps(_cc_race()).encode()),
        ])
        await handle_submission(msg1, queue_dir=str(tmp_path), channel_id=msg1.channel.id)
        await handle_submission(msg2, queue_dir=str(tmp_path), channel_id=msg2.channel.id)
        assert len(list(tmp_path.glob("*.json"))) == 2

    @pytest.mark.asyncio
    async def test_rate_limit_expires(self, tmp_path):
        from discord_bot.commands.submissions import handle_submission, _rate_limits, RATE_LIMIT_SECONDS
        _rate_limits.clear()
        msg1 = _make_message(user_id=77, attachments=[
            _make_attachment(json.dumps(_ks_match()).encode()),
        ])
        await handle_submission(msg1, queue_dir=str(tmp_path), channel_id=msg1.channel.id)
        # Simulate expiry by backdating
        _rate_limits[77] = time.monotonic() - RATE_LIMIT_SECONDS - 1
        msg2 = _make_message(user_id=77, attachments=[
            _make_attachment(json.dumps(_cc_race()).encode()),
        ])
        await handle_submission(msg2, queue_dir=str(tmp_path), channel_id=msg2.channel.id)
        assert len(list(tmp_path.glob("*.json"))) == 2
