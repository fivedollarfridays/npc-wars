"""Tests for kill bounty energy reward."""

from engine.combat import KILL_BOUNTY_ENERGY, MAX_ENERGY
from tests.conftest import make_bot


class TestKillBountyConstant:
    def test_kill_bounty_is_30(self):
        assert KILL_BOUNTY_ENERGY == 30


class TestKillBountyInAttributeKills:
    def test_combat_kill_awards_energy(self):
        """Killer bot receives +30 energy on combat kill."""
        from engine.rounds import attribute_kills

        killer = make_bot(emoji="K", energy=50)
        victim = make_bot(emoji="V", hp=0)
        victim.alive = False
        bots = [killer, victim]

        elims = [{"emoji": "V", "round": 5}]
        events = [{"type": "hit", "attacker": "K", "target": "V",
                   "damage": 25, "hp_before": 20}]

        attribute_kills(elims, events, bots, round_num=5)
        assert killer.energy == 50 + KILL_BOUNTY_ENERGY  # 80
        assert killer.kills == 1

    def test_storm_kill_no_bounty(self):
        """Storm kills do NOT award energy bounty."""
        from engine.rounds import attribute_kills

        victim = make_bot(emoji="V", hp=0)
        victim.alive = False
        bots = [victim]

        elims = [{"emoji": "V", "round": 5}]
        events = [{"type": "storm_damage", "target": "V", "damage": 10}]

        attribute_kills(elims, events, bots, round_num=5)
        # No killer bot to receive bounty — just verify no crash

    def test_energy_capped_at_max(self):
        """Kill bounty doesn't exceed MAX_ENERGY."""
        from engine.rounds import attribute_kills

        killer = make_bot(emoji="K", energy=90)
        victim = make_bot(emoji="V", hp=0)
        victim.alive = False
        bots = [killer, victim]

        elims = [{"emoji": "V", "round": 5}]
        events = [{"type": "hit", "attacker": "K", "target": "V",
                   "damage": 25, "hp_before": 20}]

        attribute_kills(elims, events, bots, round_num=5)
        assert killer.energy == MAX_ENERGY  # 100, not 120

    def test_bounty_on_unknown_killer_no_crash(self):
        """'unknown' killer does not receive bounty and does not crash."""
        from engine.rounds import attribute_kills

        victim = make_bot(emoji="V", hp=0)
        victim.alive = False
        bots = [victim]

        elims = [{"emoji": "V", "round": 5}]
        events = []  # no events -> killer is "unknown"

        attribute_kills(elims, events, bots, round_num=5)
        # Should not crash, no bounty awarded
