"""YouTube API authentication — OAuth2 flow and token persistence."""

import logging
import os
import subprocess
from typing import Any

log = logging.getLogger(__name__)

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def authenticate(
    client_secrets_path: str,
    token_path: str,
    scopes: list[str] = SCOPES,
) -> Credentials:
    """Return valid YouTube API credentials.

    Loads stored token if present and valid. Refreshes if expired with a
    refresh token. Runs the browser OAuth2 flow on first use and persists
    the resulting token.

    Args:
        client_secrets_path: Path to client_secrets.json from Google Cloud Console.
        token_path: Path where the token will be stored/loaded (e.g. token.json).
        scopes: OAuth2 scopes to request.

    Returns:
        Valid google.oauth2.credentials.Credentials object.
    """
    _warn_if_tracked(client_secrets_path)
    _warn_if_tracked(token_path)

    creds = _load_token(token_path)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        return refresh_token(creds, token_path)

    # No usable token — run full OAuth2 flow
    creds = _run_oauth_flow(client_secrets_path, scopes)
    _save_token(creds, token_path)
    return creds


def get_youtube_service(credentials: Credentials) -> Any:
    """Build and return the YouTube Data API v3 service resource.

    Args:
        credentials: Valid OAuth2 credentials.

    Returns:
        googleapiclient Resource object for the YouTube v3 API.
    """
    return build("youtube", "v3", credentials=credentials)


def refresh_token(credentials: Credentials, token_path: str) -> Credentials:
    """Refresh expired credentials and persist the updated token.

    Args:
        credentials: Expired credentials with a valid refresh_token.
        token_path: Path where the refreshed token will be saved.

    Returns:
        The same credentials object, now refreshed.
    """
    credentials.refresh(Request())
    _save_token(credentials, token_path)
    return credentials


def _warn_if_tracked(path: str) -> None:
    """Warn if a file is tracked by git (secrets should not be committed)."""
    try:
        result = subprocess.run(
            ["git", "ls-files", path],
            capture_output=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            log.warning(
                "Security warning: %s is tracked by git. "
                "Credential files should be in .gitignore.",
                path,
            )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass  # git not available or too slow — skip check


def _load_token(token_path: str) -> Credentials | None:
    """Load credentials from a JSON token file.

    Returns None if the file does not exist.
    """
    if os.path.exists(token_path):
        return Credentials.from_authorized_user_file(token_path)
    return None


def _save_token(credentials: Credentials, token_path: str) -> None:
    """Persist credentials to a JSON token file with restricted permissions."""
    with open(token_path, "w") as f:
        f.write(credentials.to_json())
    os.chmod(token_path, 0o600)


def _run_oauth_flow(client_secrets_path: str, scopes: list[str]) -> Credentials:
    """Run the InstalledApp OAuth2 flow (opens a local browser window).

    Args:
        client_secrets_path: Path to client_secrets.json.
        scopes: OAuth2 scopes to request.

    Returns:
        Fresh credentials from the completed flow.
    """
    flow = InstalledAppFlow.from_client_secrets_file(client_secrets_path, scopes)
    return flow.run_local_server(port=0)
