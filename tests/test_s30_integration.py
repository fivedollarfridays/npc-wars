"""S30 Integration Gate -- Visual identity system end-to-end."""

from __future__ import annotations

from pathlib import Path

from engine.game import run_match
from engine.loader import load_bots
from agentgrounds.wars.cli.renderer import TerminalRenderer

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BOTS_DIR = "bots"
SEED = 42


def _builtin_configs() -> list[dict]:
    return load_bots(BOTS_DIR)


def _seeded_match(seed: int = SEED, configs: list[dict] | None = None) -> dict:
    cfgs = configs if configs is not None else _builtin_configs()
    return run_match(cfgs, match_id=1, seed=seed)


def _make_renderer(match_data: dict) -> TerminalRenderer:
    return TerminalRenderer(
        players=match_data.get("players", []),
        grid_size=match_data.get("grid_size", 10),
    )


# ===========================================================================
# 1. Position data has glyph
# ===========================================================================


class TestPositionDataHasGlyph:
    """Every position record in round data must contain a glyph field."""

    def test_position_data_has_glyph(self) -> None:
        match = _seeded_match()
        for rnd in match["rounds"]:
            for p in rnd["positions"]:
                assert "glyph" in p, (
                    f"Position for {p['emoji']} in round {rnd['round']} "
                    f"missing 'glyph' field"
                )


# ===========================================================================
# 2. Players array has glyph
# ===========================================================================


class TestPlayersArrayHasGlyph:
    """Match data players list must contain glyph for each player."""

    def test_players_array_has_glyph(self) -> None:
        match = _seeded_match()
        for player in match["players"]:
            assert "glyph" in player, (
                f"Player {player['name']} missing 'glyph' field"
            )


# ===========================================================================
# 3. Glyph in rendered grid
# ===========================================================================


class TestGlyphInRenderedGrid:
    """Rendered grid frame should contain glyph characters (not just emoji)."""

    def test_glyph_in_rendered_grid(self) -> None:
        match = _seeded_match()
        renderer = _make_renderer(match)
        # Use a mid-match round where bots are alive
        mid = min(5, len(match["rounds"]) - 1)
        frame = renderer.render_frame(match["rounds"][mid], clear=False)

        # Collect glyphs from alive bots (glyph may equal emoji for fallback)
        alive_glyphs = {
            p["glyph"] for p in match["rounds"][mid]["positions"]
            if p["alive"]
        }
        assert len(alive_glyphs) > 0, "No glyphs found in alive bots"
        # At least one glyph character should appear in the frame
        found = any(g in frame for g in alive_glyphs)
        assert found, (
            f"No glyph characters found in rendered frame. "
            f"Alive glyphs: {alive_glyphs}"
        )


# ===========================================================================
# 4. Glyph has ANSI color
# ===========================================================================


class TestGlyphHasAnsiColor:
    """Rendered glyph must have ANSI escape codes for HP coloring."""

    def test_glyph_has_ansi_color(self) -> None:
        match = _seeded_match()
        renderer = _make_renderer(match)
        mid = min(5, len(match["rounds"]) - 1)
        frame = renderer.render_frame(match["rounds"][mid], clear=False)
        # ANSI escape codes start with \033[
        assert "\033[" in frame, "No ANSI escape codes found in rendered frame"


# ===========================================================================
# 5. Roster shows glyph
# ===========================================================================


class TestRosterShowsGlyph:
    """Roster lines must contain glyph characters."""

    def test_roster_shows_glyph(self) -> None:
        match = _seeded_match()
        renderer = _make_renderer(match)
        mid = min(5, len(match["rounds"]) - 1)
        frame = renderer.render_frame(match["rounds"][mid], clear=False)

        # Roster section starts after "Combatants"
        lines = frame.split("\n")
        roster_lines = []
        in_roster = False
        for line in lines:
            if "Combatants" in line:
                in_roster = True
                continue
            if in_roster:
                if line.strip() == "":
                    break
                roster_lines.append(line)

        assert len(roster_lines) > 0, "No roster lines found"

        # Collect glyphs from that round's positions (glyph may equal emoji)
        round_glyphs = {
            p["glyph"] for p in match["rounds"][mid]["positions"]
        }
        assert len(round_glyphs) > 0, "No glyphs in round data"

        # At least one glyph should appear in roster
        found = any(
            g in line
            for g in round_glyphs
            for line in roster_lines
        )
        assert found, (
            f"No glyph characters in roster lines. "
            f"Glyphs: {round_glyphs}"
        )


