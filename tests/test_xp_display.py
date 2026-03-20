"""Tests for engine.xp_display — post-match XP summary formatting."""

from __future__ import annotations


# ── Cycle 1: Basic single-bot formatting ────────────────────────────


class TestBasicFormatting:
    """format_xp_summary produces formatted output for a single bot."""

    def test_single_bot_shows_total_and_breakdown(self) -> None:
        """Single bot entry shows +XP total and component breakdown."""
        from engine.xp_display import format_xp_summary

        awards = {
            "A": {
                "base": 10, "kills": 30, "survival": 20,
                "placement": 50, "bonuses": 0, "total": 110,
                "new_level": 3, "leveled_up": False,
            },
        }
        result = format_xp_summary(awards)
        assert "+110 XP" in result
        assert "10 base" in result
        assert "30 kills" in result
        assert "20 survival" in result
        assert "50 win" in result
        assert "0 bonus" in result

    def test_header_and_footer_lines(self) -> None:
        """Output includes header and footer separator lines."""
        from engine.xp_display import format_xp_summary

        awards = {
            "A": {
                "base": 10, "kills": 0, "survival": 10,
                "placement": 0, "bonuses": 0, "total": 20,
                "new_level": 1, "leveled_up": False,
            },
        }
        result = format_xp_summary(awards)
        lines = result.strip().splitlines()
        assert "XP Awards" in lines[0]
        # Footer is the last line and contains dashes
        assert "──" in lines[-1]

    def test_emoji_key_used_as_label(self) -> None:
        """When no players list provided, emoji key is used as label."""
        from engine.xp_display import format_xp_summary

        awards = {
            "Z": {
                "base": 10, "kills": 0, "survival": 0,
                "placement": 0, "bonuses": 0, "total": 10,
                "new_level": 1, "leveled_up": False,
            },
        }
        result = format_xp_summary(awards)
        assert "Z" in result


# ── Cycle 2: Sorting and multiple bots ──────────────────────────────


class TestSortingAndMultipleBots:
    """Multiple bots sorted by total XP descending."""

    def test_sorted_by_total_xp_descending(self) -> None:
        """Bots appear in order of highest XP first."""
        from engine.xp_display import format_xp_summary

        awards = {
            "A": _award(total=50),
            "B": _award(total=150),
            "C": _award(total=80),
        }
        result = format_xp_summary(awards)
        # B (150) should appear before C (80) before A (50)
        b_pos = result.index("+150 XP")
        c_pos = result.index("+80 XP")
        a_pos = result.index("+50 XP")
        assert b_pos < c_pos < a_pos

    def test_name_mapping_from_players(self) -> None:
        """When players list provided, names replace emojis."""
        from engine.xp_display import format_xp_summary

        awards = {"A": _award(total=100)}
        players = [{"emoji": "A", "name": "GooseLoose"}]
        result = format_xp_summary(awards, players=players)
        assert "GooseLoose" in result

    def test_empty_awards_returns_empty(self) -> None:
        """Empty xp_awards dict returns empty string."""
        from engine.xp_display import format_xp_summary

        assert format_xp_summary({}) == ""


# ── Cycle 3: Level-up display with unlocks ──────────────────────────


class TestLevelUpDisplay:
    """Level-up lines appear below the bot entry with unlocks."""

    def test_level_up_line_shown(self) -> None:
        """When leveled_up is True, a LEVEL UP line appears."""
        from engine.xp_display import format_xp_summary

        awards = {"A": _award(total=100, new_level=5, leveled_up=True)}
        result = format_xp_summary(awards)
        assert "LEVEL UP" in result
        assert "Level" in result

    def test_level_up_shows_old_and_new_level(self) -> None:
        """Level-up line shows transition from old to new level."""
        from engine.xp_display import format_xp_summary

        # new_level=5 and leveled_up=True means old was 4
        awards = {"A": _award(total=100, new_level=5, leveled_up=True)}
        result = format_xp_summary(awards)
        # Should contain something like "Level 4 -> 5"
        assert "4" in result
        assert "5" in result

    def test_level_up_shows_unlocked_actions(self) -> None:
        """Level 5 unlocks 'dash' and 'on_kill' -- these should appear."""
        from engine.xp_display import format_xp_summary

        awards = {"A": _award(total=100, new_level=5, leveled_up=True)}
        result = format_xp_summary(awards)
        # Level 5 milestone unlocks dash + on_kill
        assert "dash" in result
        assert "on_kill" in result

    def test_no_level_up_no_extra_line(self) -> None:
        """When leveled_up is False, no LEVEL UP line."""
        from engine.xp_display import format_xp_summary

        awards = {"A": _award(total=50, new_level=2, leveled_up=False)}
        result = format_xp_summary(awards)
        assert "LEVEL UP" not in result

    def test_level_up_no_unlocks_at_level(self) -> None:
        """Level-up to a level with no new unlocks still shows level change."""
        from engine.xp_display import format_xp_summary

        # Level 2 has no new actions or callbacks
        awards = {"A": _award(total=50, new_level=2, leveled_up=True)}
        result = format_xp_summary(awards)
        assert "LEVEL UP" in result
        assert "1" in result  # old level
        assert "2" in result  # new level


# ── Cycle 4: Edge cases ─────────────────────────────────────────────


class TestEdgeCases:
    """Edge cases: placement labels, multi-level jumps, four-bot match."""

    def test_second_place_shows_place_label(self) -> None:
        """Placement of 25 (2nd place) shows 'place' label."""
        from engine.xp_display import format_xp_summary

        awards = {"A": _award(placement=25, total=45)}
        result = format_xp_summary(awards)
        assert "25 place" in result

    def test_zero_placement_no_label(self) -> None:
        """Placement of 0 shows no label (just '0')."""
        from engine.xp_display import format_xp_summary

        awards = {"A": _award(placement=0, total=10)}
        result = format_xp_summary(awards)
        assert "0 win" not in result

    def test_four_bot_match_output(self) -> None:
        """Full four-bot match produces expected line count."""
        from engine.xp_display import format_xp_summary

        awards = {
            "A": _award(total=150, new_level=5, leveled_up=True),
            "B": _award(total=82),
            "C": _award(total=52),
            "D": _award(total=22),
        }
        players = [
            {"emoji": "A", "name": "GooseLoose"},
            {"emoji": "B", "name": "AggroBoy"},
            {"emoji": "C", "name": "TankBot"},
            {"emoji": "D", "name": "ChaosBot"},
        ]
        result = format_xp_summary(awards, players=players)
        lines = result.splitlines()
        # header + 4 bots + 1 level-up line + footer = 7
        assert len(lines) == 7
        assert "GooseLoose" in lines[1]
        assert "LEVEL UP" in lines[2]
        assert "ChaosBot" in lines[-2]

    def test_returns_string_type(self) -> None:
        """format_xp_summary returns a str."""
        from engine.xp_display import format_xp_summary

        result = format_xp_summary({"A": _award(total=10)})
        assert isinstance(result, str)


def _award(
    *,
    base: int = 10,
    kills: int = 0,
    survival: int = 0,
    placement: int = 0,
    bonuses: int = 0,
    total: int | None = None,
    new_level: int = 1,
    leveled_up: bool = False,
) -> dict:
    """Build a test award dict with sensible defaults."""
    return {
        "base": base,
        "kills": kills,
        "survival": survival,
        "placement": placement,
        "bonuses": bonuses,
        "total": total if total is not None else (base + kills + survival + placement + bonuses),
        "new_level": new_level,
        "leveled_up": leveled_up,
    }
