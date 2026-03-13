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

    guild_id = int(guild_id_raw)

    announcement_raw = os.environ.get("ANNOUNCEMENT_CHANNEL_ID")
    results_raw = os.environ.get("RESULTS_CHANNEL_ID")

    return {
        "bot_token": bot_token,
        "guild_id": guild_id,
        "announcement_channel_id": int(announcement_raw) if announcement_raw else None,
        "results_channel_id": int(results_raw) if results_raw else None,
    }
