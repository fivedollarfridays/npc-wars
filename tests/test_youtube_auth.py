"""Tests for youtube/auth.py — OAuth2 flow and token storage."""

import json
import os
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# _load_token
# ---------------------------------------------------------------------------


class TestLoadToken:
    def test_returns_none_when_file_missing(self, tmp_path):
        from youtube.auth import _load_token

        result = _load_token(str(tmp_path / "token.json"))
        assert result is None

    def test_returns_credentials_when_file_exists(self, tmp_path):
        from youtube.auth import _load_token

        token_path = str(tmp_path / "token.json")
        mock_creds = MagicMock()
        with patch("youtube.auth.Credentials.from_authorized_user_file", return_value=mock_creds) as mock_load:
            # Create the file so os.path.exists passes
            with open(token_path, "w") as f:
                f.write("{}")
            result = _load_token(token_path)
        assert result is mock_creds
        mock_load.assert_called_once_with(token_path)


# ---------------------------------------------------------------------------
# _save_token
# ---------------------------------------------------------------------------


class TestSaveToken:
    def test_writes_credentials_json(self, tmp_path):
        from youtube.auth import _save_token

        token_path = str(tmp_path / "token.json")
        mock_creds = MagicMock()
        mock_creds.to_json.return_value = '{"token": "abc"}'

        _save_token(mock_creds, token_path)

        assert os.path.exists(token_path)
        with open(token_path) as f:
            assert json.load(f) == {"token": "abc"}


# ---------------------------------------------------------------------------
# authenticate
# ---------------------------------------------------------------------------


class TestAuthenticate:
    def test_returns_valid_stored_credentials(self, tmp_path):
        """If stored token exists and is valid, returns it without OAuth flow."""
        from youtube.auth import authenticate

        token_path = str(tmp_path / "token.json")
        with open(token_path, "w") as f:
            f.write("{}")

        mock_creds = MagicMock()
        mock_creds.valid = True

        with patch("youtube.auth._load_token", return_value=mock_creds):
            with patch("youtube.auth._run_oauth_flow") as mock_flow:
                result = authenticate("secrets.json", token_path)

        assert result is mock_creds
        mock_flow.assert_not_called()

    def test_runs_oauth_flow_when_no_token(self, tmp_path):
        """If no stored token, runs OAuth2 flow and saves result."""
        from youtube.auth import authenticate

        token_path = str(tmp_path / "token.json")
        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_creds.to_json.return_value = '{"token": "new"}'

        with patch("youtube.auth._load_token", return_value=None):
            with patch("youtube.auth._run_oauth_flow", return_value=mock_creds) as mock_flow:
                with patch("youtube.auth._save_token") as mock_save:
                    result = authenticate("secrets.json", token_path)

        assert result is mock_creds
        mock_flow.assert_called_once()
        mock_save.assert_called_once_with(mock_creds, token_path)

    def test_refreshes_expired_token(self, tmp_path):
        """If stored token is expired but has refresh_token, refreshes it."""
        from youtube.auth import authenticate

        token_path = str(tmp_path / "token.json")
        with open(token_path, "w") as f:
            f.write("{}")

        mock_creds = MagicMock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = "refresh_abc"

        refreshed_creds = MagicMock()
        refreshed_creds.valid = True

        with patch("youtube.auth._load_token", return_value=mock_creds):
            with patch("youtube.auth.refresh_token", return_value=refreshed_creds) as mock_refresh:
                with patch("youtube.auth._run_oauth_flow") as mock_flow:
                    result = authenticate("secrets.json", token_path)

        assert result is refreshed_creds
        mock_refresh.assert_called_once_with(mock_creds, token_path)
        mock_flow.assert_not_called()

    def test_runs_flow_when_token_expired_no_refresh(self, tmp_path):
        """If token is expired with no refresh_token, runs new OAuth flow."""
        from youtube.auth import authenticate

        token_path = str(tmp_path / "token.json")
        with open(token_path, "w") as f:
            f.write("{}")

        mock_creds = MagicMock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = None
        new_creds = MagicMock()
        new_creds.to_json.return_value = '{"token": "new"}'

        with patch("youtube.auth._load_token", return_value=mock_creds):
            with patch("youtube.auth._run_oauth_flow", return_value=new_creds) as mock_flow:
                with patch("youtube.auth._save_token"):
                    result = authenticate("secrets.json", token_path)

        assert result is new_creds
        mock_flow.assert_called_once()


# ---------------------------------------------------------------------------
# refresh_token
# ---------------------------------------------------------------------------


class TestRefreshToken:
    def test_calls_refresh_and_saves(self, tmp_path):
        from youtube.auth import refresh_token

        token_path = str(tmp_path / "token.json")
        mock_creds = MagicMock()
        mock_creds.to_json.return_value = '{"token": "refreshed"}'

        with patch("youtube.auth.Request") as mock_request_cls:
            with patch("youtube.auth._save_token") as mock_save:
                result = refresh_token(mock_creds, token_path)

        mock_creds.refresh.assert_called_once_with(mock_request_cls())
        mock_save.assert_called_once_with(mock_creds, token_path)
        assert result is mock_creds


# ---------------------------------------------------------------------------
# get_youtube_service
# ---------------------------------------------------------------------------


class TestGetYoutubeService:
    def test_builds_youtube_v3_service(self):
        from youtube.auth import get_youtube_service

        mock_creds = MagicMock()
        mock_service = MagicMock()

        with patch("youtube.auth.build", return_value=mock_service) as mock_build:
            result = get_youtube_service(mock_creds)

        mock_build.assert_called_once_with("youtube", "v3", credentials=mock_creds)
        assert result is mock_service


# ---------------------------------------------------------------------------
# _run_oauth_flow
# ---------------------------------------------------------------------------


class TestRunOauthFlow:
    def test_uses_installed_app_flow(self):
        from youtube.auth import _run_oauth_flow, SCOPES

        mock_creds = MagicMock()
        mock_flow = MagicMock()
        mock_flow.run_local_server.return_value = mock_creds

        with patch("youtube.auth.InstalledAppFlow.from_client_secrets_file", return_value=mock_flow) as mock_cls:
            result = _run_oauth_flow("secrets.json", SCOPES)

        mock_cls.assert_called_once_with("secrets.json", SCOPES)
        mock_flow.run_local_server.assert_called_once_with(port=0)
        assert result is mock_creds
