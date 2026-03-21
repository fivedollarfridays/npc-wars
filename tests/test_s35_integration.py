"""S35 Integration Gate — equipment system end-to-end tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from engine.combat import Bot
from engine.equipment import (
    EQUIPMENT_CATALOG,
    EQUIPMENT_DEFAULTS,
    compute_equipment_bonuses,
    validate_equipment,
)
from engine.game import run_match


def _bot(emoji: str = "🤖", x: int = 3, y: int = 3, **kw: Any) -> Bot:
    return Bot(
        name="Test", emoji=emoji, bio="test", author="test",
        decide_func=kw.pop("decide_func", lambda s: ("rest",)),
        x=x, y=y, **kw,
    )


class TestEquipmentValidation:
    def test_default_valid(self) -> None:
        ok, msg = validate_equipment(EQUIPMENT_DEFAULTS)
        assert ok, msg

    def test_over_budget_rejected(self) -> None:
        loadout = {"weapon": "axe", "armor": "plate",
                   "accessories": ["cloak_of_shadows", "boots_of_speed"],
                   "tactical": "overdrive"}
        ok, _ = validate_equipment(loadout)
        assert not ok

    def test_missing_weapon_rejected(self) -> None:
        ok, _ = validate_equipment({"armor": "leather", "accessories": []})
        assert not ok

    def test_three_accessories_rejected(self) -> None:
        ok, _ = validate_equipment({
            "weapon": "dagger", "armor": "leather",
            "accessories": ["ring_of_health", "ring_of_haste", "compass"],
        })
        assert not ok

    def test_full_valid_loadout(self) -> None:
        loadout = {"weapon": "mace", "armor": "plate",
                   "accessories": ["ring_of_health", "charm_of_evasion"],
                   "tactical": None}
        ok, msg = validate_equipment(loadout)
        assert ok, msg


class TestCombatWithEquipment:
    def test_sword_bonuses_in_match(self) -> None:
        """Sword-equipped bot should have to_hit and damage bonuses."""
        bonuses = compute_equipment_bonuses(EQUIPMENT_DEFAULTS)
        assert bonuses.to_hit == 1  # sword
        assert bonuses.min_damage == 3
        assert bonuses.max_damage == 5
        assert bonuses.dr == 2  # leather

    def test_axe_crit_bonus(self) -> None:
        bonuses = compute_equipment_bonuses({
            "weapon": "axe", "armor": "leather", "accessories": [],
        })
        assert bonuses.crit_mult == 0.2

    def test_mace_armor_pierce(self) -> None:
        bonuses = compute_equipment_bonuses({
            "weapon": "mace", "armor": "leather", "accessories": [],
        })
        assert bonuses.armor_pierce == 4

    def test_spear_reach(self) -> None:
        bonuses = compute_equipment_bonuses({
            "weapon": "spear", "armor": "leather", "accessories": [],
        })
        assert bonuses.reach_distance == 2


class TestEquipmentInMatch:
    def test_match_with_equipped_bots(self) -> None:
        """Real match with equipped bots runs without error."""
        configs = [
            {"name": "Knight", "emoji": "K", "bio": "tank",
             "decide_func": lambda s: ("attack", "east"),
             "equipment": {"weapon": "mace", "armor": "plate",
                          "accessories": ["ring_of_health"], "tactical": None}},
            {"name": "Rogue", "emoji": "R", "bio": "fast",
             "decide_func": lambda s: ("attack", "west"),
             "equipment": {"weapon": "dagger", "armor": "leather",
                          "accessories": ["boots_of_speed"], "tactical": None}},
        ]
        result = run_match(configs, match_id=1, seed=42)
        assert "winner" in result
        assert len(result["rounds"]) > 0

    def test_default_equipment_match(self) -> None:
        """Bots without equipment get defaults and match runs."""
        configs = [
            {"name": "A", "emoji": "A", "bio": "a",
             "decide_func": lambda s: ("rest",)},
            {"name": "B", "emoji": "B", "bio": "b",
             "decide_func": lambda s: ("rest",)},
        ]
        result = run_match(configs, match_id=1, seed=42)
        assert "winner" in result


class TestStateDict:
    def test_self_dict_has_equipment(self) -> None:
        bot = _bot()
        bot.equipment = EQUIPMENT_DEFAULTS
        bot.equipment_bonuses = compute_equipment_bonuses(EQUIPMENT_DEFAULTS)
        d = bot.to_self_dict()
        assert "equipment" in d
        assert d["equipment"]["weapon"] == "sword"
        assert "equipment_bonuses" in d
        assert d["equipment_bonuses"]["to_hit"] == 1

    def test_enemy_dict_shows_weapon_armor(self) -> None:
        bot = _bot()
        bot.equipment = {"weapon": "axe", "armor": "plate", "accessories": []}
        d = bot.to_enemy_dict()
        assert d["weapon"] == "axe"
        assert d["armor"] == "plate"
        assert "accessories" not in d  # hidden
        assert "equipment_bonuses" not in d  # hidden

    def test_enemy_dict_hides_accessories(self) -> None:
        bot = _bot()
        bot.equipment = {"weapon": "sword", "armor": "leather",
                        "accessories": ["ring_of_health"]}
        d = bot.to_enemy_dict()
        assert "accessories" not in d


class TestBotLoading:
    def test_builtin_bots_load_with_equipment(self) -> None:
        from engine.loader import load_bots
        bots_dir = str(Path(__file__).resolve().parent.parent / "bots")
        configs = load_bots(bots_dir)
        for cfg in configs:
            assert "equipment" in cfg, f"{cfg['name']} missing equipment"
            ok, msg = validate_equipment(cfg["equipment"])
            assert ok, f"{cfg['name']} invalid equipment: {msg}"


class TestNoDeadCode:
    def test_equipment_module_exports(self) -> None:
        import engine.equipment as mod
        for name in mod.__all__:
            assert getattr(mod, name) is not None

    def test_catalog_complete(self) -> None:
        total = sum(len(items) for items in EQUIPMENT_CATALOG.values())
        assert total == 23, f"Expected 23 items, got {total}"

    def test_all_slots_have_items(self) -> None:
        for slot in ("weapon", "armor", "accessory", "tactical"):
            assert slot in EQUIPMENT_CATALOG
            assert len(EQUIPMENT_CATALOG[slot]) >= 3
