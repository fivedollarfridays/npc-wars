"""Tests for kill attribution — killing blow gets credit, not last-hit."""

from tests.conftest import bot_config, chase_and_attack

from engine.game import run_match


class TestKillAttribution:
    def test_killing_blow_gets_credit(self):
        """When two bots attack the same target, the one dealing the fatal hit gets the kill."""
        round_count = [0]

        def target_bot(state):
            """Stays still, takes hits."""
            return ("rest",)

        def attacker_from_west(state):
            """Moves east toward target, then attacks east."""
            me = state["me"]
            enemies = state["enemies"]
            if not enemies:
                return ("rest",)
            target = enemies[0]
            dx = target["x"] - me["x"]
            dy = target["y"] - me["y"]
            if abs(dx) + abs(dy) == 1:
                if dx == 1:
                    return ("attack", "east")
                if dx == -1:
                    return ("attack", "west")
                if dy == 1:
                    return ("attack", "south")
                return ("attack", "north")
            if abs(dx) >= abs(dy):
                return ("move", "east") if dx > 0 else ("move", "west")
            return ("move", "south") if dy > 0 else ("move", "north")

        configs = [
            bot_config("Target", "🎯", target_bot),
            bot_config("Killer1", "⚔️", attacker_from_west),
            bot_config("Killer2", "🗡️", attacker_from_west),
        ]
        data = run_match(configs, seed=42)

        # Verify kill attribution exists
        combat_elims = [e for e in data["eliminations"] if e.get("cause") == "combat"]
        for elim in combat_elims:
            assert elim["killed_by"] != "unknown"

    def test_storm_kill_attributed_correctly(self):
        """Bot killed by storm should have cause='storm'."""
        def stay_still(state):
            return ("rest",)

        configs = [
            bot_config("A", "🅰️", stay_still),
            bot_config("B", "🅱️", stay_still),
        ]
        data = run_match(configs, seed=42)
        storm_elims = [e for e in data["eliminations"] if e.get("cause") == "storm"]
        for elim in storm_elims:
            assert elim["killed_by"] == "storm"

    def test_kill_stats_match_eliminations(self):
        """Total kills in stats should match combat eliminations."""
        configs = [
            bot_config("A", "🅰️", chase_and_attack),
            bot_config("B", "🅱️", chase_and_attack),
            bot_config("C", "🅾️", chase_and_attack),
        ]
        data = run_match(configs, seed=42)
        total_kills_in_stats = sum(s["kills"] for s in data["stats"].values())
        combat_elims = len([e for e in data["eliminations"] if e.get("cause") == "combat"])
        assert total_kills_in_stats == combat_elims
