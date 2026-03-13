"""CRUD operations for emoji-to-user claims.

State is a plain dict mapping emoji -> user_id.
All mutation functions are pure: they return a new state dict.
File I/O is at the edges via load_claims / save_claims.
"""

import json
import os

MAX_CLAIMS_PER_USER = 3

__all__ = [
    "claim_emoji",
    "unclaim_emoji",
    "get_claims",
    "get_user_claims",
    "is_claimed",
    "load_claims",
    "save_claims",
]


def claim_emoji(state: dict, user_id: str, emoji: str) -> tuple[dict, bool, str]:
    """Claim an emoji for a user. Returns (new_state, ok, reason)."""
    if emoji in state:
        return state, False, f"Emoji {emoji} is already claimed"
    if len(get_user_claims(state, user_id)) >= MAX_CLAIMS_PER_USER:
        return state, False, f"User has reached the limit of {MAX_CLAIMS_PER_USER} claims"
    return {**state, emoji: user_id}, True, ""


def unclaim_emoji(state: dict, user_id: str, emoji: str) -> tuple[dict, bool, str]:
    """Remove a user's claim on an emoji. Returns (new_state, ok, reason)."""
    if emoji not in state:
        return state, False, f"Emoji {emoji} is not claimed"
    if state[emoji] != user_id:
        return state, False, f"Emoji {emoji} is not owned by this user"
    return {k: v for k, v in state.items() if k != emoji}, True, ""


def get_claims(state: dict) -> dict:
    """Return a copy of the full claims dict."""
    return dict(state)


def get_user_claims(state: dict, user_id: str) -> list[str]:
    """Return list of emojis claimed by user_id."""
    return [emoji for emoji, uid in state.items() if uid == user_id]


def is_claimed(state: dict, emoji: str) -> bool:
    """Return True if the emoji is already claimed."""
    return emoji in state


def load_claims(path: str) -> dict:
    """Load claims from a JSON file. Returns empty dict if file missing."""
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


def save_claims(state: dict, path: str) -> None:
    """Persist claims state to a JSON file."""
    with open(path, "w") as f:
        json.dump(state, f, indent=2)
