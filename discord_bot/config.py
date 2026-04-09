"""Configuration loader for NPC Wars Discord bot."""

import os


def load_config() -> dict:
    """Load bot configuration from environment variables.

    Required: BOT_TOKEN, GUILD_ID
    Optional: ANNOUNCEMENT_CHANNEL_ID, RESULTS_CHANNEL_ID (default None)

    Returns:
        dict with bot_token, guild_id, announcement_channel_id, results_channel_id

    Raises:
        ValueError: if a required variable is missing
    """
    bot_token = os.environ.get("BOT_TOKEN")
    if not bot_token:
        raise ValueError("Missing required environment variable: BOT_TOKEN")

    guild_id_raw = os.environ.get("GUILD_ID")
    if not guild_id_raw:
        raise ValueError("Missing required environment variable: GUILD_ID")

    try:
        guild_id = int(guild_id_raw)
    except ValueError:
        raise ValueError(f"GUILD_ID must be a numeric value, got: {guild_id_raw!r}")

    announcement_raw = os.environ.get("ANNOUNCEMENT_CHANNEL_ID")
    results_raw = os.environ.get("RESULTS_CHANNEL_ID")
    submissions_raw = os.environ.get("SUBMISSIONS_CHANNEL_ID")
    ks_tv_raw = os.environ.get("KS_TV_CHANNEL_ID")
    cc_tv_raw = os.environ.get("CC_TV_CHANNEL_ID")

    def _parse_channel(name: str, value: str) -> int:
        try:
            return int(value)
        except ValueError:
            raise ValueError(f"{name} must be a numeric value, got: {value!r}")

    return {
        "bot_token": bot_token,
        "guild_id": guild_id,
        "announcement_channel_id": _parse_channel("ANNOUNCEMENT_CHANNEL_ID", announcement_raw) if announcement_raw else None,
        "results_channel_id": _parse_channel("RESULTS_CHANNEL_ID", results_raw) if results_raw else None,
        "submissions_channel_id": _parse_channel("SUBMISSIONS_CHANNEL_ID", submissions_raw) if submissions_raw else None,
        "ks_tv_channel_id": _parse_channel("KS_TV_CHANNEL_ID", ks_tv_raw) if ks_tv_raw else None,
        "cc_tv_channel_id": _parse_channel("CC_TV_CHANNEL_ID", cc_tv_raw) if cc_tv_raw else None,
    }
