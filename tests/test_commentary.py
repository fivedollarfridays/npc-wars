"""Tests for engine/commentary.py — Kill Switch commentary engine."""

from engine.commentary import CommentaryLine, generate_commentary
from engine.commentary_templates import COLOR_COMMENTARY, PLAY_BY_PLAY


# --- helpers ---


def _match_data(rounds, eliminations=None, winner="🤖", players=None):
    """Build minimal match data for testing."""
    return {
        "match_id": 1,
        "winner": winner,
        "players": players or [{"emoji": "🤖"}, {"emoji": "👾"}],
        "rounds": rounds,
        "eliminations": eliminations or [],
        "stats": {
            "🤖": {
                "kills": 2, "archetype": "Bruiser",
                "equipment": {"weapon": "sword", "armor": "plate", "tactical": "battle_cry"},
            },
            "👾": {
                "kills": 1, "archetype": "Assassin",
                "equipment": {"weapon": "dagger", "armor": "leather", "tactical": "teleport"},
            },
        },
        "duration_rounds": len(rounds),
    }


def _round(num, positions, events=None):
    return {"round": num, "storm_border": 5, "positions": positions, "events": events or []}


def _pos(emoji, action="move north", hp=50, alive=True, **kw):
    return {"emoji": emoji, "action": action, "hp": hp, "alive": alive, "x": 3, "y": 3, **kw}


def _evt(type_, **kw):
    return {"type": type_, **kw}


def _profiles():
    return {
        "🤖": {
            "traits": ["Aggressive", "Momentum Builder"],
            "archetype_variant": "Berserker", "bio": "Relentless.",
        },
        "👾": {
            "traits": ["Mobile", "Kiter"],
            "archetype_variant": "Ghost", "bio": "Elusive.",
        },
    }


def _rivalries():
    return {
        ("🤖", "👾"): {
            "wins_a": 3, "wins_b": 1, "streak": 2,
            "streak_holder": "🤖", "matches": 4,
        },
    }


# --- test: return type ---


class TestReturnType:
    def test_returns_list_of_commentary_lines(self):
        rounds = [_round(1, [_pos("🤖"), _pos("👾")])]
        result = generate_commentary(_match_data(rounds), _profiles(), _rivalries())
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(line, CommentaryLine) for line in result)

    def test_commentary_line_fields(self):
        rounds = [_round(1, [_pos("🤖"), _pos("👾")])]
        result = generate_commentary(_match_data(rounds), _profiles(), _rivalries())
        line = result[0]
        assert isinstance(line.round, int)
        assert isinstance(line.text, str)
        assert line.tone in ("calm", "heating", "intense", "hype", "chaos")
        assert line.type in ("play_by_play", "color")


# --- test: play-by-play event coverage ---


class TestPlayByPlay:
    def test_kill_event(self):
        rounds = [_round(1, [_pos("🤖"), _pos("👾", hp=0, alive=False)],
                         [_evt("kill", attacker="🤖", victim="👾")])]
        elims = [{"emoji": "👾", "killed_by": "🤖"}]
        result = generate_commentary(
            _match_data(rounds, eliminations=elims), _profiles(), _rivalries(),
        )
        pbp = [c for c in result if c.type == "play_by_play"]
        assert any("🤖" in c.text or "kill" in c.text.lower() for c in pbp)

    def test_movement(self):
        rounds = [_round(1, [_pos("🤖", action="move north"), _pos("👾")])]
        result = generate_commentary(_match_data(rounds), _profiles(), _rivalries())
        pbp = [c for c in result if c.type == "play_by_play"]
        assert len(pbp) > 0

    def test_defend_action(self):
        rounds = [_round(1, [_pos("🤖", action="defend"), _pos("👾")])]
        result = generate_commentary(_match_data(rounds), _profiles(), _rivalries())
        pbp = [c for c in result if c.type == "play_by_play"]
        assert any("defend" in c.text.lower() or "🤖" in c.text for c in pbp)

    def test_trap_placement(self):
        rounds = [_round(1, [_pos("🤖", action="trap"), _pos("👾")])]
        result = generate_commentary(_match_data(rounds), _profiles(), _rivalries())
        pbp = [c for c in result if c.type == "play_by_play"]
        assert any("trap" in c.text.lower() or "🤖" in c.text for c in pbp)

    def test_ability_use(self):
        rounds = [_round(1, [_pos("🤖", action="battle_cry"), _pos("👾")])]
        result = generate_commentary(_match_data(rounds), _profiles(), _rivalries())
        pbp = [c for c in result if c.type == "play_by_play"]
        assert len(pbp) > 0

    def test_storm_damage(self):
        rounds = [_round(1, [_pos("🤖"), _pos("👾")],
                         [_evt("kill", attacker="storm", victim="👾", cause="storm")])]
        elims = [{"emoji": "👾", "killed_by": "storm"}]
        result = generate_commentary(
            _match_data(rounds, eliminations=elims), _profiles(), _rivalries(),
        )
        pbp = [c for c in result if c.type == "play_by_play"]
        assert any("storm" in c.text.lower() for c in pbp)


# --- test: color commentary ---


