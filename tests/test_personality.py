"""Tests for engine/personality.py — Kill Switch personality profiler."""

import json

from engine.personality import profile_bot


def _write_match(tmp_path, match_id, emoji, stats, rounds=None, elims=None):
    """Write a minimal match JSON to tmp_path/results/."""
    results_dir = tmp_path / "results"
    results_dir.mkdir(exist_ok=True)
    match = {
        "match_id": match_id,
        "date": "2026-04-01",
        "winner": stats.get("_winner", emoji),
        "players": [{"emoji": emoji}],
        "duration_rounds": stats.get("rounds_survived", 10),
        "stats": {emoji: {k: v for k, v in stats.items() if not k.startswith("_")}},
        "rounds": rounds or [],
        "eliminations": elims or [],
    }
    (results_dir / f"match_{match_id:03d}.json").write_text(json.dumps(match))
    return str(results_dir)


def _write_patterns(tmp_path, emoji, pattern_data):
    """Write a pattern table JSON for a bot."""
    patterns_dir = tmp_path / "patterns"
    patterns_dir.mkdir(exist_ok=True)
    (patterns_dir / f"{emoji}.json").write_text(json.dumps(pattern_data))
    return str(patterns_dir)


def _make_rounds(actions, emoji):
    """Build round list from a list of action strings."""
    return [
        {"round": i + 1, "positions": [{"emoji": emoji, "action": a}]}
        for i, a in enumerate(actions)
    ]


# ── Graceful first-match / no-data ────────────────────────────────


class TestFirstMatch:
    def test_no_results_dir(self, tmp_path):
        result = profile_bot("🤖", str(tmp_path / "nope"), str(tmp_path / "nope2"))
        assert result["archetype_variant"] == "Unknown"
        assert result["traits"] == []
        assert isinstance(result["bio"], str)
        assert len(result["bio"]) > 0

    def test_no_matches_for_bot(self, tmp_path):
        results_dir = tmp_path / "results"
        results_dir.mkdir()
        result = profile_bot("🤖", str(results_dir), str(tmp_path / "patterns"))
        assert result["archetype_variant"] == "Unknown"
        assert result["traits"] == []

    def test_single_match_minimal(self, tmp_path):
        stats = {
            "kills": 0, "damage_dealt": 10, "damage_taken": 50,
            "rounds_survived": 5, "score": 10, "momentum_tier": 0,
            "archetype": "Balanced",
            "equipment": {"weapon": "sword", "armor": "leather",
                          "accessories": [], "tactical": None},
        }
        results_dir = _write_match(tmp_path, 1, "🤖", stats)
        result = profile_bot("🤖", results_dir, str(tmp_path / "patterns"))
        assert "archetype_variant" in result
        assert "traits" in result
        assert "bio" in result
        assert isinstance(result["bio"], str)


# ── Aggressive bot ─────────────────────────────────────────────────


class TestAggressiveBot:
    def test_high_kills_high_damage(self, tmp_path):
        results_dir = None
        for i in range(5):
            stats = {
                "kills": 4, "damage_dealt": 120, "damage_taken": 30,
                "rounds_survived": 15, "score": 80, "momentum_tier": 3,
                "archetype": "Bruiser", "_winner": "🤖",
                "equipment": {"weapon": "axe", "armor": "leather",
                              "accessories": [], "tactical": "battle_cry"},
            }
            actions = ["attack east"] * 10 + ["move north"] * 5
            rounds = _make_rounds(actions, "🤖")
            results_dir = _write_match(tmp_path, i + 1, "🤖", stats, rounds)

        result = profile_bot("🤖", results_dir, str(tmp_path / "patterns"))
        assert "aggressive" in " ".join(result["traits"]).lower() or any(
            "aggress" in t.lower() for t in result["traits"]
        )

    def test_opener_trait_from_early_attacks(self, tmp_path):
        results_dir = None
        for i in range(5):
            stats = {
                "kills": 2, "damage_dealt": 80, "damage_taken": 40,
                "rounds_survived": 12, "score": 50, "momentum_tier": 2,
                "archetype": "Assassin",
                "equipment": {"weapon": "dagger", "armor": "leather",
                              "accessories": ["boots_of_speed"], "tactical": None},
            }
            actions = ["attack east", "attack west", "attack north"] + ["rest"] * 9
            rounds = _make_rounds(actions, "🤖")
            results_dir = _write_match(tmp_path, i + 1, "🤖", stats, rounds)

        result = profile_bot("🤖", results_dir, str(tmp_path / "patterns"))
        assert any("opener" in t.lower() for t in result["traits"])


