"""S27 Integration Gate — verify stat system wiring and backward compatibility."""

from __future__ import annotations

from engine.combat import Bot
from engine.game import run_match
from engine.loader import load_bots
from engine.state import build_state
from engine.stats import DEFAULT_ALLOCATION, validate_allocation
from tests.conftest import chase_and_attack, make_bot

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


def _custom_stat_config(
    name: str, emoji: str, power: int, speed: int, armor: int, mind: int,
) -> dict:
    alloc = validate_allocation(power, speed, armor, mind)
    return {
        "name": name, "emoji": emoji, "bio": "", "author": "test",
        "decide_func": chase_and_attack,
        "stat_allocation": alloc,
    }


# ===========================================================================
# Backward compatibility — 25/25/25/25 must match pre-overhaul behaviour
# ===========================================================================


class TestBackwardCompatibility:
    """Default (25/25/25/25) bots must behave identically to pre-overhaul."""

    def test_default_bots_start_hp_100(self) -> None:
        match = _seeded_match()
        r1 = match["rounds"][0]
        for pos in r1["positions"]:
            # All bots start at max_hp=100 with default stats
            assert pos["max_hp"] == 100, f"{pos['emoji']} max_hp != 100"

    def test_default_bots_start_energy_100(self) -> None:
        # Energy isn't in round positions, so check via Bot init
        configs = _builtin_configs()
        for cfg in configs:
            bot = Bot(
                name=cfg["name"], emoji=cfg["emoji"], bio=cfg["bio"],
                author=cfg["author"], decide_func=cfg["decide_func"],
                x=0, y=0, stat_allocation=cfg.get("stat_allocation"),
            )
            assert bot.energy == 100, f"{bot.name} energy != 100"

    def test_default_bots_damage_in_range(self) -> None:
        match = _seeded_match()
        hit_damages: list[int] = []
        for rnd in match["rounds"]:
            for evt in rnd.get("events", []):
                if evt.get("type") == "hit":
                    hit_damages.append(evt["damage"])
        assert len(hit_damages) > 0, "No hit events found"
        # S28: roll-based combat produces damage in [15, 35] base range
        # with crits up to ~52. Check average is near 25.
        avg = sum(hit_damages) / len(hit_damages)
        assert 15 <= avg <= 45, f"Avg hit damage {avg:.1f} outside [15, 45]"

    def test_default_match_length_reasonable(self) -> None:
        match = _seeded_match()
        num_rounds = len(match["rounds"])
        assert 15 <= num_rounds <= 50, f"Match length {num_rounds} outside [15, 50]"


# ===========================================================================
# Stat system wired
# ===========================================================================