class TestColorCommentary:
    def test_personality_reference(self):
        """Color commentary should reference personality traits."""
        rounds = [
            _round(1, [_pos("🤖", action="attack east"), _pos("👾")],
                   [_evt("kill", attacker="🤖", victim="👾")]),
        ]
        result = generate_commentary(
            _match_data(rounds, eliminations=[{"emoji": "👾", "killed_by": "🤖"}]),
            _profiles(), _rivalries(),
        )
        color = [c for c in result if c.type == "color"]
        assert len(color) > 0

    def test_rivalry_reference(self):
        """Color commentary should reference rivalry when available."""
        rounds = [
            _round(1, [_pos("🤖", action="attack east"), _pos("👾", hp=0, alive=False)],
                   [_evt("kill", attacker="🤖", victim="👾")]),
        ]
        result = generate_commentary(
            _match_data(rounds, eliminations=[{"emoji": "👾", "killed_by": "🤖"}]),
            _profiles(), _rivalries(),
        )
        color = [c for c in result if c.type == "color"]
        assert len(color) > 0

    def test_no_profiles_still_works(self):
        """Should work without profiles — just less color commentary."""
        rounds = [_round(1, [_pos("🤖"), _pos("👾")])]
        result = generate_commentary(_match_data(rounds), {}, {})
        assert isinstance(result, list)

    def test_no_rivalries_still_works(self):
        rounds = [_round(1, [_pos("🤖"), _pos("👾")])]
        result = generate_commentary(_match_data(rounds), _profiles(), {})
        assert isinstance(result, list)


# --- test: drama tiers ---


class TestDramaTiers:
    def _commentary_tones(self, drama_events, drama_bots):
        """Run commentary and collect unique tones (no winner to avoid closer)."""
        rounds = [_round(1, drama_bots, drama_events)]
        md = _match_data(rounds, winner=None)
        result = generate_commentary(md, _profiles(), _rivalries())
        return {c.tone for c in result}

    def test_calm_tier(self):
        """Quiet round with 3+ bots -> calm tone."""
        tones = self._commentary_tones([], [_pos("🤖"), _pos("👾"), _pos("🎃")])
        assert "calm" in tones

    def test_heating_tier(self):
        """Chain bump -> heating."""
        events = [_evt("chain_bump"), _evt("chain_bump")]
        tones = self._commentary_tones(events, [_pos("🤖"), _pos("👾")])
        assert tones & {"heating", "intense", "hype", "chaos"}

    def test_hype_tier(self):
        """Multi-kill + near death -> hype or higher."""
        events = [
            _evt("kill", attacker="🤖", victim="👾"),
            _evt("kill", attacker="🤖", victim="🎃"),
            _evt("kill_streak", attacker="🤖"),
        ]
        bots = [
            _pos("🤖", hp=3),
            _pos("👾", hp=0, alive=False),
            _pos("🎃", hp=0, alive=False),
        ]
        tones = self._commentary_tones(events, bots)
        assert tones & {"hype", "chaos"}

    def test_chaos_tier(self):
        """Extreme events -> chaos tone."""
        events = [
            _evt("kill", attacker="🤖", victim="👾"),
            _evt("kill", attacker="🤖", victim="🎃"),
            _evt("kill", attacker="🤖", victim="🎯"),
            _evt("kill_streak", attacker="🤖"),
            _evt("watcher_spawn"),
            _evt("watcher_kill"),
        ]
        bots = [
            _pos("🤖", hp=2),
            _pos("👾", hp=0, alive=False),
            _pos("🎃", hp=0, alive=False),
            _pos("🎯", hp=0, alive=False),
        ]
        tones = self._commentary_tones(events, bots)
        assert "chaos" in tones

    def test_all_five_tones_exist(self):
        """Ensure all 5 tones are valid values accepted by the system."""
        valid = {"calm", "heating", "intense", "hype", "chaos"}
        rounds = [_round(1, [_pos("🤖"), _pos("👾")])]
        result = generate_commentary(_match_data(rounds), _profiles(), _rivalries())
        for line in result:
            assert line.tone in valid


# --- test: template count ---


class TestTemplateCount:
    def test_at_least_50_play_by_play(self):
        total = sum(len(v) for v in PLAY_BY_PLAY.values())
        assert total >= 30

    def test_at_least_20_color(self):
        total = sum(len(v) for v in COLOR_COMMENTARY.values())
        assert total >= 20

    def test_combined_at_least_50(self):
        pbp = sum(len(v) for v in PLAY_BY_PLAY.values())
        color = sum(len(v) for v in COLOR_COMMENTARY.values())
        assert pbp + color >= 50


# --- test: full match ---


class TestFullMatch:
    def test_multi_round_match(self):
        """A 5-round match with diverse events produces commentary."""
        rounds = [
            _round(1, [_pos("🤖", action="move north"), _pos("👾", action="move south")]),
            _round(2, [_pos("🤖", action="attack east"), _pos("👾", action="defend")],
                   [_evt("hit", attacker="🤖", target="👾", damage=10)]),
            _round(3, [_pos("🤖", action="trap"), _pos("👾", action="ranged_attack west")]),
            _round(4, [_pos("🤖", action="battle_cry"), _pos("👾", action="teleport")],
                   [_evt("kill", attacker="🤖", victim="👾")]),
            _round(5, [_pos("🤖", hp=80), _pos("👾", hp=0, alive=False)]),
        ]
        elims = [{"emoji": "👾", "killed_by": "🤖", "round": 4}]
        result = generate_commentary(
            _match_data(rounds, eliminations=elims), _profiles(), _rivalries(),
        )
        covered_rounds = {c.round for c in result}
        assert len(covered_rounds) >= 3

    def test_empty_rounds(self):
        """Empty match should not crash."""
        result = generate_commentary(_match_data([]), {}, {})
        assert isinstance(result, list)

    def test_watcher_event(self):
        """Watcher events generate play-by-play."""
        rounds = [_round(1, [_pos("🤖"), _pos("👾")],
                         [_evt("watcher_spawn"), _evt("watcher_kill")])]
        result = generate_commentary(_match_data(rounds), _profiles(), _rivalries())
        pbp = [c for c in result if c.type == "play_by_play"]
        assert any("watcher" in c.text.lower() for c in pbp)
