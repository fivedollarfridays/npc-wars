"""S43 Integration Gate — Phase 3A completion: full product loop."""

from __future__ import annotations

from pathlib import Path

from agentgrounds.wars.cli import cmd_leaderboard


class TestWebLeaderboard:
    def test_leaderboard_html_exists(self) -> None:
        assert Path("server/static/leaderboard.html").exists()

    def test_profile_html_exists(self) -> None:
        assert Path("server/static/profile.html").exists()


class TestDiscord:
    def test_announce_module(self) -> None:
        from discord_bot.commands.announce import build_match_embed
        embed = build_match_embed({
            "match_id": 1, "winner": "A", "duration_rounds": 10,
            "players": [{"emoji": "A", "name": "Bot A"}],
            "eliminations": [], "stats": {},
        })
        assert embed.title is not None

    def test_challenge_module(self) -> None:
        from discord_bot.commands import challenge
        assert hasattr(challenge, "register_commands")


class TestCLILeaderboard:
    def test_command_registered(self) -> None:
        assert hasattr(cmd_leaderboard, "register")
        assert hasattr(cmd_leaderboard, "run")

    def test_local_mode_works(self) -> None:
        """Local leaderboard doesn't crash."""
        import argparse
        args = argparse.Namespace(local=True, limit=5, sort="wins", server=None)
        # Should not raise
        cmd_leaderboard.run(args)


class TestPhase3AModules:
    """All Phase 3A systems exist and are importable."""

    def test_pypi_package(self) -> None:
        from agentgrounds import __version__
        assert __version__

    def test_viewer_modular(self) -> None:
        assert Path("viewer/index.html").exists()
        assert Path("viewer/js/app.js").exists()

    def test_server_app(self) -> None:
        from server.app import app
        assert app is not None

    def test_server_auth(self) -> None:
        from server.auth import get_current_player
        assert callable(get_current_player)

    def test_server_lobby(self) -> None:
        from server.routes.lobby import router
        assert router is not None

    def test_cli_upload(self) -> None:
        from agentgrounds.wars.cli import cmd_upload
        assert hasattr(cmd_upload, "run")

    def test_cli_leaderboard(self) -> None:
        from agentgrounds.wars.cli import cmd_leaderboard
        assert hasattr(cmd_leaderboard, "run")

    def test_discord_bot(self) -> None:
        from discord_bot.commands.announce import build_match_embed
        assert callable(build_match_embed)
