"""S36 Integration Gate — tactical + ability + evolve pipeline end-to-end."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from engine.abilities import AbilityDef, validate_ability
from engine.callbacks import CallbackSet, discover_callbacks
from engine.combat import Bot
from engine.game import run_match
from engine.tactical import resolve_tactical_activation


def _bot(emoji: str = "🤖", x: int = 3, y: int = 3, **kw: Any) -> Bot:
    return Bot(
        name="Test", emoji=emoji, bio="test", author="test",
        decide_func=kw.pop("decide_func", lambda s: ("rest",)),
        x=x, y=y, **kw,
    )


class TestTacticalInMatch:
    def test_battle_cry_activates(self) -> None:
        bot = _bot()
        bot.equipment = {"weapon": "sword", "armor": "leather",
                        "accessories": [], "tactical": "battle_cry"}
        bot.energy = 50
        events = resolve_tactical_activation(bot, round_num=1)
        assert len(events) == 1
        assert events[0]["tactical"] == "battle_cry"
        assert bot.tactical_damage_mult == 1.5

    def test_cooldown_blocks(self) -> None:
        bot = _bot()
        bot.equipment = {"tactical": "battle_cry"}
        bot.energy = 50
        resolve_tactical_activation(bot, round_num=1)
        events2 = resolve_tactical_activation(bot, round_num=2)
        assert events2 == []


class TestAbilityInMatch:
    def test_ability_validation(self) -> None:
        defn = {"name": "Bolt", "type": "damage", "potency": 25,
                "range": 2, "cooldown": 4, "energy_cost": 20}
        result = validate_ability(defn)
        assert result is not None
        assert isinstance(result, AbilityDef)

    def test_invalid_ability_rejected(self) -> None:
        defn = {"name": "Bad", "type": "nuke", "potency": 100,
                "range": 10, "cooldown": 0, "energy_cost": 5}
        result = validate_ability(defn)
        assert result is None

    def test_ability_in_real_match(self) -> None:
        """Match with ability-using bot runs without crash."""
        def mage_decide(state: dict[str, Any]) -> tuple[str, ...]:
            me = state["me"]
            ability = me.get("ability")
            if ability and ability.get("cooldown_remaining", 1) == 0:
                return ("use_ability", "east")
            return ("rest",)

        def power_up_fn(state: dict[str, Any]) -> dict[str, Any]:
            return {"name": "Bolt", "type": "damage", "potency": 20,
                    "range": 2, "cooldown": 3, "energy_cost": 15}

        import types
        mod = types.ModuleType("test_mage")
        mod.decide = mage_decide
        mod.power_up = power_up_fn

        configs = [
            {"name": "Mage", "emoji": "M", "bio": "mage",
             "decide_func": mage_decide, "module": mod,
             "unlocked_actions": sorted(["move", "attack", "rest", "defend", "use_ability"]),
             "unlocked_callbacks": {"setup", "on_kill", "react", "power_up", "evolve"}},
            {"name": "Fighter", "emoji": "F", "bio": "fights",
             "decide_func": lambda s: ("attack", "west")},
        ]
        result = run_match(configs, match_id=1, seed=42)
        assert "winner" in result


class TestEvolveInMatch:
    def test_evolve_in_callbacks(self) -> None:
        """CallbackSet has evolve field."""
        cs = CallbackSet(evolve=lambda s: None)
        assert cs.evolve is not None

    def test_evolve_discovery(self) -> None:
        import types
        mod = types.ModuleType("test_bot")
        mod.evolve = lambda s: {"ability_boost": 5}
        cs = discover_callbacks(mod, {"evolve"})
        assert cs.evolve is not None


class TestFeedRendering:
    def test_tactical_formatter_registered(self) -> None:
        from agentgrounds.wars.cli.feed import _FORMATTERS
        assert "tactical_activate" in _FORMATTERS

    def test_ability_formatters_registered(self) -> None:
        from agentgrounds.wars.cli.feed import _FORMATTERS
        for event_type in ("ability_damage", "ability_heal", "ability_shield", "ability_slow"):
            assert event_type in _FORMATTERS, f"Missing formatter for {event_type}"

    def test_evolve_formatter_registered(self) -> None:
        from agentgrounds.wars.cli.feed import _FORMATTERS
        assert "evolve" in _FORMATTERS


class TestStateDict:
    def test_self_dict_has_ability(self) -> None:
        bot = _bot()
        d = bot.to_self_dict()
        assert "ability" in d

    def test_enemy_dict_has_ability_flag(self) -> None:
        bot = _bot()
        d = bot.to_enemy_dict()
        assert "has_ability" in d

    def test_self_dict_has_tactical_cooldown(self) -> None:
        bot = _bot()
        d = bot.to_self_dict()
        assert "tactical_cooldown" in d


class TestCallbackWiringInLoader:
    def test_module_stored_in_config(self) -> None:
        """Loader stores module reference for callback discovery."""
        from engine.loader import load_bots
        bots_dir = str(Path(__file__).resolve().parent.parent / "bots")
        configs = load_bots(bots_dir)
        for cfg in configs:
            assert "module" in cfg, f"{cfg['name']} missing module ref"

    def test_mage_has_callbacks_in_match(self) -> None:
        """Mage bot's power_up callback is discovered during match setup."""
        import types
        mod = types.ModuleType("test_mage")
        mod.decide = lambda s: ("rest",)
        mod.power_up = lambda s: {"name": "X", "type": "heal", "potency": 10,
                                   "range": 0, "cooldown": 3, "energy_cost": 15}
        cs = discover_callbacks(mod, {"power_up"})
        assert cs.power_up is not None


class TestNoDeadCode:
    def test_tactical_module_exports(self) -> None:
        import engine.tactical as mod
        for name in mod.__all__:
            assert getattr(mod, name) is not None

    def test_abilities_module_exports(self) -> None:
        import engine.abilities as mod
        for name in mod.__all__:
            assert getattr(mod, name) is not None

    def test_discover_callbacks_used_in_game(self) -> None:
        source = Path("engine/game.py").read_text()
        assert "discover_callbacks" in source

    def test_run_power_up_used_in_game(self) -> None:
        source = Path("engine/game.py").read_text()
        assert "run_power_up_callbacks" in source