# ── Defensive bot ──────────────────────────────────────────────────


class TestDefensiveBot:
    def test_high_defense_low_kills(self, tmp_path):
        results_dir = None
        for i in range(5):
            stats = {
                "kills": 0, "damage_dealt": 15, "damage_taken": 80,
                "rounds_survived": 40, "score": 90, "momentum_tier": 1,
                "archetype": "Tank",
                "equipment": {"weapon": "mace", "armor": "plate",
                              "accessories": ["ring_of_health"], "tactical": "fortify"},
            }
            actions = ["defend"] * 15 + ["rest"] * 20 + ["move north"] * 5
            rounds = _make_rounds(actions, "🤖")
            results_dir = _write_match(tmp_path, i + 1, "🤖", stats, rounds)

        result = profile_bot("🤖", results_dir, str(tmp_path / "patterns"))
        traits_lower = [t.lower() for t in result["traits"]]
        assert any("defen" in t or "turtle" in t or "surviv" in t for t in traits_lower)

    def test_heavy_armor_trait(self, tmp_path):
        results_dir = None
        for i in range(5):
            stats = {
                "kills": 1, "damage_dealt": 30, "damage_taken": 60,
                "rounds_survived": 30, "score": 60, "momentum_tier": 1,
                "archetype": "Tank",
                "equipment": {"weapon": "mace", "armor": "plate",
                              "accessories": ["ring_of_health", "cloak_of_shadows"],
                              "tactical": "fortify"},
            }
            results_dir = _write_match(tmp_path, i + 1, "🤖", stats)

        result = profile_bot("🤖", results_dir, str(tmp_path / "patterns"))
        traits_lower = [t.lower() for t in result["traits"]]
        assert any("armor" in t or "fortif" in t or "tank" in t for t in traits_lower)


# ── Balanced bot ───────────────────────────────────────────────────


class TestBalancedBot:
    def test_balanced_stats(self, tmp_path):
        results_dir = None
        for i in range(5):
            stats = {
                "kills": 1, "damage_dealt": 50, "damage_taken": 50,
                "rounds_survived": 20, "score": 50, "momentum_tier": 2,
                "archetype": "Balanced",
                "equipment": {"weapon": "sword", "armor": "chain_mail",
                              "accessories": [], "tactical": None},
            }
            actions = ["attack east"] * 5 + ["defend"] * 5 + ["move north"] * 5 + ["rest"] * 5
            rounds = _make_rounds(actions, "🤖")
            results_dir = _write_match(tmp_path, i + 1, "🤖", stats, rounds)

        result = profile_bot("🤖", results_dir, str(tmp_path / "patterns"))
        assert result["archetype_variant"] != "Unknown"


# ── Trap-heavy bot ─────────────────────────────────────────────────


class TestTrapHeavyBot:
    def test_trap_obsessed(self, tmp_path):
        results_dir = None
        for i in range(5):
            stats = {
                "kills": 2, "damage_dealt": 40, "damage_taken": 30,
                "rounds_survived": 25, "score": 60, "momentum_tier": 2,
                "archetype": "Controller",
                "equipment": {"weapon": "bow", "armor": "crystal",
                              "accessories": ["pendant_of_mind"], "tactical": None},
            }
            actions = ["trap"] * 12 + ["move north"] * 8 + ["rest"] * 5
            rounds = _make_rounds(actions, "🤖")
            results_dir = _write_match(tmp_path, i + 1, "🤖", stats, rounds)

        result = profile_bot("🤖", results_dir, str(tmp_path / "patterns"))
        traits_lower = [t.lower() for t in result["traits"]]
        assert any("trap" in t for t in traits_lower)


# ── Pattern-based traits ───────────────────────────────────────────


