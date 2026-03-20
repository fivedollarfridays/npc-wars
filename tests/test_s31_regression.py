"""S31 regression: 25/25/25/25 default bots produce reasonable gameplay."""

from engine.game import run_match
from engine.stats import DEFAULT_ALLOCATION, calculate_derived


def _run_default_matches(n: int = 20, seed_base: int = 5000):
    """Run n matches with 4 default-stat bots, collect stats."""
    hits, misses, crits, rounds_list = [], [], [], []
    for i in range(n):
        configs = [
            {"name": f"Bot{j}", "emoji": f"B{j}", "bio": "", "author": "",
             "decide_func": lambda s: ("attack", "north") if s["enemies"] else ("rest",)}
            for j in range(4)
        ]
        data = run_match(configs, match_id=1, seed=seed_base + i)
        rounds_list.append(len(data["rounds"]))
        for rnd in data["rounds"]:
            for evt in rnd.get("events", []):
                if evt.get("type") == "hit":
                    hits.append(evt.get("damage", 0))
                    if evt.get("is_crit"):
                        crits.append(1)
                elif evt.get("type") == "attack_miss":
                    misses.append(1)
    return hits, misses, crits, rounds_list


class TestDefaultBaseline:
    """Verify default 25/25/25/25 bots produce expected gameplay ranges."""

    def test_derived_defaults_unchanged(self):
        d = calculate_derived(DEFAULT_ALLOCATION)
        assert d.max_hp == 145
        assert d.max_energy == 100
        assert d.min_damage == 35
        assert d.max_damage == 55
        assert d.damage_reduction == 0
        assert d.energy_regen == 0

    def test_match_length_reasonable(self):
        _, _, _, rounds_list = _run_default_matches(10)
        avg = sum(rounds_list) / len(rounds_list)
        assert 10 <= avg <= 80, f"Avg match length {avg} outside [10, 80]"

    def test_avg_damage_per_hit(self):
        hits, _, _, _ = _run_default_matches(10)
        if hits:
            avg = sum(hits) / len(hits)
            assert 10 <= avg <= 50, f"Avg damage per hit {avg} outside [10, 50]"

    def test_miss_rate(self):
        hits, misses, _, _ = _run_default_matches(10)
        total_attacks = len(hits) + len(misses)
        if total_attacks > 0:
            miss_rate = len(misses) / total_attacks * 100
            assert 5 <= miss_rate <= 50, f"Miss rate {miss_rate}% outside [5, 50]"

    def test_crit_rate(self):
        hits, _, crits, _ = _run_default_matches(10)
        if hits:
            crit_rate = len(crits) / len(hits) * 100
            assert 0 <= crit_rate <= 25, f"Crit rate {crit_rate}% outside [0, 25]"

    def test_matches_complete(self):
        _, _, _, rounds_list = _run_default_matches(5)
        assert all(r > 0 for r in rounds_list), "Some matches had 0 rounds"