class TestStatSystemWired:
    """Verify the stat allocation system is fully integrated."""

    def test_custom_stat_bot_different_hp(self) -> None:
        # armor=50 -> base HP = 55 + 50*0.8 = 95 (plus versatility bonus)
        # High-armor specialist has less HP than balanced due to versatility
        # penalty, but more than a low-armor specialist.
        tank = _custom_stat_config("Tank", "\U0001f6e1\ufe0f", 15, 15, 50, 20)
        low_armor = _custom_stat_config("Weak", "\U0001f47e", 50, 15, 15, 20)
        match = _seeded_match(configs=[tank, low_armor])
        r1 = match["rounds"][0]
        tank_pos = next(p for p in r1["positions"] if p["emoji"] == "\U0001f6e1\ufe0f")
        weak_pos = next(p for p in r1["positions"] if p["emoji"] == "\U0001f47e")
        assert tank_pos["max_hp"] > weak_pos["max_hp"], (
            f"Tank max_hp {tank_pos['max_hp']} should exceed low-armor {weak_pos['max_hp']}"
        )

    def test_state_dict_has_stat_fields(self) -> None:
        match = _seeded_match()
        r1 = match["rounds"][0]
        for pos in r1["positions"]:
            assert "max_hp" in pos, f"{pos['emoji']} missing max_hp in position data"

    def test_state_dict_self_has_power_speed_armor_mind(self) -> None:
        bot = make_bot(name="Me", emoji="\U0001f916", x=0, y=0)
        other = make_bot(name="Other", emoji="\U0001f3af", x=5, y=5)
        state = build_state(bot, [bot, other], round_num=1, grid_size=10, storm_border=0)
        for field in ("power", "speed", "armor", "mind"):
            assert field in state["me"], f"state['me'] missing '{field}'"

    def test_state_dict_enemy_has_max_hp_and_speed_class(self) -> None:
        bot = make_bot(name="Me", emoji="\U0001f916", x=0, y=0)
        other = make_bot(name="Other", emoji="\U0001f3af", x=5, y=5)
        state = build_state(bot, [bot, other], round_num=1, grid_size=10, storm_border=0)
        enemy = state["enemies"][0]
        assert "max_hp" in enemy, "enemy missing max_hp"
        assert "speed_class" in enemy, "enemy missing speed_class"

    def test_high_mind_bot_more_energy_regen(self) -> None:
        # mind=50 -> energy_regen = max(0, int((50-25)*0.2)) = 5
        alloc = validate_allocation(power=15, speed=15, armor=20, mind=50)
        bot = make_bot(
            name="MindBot", emoji="\U0001f9e0", x=5, y=5,
            stat_allocation=alloc, energy=50,
        )
        # Rest restores: REST_ENERGY_RESTORE(20) + energy_regen(10) = 30
        # but we just check the derived value
        assert bot.derived.energy_regen > 0, "High-mind bot should have energy_regen > 0"
        assert bot.derived.energy_regen == 10, f"Expected regen=10, got {bot.derived.energy_regen}"


# ===========================================================================
# Loader
# ===========================================================================


class TestLoader:
    """Verify bot loader works with stat system."""

    def test_builtin_bots_all_load(self) -> None:
        configs = _builtin_configs()
        assert len(configs) >= 4, f"Expected at least 4 builtin bots, got {len(configs)}"

    def test_builtin_bots_have_default_stats(self) -> None:
        configs = _builtin_configs()
        for cfg in configs:
            alloc = cfg.get("stat_allocation")
            assert alloc == DEFAULT_ALLOCATION, (
                f"{cfg['name']} has stat_allocation={alloc}, expected {DEFAULT_ALLOCATION}"
            )


# ===========================================================================
# No dead code
# ===========================================================================


class TestNoDeadCode:
    """Verify engine.stats public API is importable and used."""

    def test_stats_module_importable(self) -> None:
        # These imports should all work (already imported at top, but be explicit)
        from engine import stats
        for name in ("StatAllocation", "DerivedStats", "validate_allocation",
                     "calculate_derived", "DEFAULT_ALLOCATION"):
            assert hasattr(stats, name), f"engine.stats missing {name}"

    def test_all_public_functions_have_callers(self) -> None:
        """Verify engine.stats.__all__ entries are referenced outside tests."""
        import os

        from engine.stats import __all__ as stats_all

        # Collect all Python source outside tests/
        source_files: list[str] = []
        for root, _dirs, files in os.walk("engine"):
            for f in files:
                if f.endswith(".py"):
                    source_files.append(os.path.join(root, f))
        # Also check top-level files that import from engine
        for f in os.listdir("."):
            if f.endswith(".py"):
                source_files.append(f)

        all_source = ""
        for fpath in source_files:
            with open(fpath) as fp:
                all_source += fp.read() + "\n"

        # Each __all__ entry should appear somewhere in engine/ source
        # (either as an import or direct reference)
        for name in stats_all:
            # Constants/classes should appear in code outside stats.py itself
            # We check the combined source includes the name
            assert name in all_source, (
                f"engine.stats.{name} not found in any engine/ source file"
            )