class TestPatternTraits:
    def test_storm_dodger_from_patterns(self, tmp_path):
        stats = {
            "kills": 1, "damage_dealt": 40, "damage_taken": 30,
            "rounds_survived": 30, "score": 70, "momentum_tier": 2,
            "archetype": "Assassin",
            "equipment": {"weapon": "dagger", "armor": "leather",
                          "accessories": [], "tactical": "teleport"},
        }
        for i in range(5):
            _write_match(tmp_path, i + 1, "🤖", stats)

        patterns_dir = _write_patterns(tmp_path, "🤖", {
            "storm_closing": {"move": 20, "dash": 15, "teleport": 5},
        })
        result = profile_bot("🤖", str(tmp_path / "results"), patterns_dir)
        traits_lower = [t.lower() for t in result["traits"]]
        assert any("storm" in t for t in traits_lower)

    def test_counter_puncher_from_patterns(self, tmp_path):
        stats = {
            "kills": 2, "damage_dealt": 60, "damage_taken": 40,
            "rounds_survived": 20, "score": 50, "momentum_tier": 2,
            "archetype": "Balanced",
            "equipment": {"weapon": "sword", "armor": "chain_mail",
                          "accessories": [], "tactical": None},
        }
        for i in range(5):
            _write_match(tmp_path, i + 1, "🤖", stats)

        patterns_dir = _write_patterns(tmp_path, "🤖", {
            "after_damage": {"attack": 25, "defend": 5},
        })
        result = profile_bot("🤖", str(tmp_path / "results"), patterns_dir)
        traits_lower = [t.lower() for t in result["traits"]]
        assert any("counter" in t or "retaliat" in t for t in traits_lower)


# ── Bio and archetype variant ──────────────────────────────────────


class TestBioGeneration:
    def test_bio_is_one_or_two_sentences(self, tmp_path):
        for i in range(3):
            stats = {
                "kills": 3, "damage_dealt": 100, "damage_taken": 20,
                "rounds_survived": 15, "score": 70, "momentum_tier": 3,
                "archetype": "Bruiser",
                "equipment": {"weapon": "axe", "armor": "leather",
                              "accessories": [], "tactical": "battle_cry"},
            }
            _write_match(tmp_path, i + 1, "🤖", stats)

        result = profile_bot("🤖", str(tmp_path / "results"), str(tmp_path / "p"))
        bio = result["bio"]
        assert isinstance(bio, str)
        sentences = [s.strip() for s in bio.split(".") if s.strip()]
        assert 1 <= len(sentences) <= 2

    def test_archetype_variant_not_unknown_with_data(self, tmp_path):
        for i in range(3):
            stats = {
                "kills": 3, "damage_dealt": 100, "damage_taken": 20,
                "rounds_survived": 15, "score": 70, "momentum_tier": 3,
                "archetype": "Bruiser",
                "equipment": {"weapon": "axe", "armor": "leather",
                              "accessories": [], "tactical": "battle_cry"},
            }
            _write_match(tmp_path, i + 1, "🤖", stats)

        result = profile_bot("🤖", str(tmp_path / "results"), str(tmp_path / "p"))
        assert result["archetype_variant"] != "Unknown"


# ── Trait count ────────────────────────────────────────────────────