# ===========================================================================
# 6. Leader diamond in overlay
# ===========================================================================


class TestLeaderDiamondInOverlay:
    """Leader should have gold diamond in overlay."""

    def test_leader_diamond_in_overlay(self) -> None:
        match = _seeded_match()
        renderer = _make_renderer(match)

        # Find a round where a leader exists
        for rnd in match["rounds"]:
            leaders = [p for p in rnd["positions"] if p.get("is_leader")]
            if leaders:
                frame = renderer.render_frame(rnd, clear=False)
                # Diamond character used for leader overlay
                assert "\u2666" in frame, (
                    f"Leader diamond not found in frame for round {rnd['round']}"
                )
                return

        # If no leader found in any round, that's unexpected but not a failure
        # of the visual identity system itself
        assert False, "No leader found in any round -- cannot verify diamond"


# ===========================================================================
# 7. Emoji fallback
# ===========================================================================


class TestEmojiFallback:
    """Bot without BOT_GLYPH should use emoji as glyph."""

    def test_emoji_fallback(self) -> None:
        """Template bot has no BOT_GLYPH, so glyph should equal emoji."""
        from tests.conftest import bot_config, always_rest

        # Create a bot without glyph (like template)
        cfg = bot_config("NoGlyph", "\U0001f47b", always_rest)
        # bot_config does not set glyph, so it should be None
        assert "glyph" not in cfg or cfg.get("glyph") is None

        # When the game creates a Bot, it falls back to emoji
        from engine.combat import Bot
        bot = Bot(
            name="NoGlyph", emoji="\U0001f47b", bio="", author="test",
            decide_func=always_rest, x=0, y=0, glyph=None,
        )
        assert bot.glyph == "\U0001f47b", (
            f"Expected emoji fallback, got glyph={bot.glyph!r}"
        )


# ===========================================================================
# 8. All builtins have glyph
# ===========================================================================


class TestAllBuiltinsHaveGlyph:
    """All builtin bot source files (except template) should have BOT_GLYPH."""

    def test_all_builtins_have_glyph(self) -> None:
        from agentgrounds.wars.builtin_bots import BUILTIN_NAMES, get_bot_source

        glyphs: dict[str, str] = {}
        for name in BUILTIN_NAMES:
            if name == "template":
                continue
            source = get_bot_source(name)
            assert "BOT_GLYPH" in source, (
                f"Builtin bot {name} missing BOT_GLYPH declaration"
            )
            # Extract glyph value from source
            for line in source.splitlines():
                if line.startswith("BOT_GLYPH"):
                    # e.g. BOT_GLYPH = "⚔"
                    glyph = line.split("=", 1)[1].strip().strip('"').strip("'")
                    glyphs[name] = glyph
                    break

        assert len(glyphs) >= 5, (
            f"Expected >= 5 builtin bots with glyph, got {len(glyphs)}"
        )
        # All glyphs should be distinct
        glyph_values = list(glyphs.values())
        assert len(set(glyph_values)) == len(glyph_values), (
            f"Duplicate glyphs among builtins: {glyphs}"
        )


# ===========================================================================
# 9. Renderer under limits
# ===========================================================================


class TestRendererUnderLimits:
    """renderer.py must stay under architecture limits."""

    def test_renderer_under_limits(self) -> None:
        path = Path("agentgrounds/wars/cli/renderer.py")
        lines = path.read_text().splitlines()
        assert len(lines) < 400, f"renderer.py has {len(lines)} lines (limit 400)"

        func_count = sum(1 for ln in lines if ln.lstrip().startswith("def "))
        assert func_count <= 15, (
            f"renderer.py has {func_count} functions (limit 15)"
        )


# ===========================================================================
# 10. No regressions — basic match
# ===========================================================================


class TestNoRegressionsBasicMatch:
    """Full match should complete with a winner."""

    def test_no_regressions_basic_match(self) -> None:
        match = _seeded_match()
        assert match["winner"] != "none", "Match ended with no winner"
        assert len(match["rounds"]) > 0, "Match has no rounds"
        assert "players" in match, "Match data missing players"
        assert "stats" in match, "Match data missing stats"
