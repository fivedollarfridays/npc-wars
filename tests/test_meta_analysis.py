"""Tests for data/meta_analysis.py — meta report generation."""

import json

from data.meta_analysis import generate_meta_report


# --- Helpers ---


def _make_match(
    winner, players, stats, eliminations, match_id=1,
):
    """Build a minimal match dict with equipment data."""
    return {
        "match_id": match_id,
        "date": "2026-01-01T00:00:00+00:00",
        "grid_size": 10,
        "players": [{"emoji": e, "name": e, "bio": "", "author": "t"} for e in players],
        "rounds": [],
        "eliminations": eliminations,
        "winner": winner,
        "stats": stats,
        "duration_rounds": 10,
    }


def _player_stats(weapon="sword", armor="leather", accessories=None, archetype="Balanced"):
    """Build a stats entry with equipment."""
    return {
        "kills": 1, "damage_dealt": 50, "damage_taken": 30, "rounds_survived": 10,
        "archetype": archetype,
        "equipment": {
            "weapon": weapon, "armor": armor,
            "accessories": accessories or [], "tactical": None,
        },
    }


def _write_matches(tmp_path, matches):
    """Write match dicts as JSON files and return the directory."""
    for m in matches:
        path = tmp_path / f"match_{m['match_id']:03d}.json"
        path.write_text(json.dumps(m))
    return str(tmp_path)


def _make_simple_matches(tmp_path, configs):
    """Create matches from simple config tuples.

    Each config: (match_id, winner_emoji, loser_emoji, winner_weapon, winner_armor,
                  loser_weapon, loser_armor, winner_archetype, loser_archetype)
    """
    matches = []
    for cfg in configs:
        mid, w, lo, ww, wa, lw, la, w_arch, l_arch = cfg
        matches.append(_make_match(
            winner=w, players=[w, lo],
            stats={
                w: _player_stats(weapon=ww, armor=wa, archetype=w_arch),
                lo: _player_stats(weapon=lw, armor=la, archetype=l_arch),
            },
            eliminations=[{"emoji": lo, "round": 8, "killed_by": w, "cause": "combat"}],
            match_id=mid,
        ))
    return _write_matches(tmp_path, matches)


# --- generate_meta_report ---


