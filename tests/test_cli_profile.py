"""Tests for CLI profile command and profile display formatting."""
from __future__ import annotations


# ── Cycle 1: Progress bar rendering ────────────────────────────────

def test_progress_bar_zero_percent() -> None:
    from engine.profile_display import render_progress_bar

    bar = render_progress_bar(0, 1000, width=20)
    assert bar == "░" * 20


def test_progress_bar_fifty_percent() -> None:
    from engine.profile_display import render_progress_bar

    bar = render_progress_bar(500, 1000, width=20)
    assert bar == "█" * 10 + "░" * 10


def test_progress_bar_hundred_percent() -> None:
    from engine.profile_display import render_progress_bar

    bar = render_progress_bar(1000, 1000, width=20)
    assert bar == "█" * 20


def test_progress_bar_over_max() -> None:
    """Current > total should clamp to full."""
    from engine.profile_display import render_progress_bar

    bar = render_progress_bar(1500, 1000, width=20)
    assert bar == "█" * 20


def test_progress_bar_zero_total() -> None:
    """Zero total (max level) should show full bar."""
    from engine.profile_display import render_progress_bar

    bar = render_progress_bar(0, 0, width=20)
    assert bar == "█" * 20


# ── Cycle 2: Single profile formatting ─────────────────────────────

def _make_profile(
    name: str = "GooseLoose",
    total_xp: int = 600,
    level: int = 5,
    matches: int = 47,
    wins: int = 12,
    kills: int = 89,
) -> dict:
    return {
        "name": name,
        "total_xp": total_xp,
        "level": level,
        "matches": matches,
        "wins": wins,
        "kills": kills,
    }


def test_format_profile_contains_name_and_level() -> None:
    from engine.profile_display import format_profile

    out = format_profile(_make_profile())
    assert "GooseLoose" in out
    assert "Level 5" in out


def test_format_profile_contains_stats() -> None:
    from engine.profile_display import format_profile

    out = format_profile(_make_profile())
    assert "Matches: 47" in out
    assert "Wins: 12" in out
    assert "W/R: 25.5%" in out
    assert "Kills: 89" in out


def test_format_profile_contains_progress_bar() -> None:
    from engine.profile_display import format_profile

    # 700 XP at level 5 (needs 600-800 range, so 100/200 = 50%)
    out = format_profile(_make_profile(total_xp=700, level=5))
    assert "700" in out
    assert "█" in out
    assert "░" in out


def test_format_profile_contains_unlocks() -> None:
    from engine.profile_display import format_profile

    out = format_profile(_make_profile(level=5))
    assert "move" in out
    assert "attack" in out
    assert "dash" in out


def test_format_profile_shows_next_unlock() -> None:
    from engine.profile_display import format_profile

    out = format_profile(_make_profile(level=5))
    # Next unlock after level 5 is taunt at level 8
    assert "taunt" in out
    assert "Level 8" in out


def test_format_profile_zero_matches_no_divide_by_zero() -> None:
    from engine.profile_display import format_profile

    out = format_profile(_make_profile(matches=0, wins=0, kills=0))
    assert "W/R: 0.0%" in out
    assert "K/M: 0.0" in out


# ── Cycle 3: Leaderboard formatting ────────────────────────────────

def test_format_leaderboard_header() -> None:
    from engine.profile_display import format_leaderboard

    profiles = [_make_profile()]
    out = format_leaderboard(profiles)
    assert "Name" in out
    assert "Level" in out
    assert "XP" in out


def test_format_leaderboard_rows() -> None:
    from engine.profile_display import format_leaderboard

    profiles = [
        _make_profile(name="GooseLoose", level=5, total_xp=780, matches=47, wins=12),
        _make_profile(name="AggroBoy", level=3, total_xp=320, matches=22, wins=5),
    ]
    out = format_leaderboard(profiles)
    lines = out.strip().split("\n")
    # Header + separator + 2 data rows = 4 lines minimum
    assert len(lines) >= 4
    assert "GooseLoose" in out
    assert "AggroBoy" in out


def test_format_leaderboard_ranking_numbers() -> None:
    from engine.profile_display import format_leaderboard

    profiles = [_make_profile(name="First"), _make_profile(name="Second")]
    out = format_leaderboard(profiles)
    assert "1." in out
    assert "2." in out


def test_format_leaderboard_empty() -> None:
    from engine.profile_display import format_leaderboard

    out = format_leaderboard([])
    assert "No profiles" in out


# ── Cycle 4: CLI subcommand wiring ─────────────────────────────────



def test_cmd_profile_shows_single_player(capsys, tmp_path, monkeypatch) -> None:
    from agentgrounds.wars.cli.cmd_profile import run

    db_path = str(tmp_path / "test.db")
    from engine.profile_db import init_profile_db, update_profile

    conn = init_profile_db(db_path)
    update_profile(conn, "TestBot", xp_earned=700, kills=10, won=True)
    conn.close()

    args = type("Args", (), {"name": "TestBot", "db_path": db_path})()
    run(args)
    captured = capsys.readouterr()
    assert "TestBot" in captured.out
    assert "Level" in captured.out


def test_cmd_profile_unknown_player(capsys, tmp_path) -> None:
    from agentgrounds.wars.cli.cmd_profile import run

    db_path = str(tmp_path / "test.db")
    from engine.profile_db import init_profile_db

    conn = init_profile_db(db_path)
    conn.close()

    args = type("Args", (), {"name": "Nobody", "db_path": db_path})()
    run(args)
    captured = capsys.readouterr()
    assert "No profile found" in captured.out


def test_cmd_profile_leaderboard(capsys, tmp_path) -> None:
    from agentgrounds.wars.cli.cmd_profile import run

    db_path = str(tmp_path / "test.db")
    from engine.profile_db import init_profile_db, update_profile

    conn = init_profile_db(db_path)
    update_profile(conn, "BotA", xp_earned=500, kills=5, won=True)
    update_profile(conn, "BotB", xp_earned=200, kills=2, won=False)
    conn.close()

    args = type("Args", (), {"name": None, "db_path": db_path})()
    run(args)
    captured = capsys.readouterr()
    assert "BotA" in captured.out
    assert "BotB" in captured.out
    assert "Name" in captured.out


def test_cmd_profile_register_adds_subcommand() -> None:
    import argparse

    from agentgrounds.wars.cli.cmd_profile import register

    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest="subcommand")
    register(subs)
    args = parser.parse_args(["profile", "TestBot"])
    assert args.name == "TestBot"
    assert hasattr(args, "func")
