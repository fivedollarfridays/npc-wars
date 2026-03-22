"""Tests for diff display formatter and progression box."""

from __future__ import annotations


# ── Cycle 1: format_diff_section ──


def _make_diff_entry(
    classification: str,
    delta: float,
    percentage: float | None,
    lifetime_avg: float,
    current: float,
) -> dict:
    return {
        "classification": classification,
        "delta": delta,
        "percentage": percentage,
        "lifetime_avg": lifetime_avg,
        "current": current,
    }


def test_diff_section_improved_shows_up_arrow() -> None:
    from agentgrounds.wars.cli.diff_display import format_diff_section

    diff_data = {
        "win_rate": _make_diff_entry("improved", 3.0, 8.6, 35.0, 38.0),
    }
    result = format_diff_section(diff_data)
    assert "\u25b2" in result  # ▲
    assert "38" in result
    assert "35" in result


def test_diff_section_regressed_shows_down_arrow() -> None:
    from agentgrounds.wars.cli.diff_display import format_diff_section

    diff_data = {
        "avg_kills": _make_diff_entry("regressed", -0.5, -20.0, 2.5, 2.0),
    }
    result = format_diff_section(diff_data)
    assert "\u25bc" in result  # ▼


def test_diff_section_neutral_shows_dash() -> None:
    from agentgrounds.wars.cli.diff_display import format_diff_section

    diff_data = {
        "avg_kills": _make_diff_entry("neutral", 0.0, 0.0, 2.0, 2.0),
    }
    result = format_diff_section(diff_data)
    assert "\u2500" in result  # ─


def test_diff_section_empty_shows_first_match_message() -> None:
    from agentgrounds.wars.cli.diff_display import format_diff_section

    result = format_diff_section(None)
    assert "First match" in result

    result2 = format_diff_section({})
    assert "First match" in result2


def test_diff_section_ansi_green_for_improved() -> None:
    from agentgrounds.wars.cli.diff_display import format_diff_section

    diff_data = {
        "win_rate": _make_diff_entry("improved", 3.0, 8.6, 35.0, 38.0),
    }
    result = format_diff_section(diff_data)
    assert "\033[32m" in result  # green


def test_diff_section_ansi_red_for_regressed() -> None:
    from agentgrounds.wars.cli.diff_display import format_diff_section

    diff_data = {
        "avg_kills": _make_diff_entry("regressed", -0.5, -20.0, 2.5, 2.0),
    }
    result = format_diff_section(diff_data)
    assert "\033[31m" in result  # red


def test_diff_section_ansi_dim_for_neutral() -> None:
    from agentgrounds.wars.cli.diff_display import format_diff_section

    diff_data = {
        "avg_kills": _make_diff_entry("neutral", 0.0, 0.0, 2.0, 2.0),
    }
    result = format_diff_section(diff_data)
    assert "\033[90m" in result  # dim


# ── Cycle 2: format_progression ──


def test_progression_shows_level_change() -> None:
    from agentgrounds.wars.cli.diff_display import format_progression

    xp_data = {"total": 85, "new_xp": 1200}
    result = format_progression(xp_data, old_level=7, new_level=8)
    assert "7" in result
    assert "8" in result
    assert "\u2192" in result  # →
    assert "85" in result or "+85" in result


def test_progression_shows_unlocked_actions() -> None:
    from agentgrounds.wars.cli.diff_display import format_progression

    # Level 8 unlocks taunt + setup callback
    xp_data = {"total": 120, "new_xp": 1200}
    result = format_progression(xp_data, old_level=7, new_level=8)
    assert "taunt" in result.lower() or "UNLOCK" in result.upper()


def test_progression_shows_next_unlock() -> None:
    from agentgrounds.wars.cli.diff_display import format_progression

    xp_data = {"total": 85, "new_xp": 1200}
    result = format_progression(xp_data, old_level=7, new_level=8)
    # Should mention next unlock level (12 has trap + react)
    assert "Next" in result or "next" in result


def test_progression_no_xp_data_returns_empty() -> None:
    from agentgrounds.wars.cli.diff_display import format_progression

    result = format_progression(None, old_level=1, new_level=1)
    assert result == ""


def test_progression_no_level_change() -> None:
    from agentgrounds.wars.cli.diff_display import format_progression

    xp_data = {"total": 50, "new_xp": 600}
    result = format_progression(xp_data, old_level=5, new_level=5)
    assert "5" in result
    assert "+50" in result


# ── Cycle 3: format_match_summary ──


def test_summary_produces_boxed_output() -> None:
    from agentgrounds.wars.cli.diff_display import format_match_summary

    diff_data = {
        "win_rate": _make_diff_entry("improved", 3.0, 8.6, 35.0, 38.0),
    }
    xp_data = {"total": 85, "new_xp": 1200}
    result = format_match_summary(
        bot_name="Wraith",
        bot_glyph="\u25c6",
        placement=2,
        kills=3,
        rounds_survived=22,
        score=52,
        momentum_name="Tier 3",
        diff_data=diff_data,
        xp_data=xp_data,
        old_level=7,
        new_level=8,
    )
    # Box characters present
    assert "\u250c" in result  # ┌
    assert "\u2510" in result  # ┐
    assert "\u2514" in result  # └
    assert "\u2518" in result  # ┘
    assert "\u2502" in result  # │


def test_summary_contains_bot_name_and_glyph() -> None:
    from agentgrounds.wars.cli.diff_display import format_match_summary

    result = format_match_summary(
        bot_name="Wraith",
        bot_glyph="\u25c6",
        placement=2,
        kills=3,
        rounds_survived=22,
        score=52,
        momentum_name="Tier 3",
        diff_data=None,
        xp_data=None,
        old_level=1,
        new_level=1,
    )
    assert "Wraith" in result
    assert "\u25c6" in result


def test_summary_contains_placement_info() -> None:
    from agentgrounds.wars.cli.diff_display import format_match_summary

    result = format_match_summary(
        bot_name="Wraith",
        bot_glyph="\u25c6",
        placement=1,
        kills=5,
        rounds_survived=30,
        score=100,
        momentum_name="Tier 5",
        diff_data=None,
        xp_data=None,
        old_level=1,
        new_level=1,
    )
    assert "1st" in result
    assert "5 kills" in result


def test_summary_includes_diff_and_progression_sections() -> None:
    from agentgrounds.wars.cli.diff_display import format_match_summary

    diff_data = {
        "win_rate": _make_diff_entry("improved", 3.0, 8.6, 35.0, 38.0),
        "avg_kills": _make_diff_entry("regressed", -0.5, -20.0, 2.5, 2.0),
    }
    xp_data = {"total": 85, "new_xp": 1200}
    result = format_match_summary(
        bot_name="Wraith",
        bot_glyph="\u25c6",
        placement=2,
        kills=3,
        rounds_survived=22,
        score=52,
        momentum_name="Tier 3",
        diff_data=diff_data,
        xp_data=xp_data,
        old_level=7,
        new_level=8,
    )
    assert "Stats vs Lifetime" in result
    assert "Progression" in result
    assert "\u25b2" in result  # ▲ for improved
    assert "Level" in result