class TestGenerateMetaReport:
    def test_returns_dict(self, tmp_path):
        results_dir = _make_simple_matches(tmp_path, [
            (1, "A", "B", "sword", "leather", "axe", "plate", "Balanced", "Tank"),
        ])
        report = generate_meta_report(results_dir)
        assert isinstance(report, dict)

    def test_weapon_win_rates(self, tmp_path):
        results_dir = _make_simple_matches(tmp_path, [
            (1, "A", "B", "sword", "leather", "axe", "plate", "Balanced", "Tank"),
            (2, "A", "B", "sword", "leather", "axe", "plate", "Balanced", "Tank"),
            (3, "B", "A", "axe", "plate", "sword", "leather", "Tank", "Balanced"),
        ])
        report = generate_meta_report(results_dir)
        weapons = report["weapon_win_rates"]
        # sword: 2 wins out of 3 appearances as winner or loser
        assert weapons["sword"]["wins"] == 2
        assert weapons["sword"]["matches"] == 3
        assert weapons["axe"]["wins"] == 1

    def test_armor_win_rates(self, tmp_path):
        results_dir = _make_simple_matches(tmp_path, [
            (1, "A", "B", "sword", "chain_mail", "axe", "leather", "Balanced", "Tank"),
            (2, "A", "B", "sword", "chain_mail", "axe", "leather", "Balanced", "Tank"),
        ])
        report = generate_meta_report(results_dir)
        armor = report["armor_win_rates"]
        assert armor["chain_mail"]["wins"] == 2
        assert armor["chain_mail"]["matches"] == 2
        assert armor["leather"]["wins"] == 0

    def test_accessory_win_rates(self, tmp_path):
        matches = [_make_match(
            winner="A", players=["A", "B"],
            stats={
                "A": _player_stats(accessories=["boots_of_speed", "ring_of_health"]),
                "B": _player_stats(accessories=["amulet_of_crit"]),
            },
            eliminations=[{"emoji": "B", "round": 8, "killed_by": "A", "cause": "combat"}],
            match_id=1,
        )]
        results_dir = _write_matches(tmp_path, matches)
        report = generate_meta_report(results_dir)
        acc = report["accessory_win_rates"]
        assert acc["boots_of_speed"]["wins"] == 1
        assert acc["amulet_of_crit"]["wins"] == 0

    def test_dominant_strategies(self, tmp_path):
        """Weapon with >60% win rate and >=5 matches is dominant."""
        configs = []
        for i in range(1, 8):
            # sword wins 6 out of 7
            if i <= 6:
                configs.append((i, "A", "B", "sword", "leather", "axe", "plate", "Balanced", "Tank"))
            else:
                configs.append((i, "B", "A", "axe", "plate", "sword", "leather", "Tank", "Balanced"))
        results_dir = _make_simple_matches(tmp_path, configs)
        report = generate_meta_report(results_dir)
        dominant = report["dominant_strategies"]
        weapon_names = [d["name"] for d in dominant if d["category"] == "weapon"]
        assert "sword" in weapon_names

    def test_no_dominant_below_threshold(self, tmp_path):
        """Weapon with <5 matches should not be dominant."""
        configs = [
            (1, "A", "B", "sword", "leather", "axe", "plate", "Balanced", "Tank"),
            (2, "A", "B", "sword", "leather", "axe", "plate", "Balanced", "Tank"),
        ]
        results_dir = _make_simple_matches(tmp_path, configs)
        report = generate_meta_report(results_dir)
        dominant = report["dominant_strategies"]
        assert len(dominant) == 0

    def test_archetype_win_rates(self, tmp_path):
        results_dir = _make_simple_matches(tmp_path, [
            (1, "A", "B", "sword", "leather", "axe", "plate", "Assassin", "Tank"),
            (2, "A", "B", "sword", "leather", "axe", "plate", "Assassin", "Tank"),
            (3, "B", "A", "axe", "plate", "sword", "leather", "Tank", "Assassin"),
        ])
        report = generate_meta_report(results_dir)
        arch = report["archetype_win_rates"]
        assert arch["Assassin"]["wins"] == 2
        assert arch["Assassin"]["matches"] == 3
        assert arch["Tank"]["wins"] == 1

    def test_top_builds(self, tmp_path):
        configs = []
        for i in range(1, 8):
            configs.append((i, "A", "B", "sword", "chain_mail", "axe", "plate", "Balanced", "Tank"))
        results_dir = _make_simple_matches(tmp_path, configs)
        report = generate_meta_report(results_dir)
        top = report["top_builds"]
        assert len(top) <= 5
        assert top[0]["wins"] >= top[-1]["wins"]

    def test_counter_picks(self, tmp_path):
        """Counter picks: builds that beat dominant strategies."""
        configs = []
        # sword dominates
        for i in range(1, 7):
            configs.append((i, "A", "B", "sword", "leather", "axe", "plate", "Balanced", "Tank"))
        # mace beats sword
        configs.append((7, "B", "A", "mace", "chain_mail", "sword", "leather", "Tank", "Balanced"))
        configs.append((8, "B", "A", "mace", "chain_mail", "sword", "leather", "Tank", "Balanced"))
        results_dir = _make_simple_matches(tmp_path, configs)
        report = generate_meta_report(results_dir)
        counters = report["counter_picks"]
        assert len(counters) <= 3

    def test_meta_trend(self, tmp_path):
        results_dir = _make_simple_matches(tmp_path, [
            (1, "A", "B", "sword", "leather", "axe", "plate", "Balanced", "Tank"),
        ])
        report = generate_meta_report(results_dir)
        assert "meta_trend" in report

    def test_empty_results_dir(self, tmp_path):
        report = generate_meta_report(str(tmp_path))
        assert report["top_builds"] == []
        assert report["dominant_strategies"] == []
        assert report["counter_picks"] == []

    def test_single_match(self, tmp_path):
        results_dir = _make_simple_matches(tmp_path, [
            (1, "A", "B", "sword", "leather", "axe", "plate", "Balanced", "Tank"),
        ])
        report = generate_meta_report(results_dir)
        assert report["weapon_win_rates"]["sword"]["wins"] == 1

    def test_all_same_loadout(self, tmp_path):
        configs = []
        for i in range(1, 6):
            w, lo = ("A", "B") if i % 2 else ("B", "A")
            configs.append((i, w, lo, "sword", "leather", "sword", "leather", "Balanced", "Balanced"))
        results_dir = _make_simple_matches(tmp_path, configs)
        report = generate_meta_report(results_dir)
        # 5 matches × 2 players each = 10 entries, all using sword
        assert report["weapon_win_rates"]["sword"]["matches"] == 10
        # Mirror matches → 50% win rate, can't be dominant
        dominant_weapons = [d for d in report["dominant_strategies"] if d["category"] == "weapon"]
        assert len(dominant_weapons) == 0

    def test_matches_without_equipment_skipped(self, tmp_path):
        """Old matches without equipment data are gracefully handled."""
        matches = [_make_match(
            winner="A", players=["A", "B"],
            stats={
                "A": {"kills": 1, "damage_dealt": 50, "damage_taken": 30, "rounds_survived": 10},
                "B": {"kills": 0, "damage_dealt": 30, "damage_taken": 50, "rounds_survived": 5},
            },
            eliminations=[{"emoji": "B", "round": 8, "killed_by": "A", "cause": "combat"}],
            match_id=1,
        )]
        results_dir = _write_matches(tmp_path, matches)
        report = generate_meta_report(results_dir)
        assert report["top_builds"] == []