_COVERAGE_PROFILES = [
    {"kills": 5, "damage_dealt": 150, "damage_taken": 20,
     "rounds_survived": 10, "score": 80, "momentum_tier": 4,
     "archetype": "Bruiser", "_winner": "🤖",
     "equipment": {"weapon": "axe", "armor": "leather",
                   "accessories": [], "tactical": "battle_cry"},
     "_actions": ["attack east"] * 10,
     "_patterns": {"after_damage": {"attack": 20}}},
    {"kills": 0, "damage_dealt": 10, "damage_taken": 80,
     "rounds_survived": 45, "score": 100, "momentum_tier": 1,
     "archetype": "Tank",
     "equipment": {"weapon": "mace", "armor": "plate",
                   "accessories": ["ring_of_health"], "tactical": "fortify"},
     "_actions": ["defend"] * 20 + ["rest"] * 20, "_patterns": None},
    {"kills": 2, "damage_dealt": 40, "damage_taken": 30,
     "rounds_survived": 25, "score": 60, "momentum_tier": 2,
     "archetype": "Controller",
     "equipment": {"weapon": "bow", "armor": "crystal",
                   "accessories": ["pendant_of_mind"], "tactical": None},
     "_actions": ["trap"] * 15 + ["move north"] * 10, "_patterns": None},
    {"kills": 3, "damage_dealt": 90, "damage_taken": 15,
     "rounds_survived": 20, "score": 70, "momentum_tier": 3,
     "archetype": "Controller",
     "equipment": {"weapon": "bow", "armor": "leather",
                   "accessories": ["compass"], "tactical": None},
     "_actions": ["ranged_attack east"] * 15 + ["move north"] * 5,
     "_patterns": {"at_range_1": {"ranged_attack": 15, "move": 5}}},
    {"kills": 1, "damage_dealt": 30, "damage_taken": 25,
     "rounds_survived": 30, "score": 55, "momentum_tier": 2,
     "archetype": "Assassin",
     "equipment": {"weapon": "dagger", "armor": "leather",
                   "accessories": ["boots_of_speed"], "tactical": "teleport"},
     "_actions": ["dash"] * 10 + ["move east"] * 10 + ["attack north"] * 5,
     "_patterns": None},
]


def _profile_from_spec(tmp_path, pidx, prof):
    """Write matches + patterns for a profile spec, return traits."""
    import copy
    prof = copy.deepcopy(prof)
    sub = tmp_path / f"bot_{pidx}"
    sub.mkdir()
    actions = prof.pop("_actions")
    pat = prof.pop("_patterns")
    for i in range(5):
        _write_match(sub, i + 1, "🤖", prof, _make_rounds(actions, "🤖"))
    patterns_dir = sub / "patterns"
    patterns_dir.mkdir()
    if pat:
        (patterns_dir / "🤖.json").write_text(json.dumps(pat))
    result = profile_bot("🤖", str(sub / "results"), str(patterns_dir))
    return set(result["traits"])


class TestTraitCoverage:
    def test_at_least_10_distinct_traits_possible(self, tmp_path):
        """Across different bot profiles, at least 10 distinct traits should emerge."""
        all_traits: set[str] = set()
        for pidx, prof in enumerate(_COVERAGE_PROFILES):
            all_traits.update(_profile_from_spec(tmp_path, pidx, prof))
        assert len(all_traits) >= 10, f"Only {len(all_traits)} traits: {all_traits}"


# ── Callback usage trait ───────────────────────────────────────────


class TestCallbackTrait:
    def test_tactical_user_trait(self, tmp_path):
        for i in range(5):
            stats = {
                "kills": 2, "damage_dealt": 70, "damage_taken": 30,
                "rounds_survived": 15, "score": 60, "momentum_tier": 2,
                "archetype": "Bruiser",
                "equipment": {"weapon": "sword", "armor": "leather",
                              "accessories": [], "tactical": "battle_cry"},
            }
            actions = ["battle_cry"] * 5 + ["attack east"] * 10
            rounds = _make_rounds(actions, "🤖")
            _write_match(tmp_path, i + 1, "🤖", stats, rounds)

        result = profile_bot("🤖", str(tmp_path / "results"), str(tmp_path / "p"))
        traits_lower = [t.lower() for t in result["traits"]]
        assert any("tactical" in t or "battle" in t or "cry" in t for t in traits_lower)


# ── Equipment preference trait ─────────────────────────────────────


class TestEquipmentTrait:
    def test_ranged_preference(self, tmp_path):
        for i in range(5):
            stats = {
                "kills": 2, "damage_dealt": 60, "damage_taken": 20,
                "rounds_survived": 20, "score": 55, "momentum_tier": 2,
                "archetype": "Controller",
                "equipment": {"weapon": "bow", "armor": "leather",
                              "accessories": ["compass"], "tactical": None},
            }
            actions = ["ranged_attack east"] * 12 + ["move north"] * 8
            rounds = _make_rounds(actions, "🤖")
            _write_match(tmp_path, i + 1, "🤖", stats, rounds)

        result = profile_bot("🤖", str(tmp_path / "results"), str(tmp_path / "p"))
        traits_lower = [t.lower() for t in result["traits"]]
        assert any("ranged" in t or "sniper" in t or "archer" in t for t in traits_lower)
