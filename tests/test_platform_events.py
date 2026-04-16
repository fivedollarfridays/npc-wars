"""Tests for platform event contract and adapters (T61.1)."""
from __future__ import annotations

from engine.platform_events import (
    EVENT_TYPES,
    GameEvent,
    adapt_circuit_events,
    adapt_killswitch_events,
)


class _FakeRaceEvent:
    """Minimal duck-type stand-in for npc-race RaceEvent."""
    __slots__ = ("type", "tick", "cars", "data")

    def __init__(self, event_type, tick, cars, data=None):
        self.type = event_type
        self.tick = tick
        self.cars = cars
        self.data = data or {}


# -- GameEvent dataclass -----------------------------------------------------


class TestGameEventShape:
    """GameEvent has required fields with correct types."""

    def test_required_fields(self):
        evt = GameEvent(
            type="kill", timestamp=3, participants=["A", "B"],
            data={"cause": "melee"}, drama_weight=4,
        )
        assert evt.type == "kill"
        assert evt.timestamp == 3
        assert evt.participants == ["A", "B"]
        assert evt.data == {"cause": "melee"}
        assert evt.drama_weight == 4

    def test_data_defaults_empty(self):
        evt = GameEvent(type="pit_stop", timestamp=100, participants=["car1"])
        assert evt.data == {}
        assert evt.drama_weight == 0

    def test_drama_weight_is_numeric(self):
        evt = GameEvent(type="overtake", timestamp=1, participants=["a"])
        assert isinstance(evt.drama_weight, (int, float))


# -- Kill Switch adapter -----------------------------------------------------


def _ks_match(rounds=None, eliminations=None):
    """Minimal Kill Switch match_data fixture."""
    return {
        "rounds": rounds or [],
        "eliminations": eliminations or [],
        "players": [{"emoji": "A"}, {"emoji": "B"}],
        "duration_rounds": len(rounds) if rounds else 0,
    }


def _ks_round(rnum, events=None, positions=None):
    return {
        "round": rnum,
        "events": events or [],
        "positions": positions or [
            {"emoji": "A", "hp": 20, "alive": True},
            {"emoji": "B", "hp": 20, "alive": True},
        ],
    }


class TestKillSwitchAdapterEmpty:
    """Empty match produces no events."""

    def test_no_rounds(self):
        result = adapt_killswitch_events(_ks_match())
        assert result == []

    def test_calm_round(self):
        md = _ks_match([_ks_round(1)])
        result = adapt_killswitch_events(md)
        assert result == []


class TestKillSwitchAdapterKill:
    """Kill events mapped correctly."""

    def test_kill_event(self):
        events = [{"type": "kill", "attacker": "A", "victim": "B"}]
        md = _ks_match([_ks_round(1, events)])
        result = adapt_killswitch_events(md)
        kills = [e for e in result if e.type == "kill"]
        assert len(kills) == 1
        assert "A" in kills[0].participants
        assert "B" in kills[0].participants
        assert kills[0].drama_weight == 4
        assert kills[0].timestamp == 1

    def test_storm_kill(self):
        events = [{"type": "kill", "attacker": "storm", "victim": "A", "cause": "storm"}]
        md = _ks_match([_ks_round(2, events)])
        result = adapt_killswitch_events(md)
        kills = [e for e in result if e.type == "kill"]
        assert len(kills) == 1
        assert kills[0].data.get("cause") == "storm"


class TestKillSwitchAdapterCombat:
    """Combat events: hit, ability_damage."""

    def test_hit_event(self):
        events = [{"type": "hit", "attacker": "A", "target": "B", "damage": 5, "is_crit": True}]
        md = _ks_match([_ks_round(1, events)])
        result = adapt_killswitch_events(md)
        hits = [e for e in result if e.type == "hit"]
        assert len(hits) == 1
        assert hits[0].data["damage"] == 5
        assert hits[0].data["is_crit"] is True

    def test_ability_damage(self):
        events = [{"type": "ability_damage", "emoji": "A", "target": "B",
                    "ability": "fireball", "damage": 8}]
        md = _ks_match([_ks_round(1, events)])
        result = adapt_killswitch_events(md)
        abilities = [e for e in result if e.type == "ability_damage"]
        assert len(abilities) == 1


class TestKillSwitchAdapterWatcher:
    """Watcher events."""

    def test_watcher_spawn(self):
        events = [{"type": "watcher_spawn", "x": 3, "y": 4}]
        md = _ks_match([_ks_round(1, events)])
        result = adapt_killswitch_events(md)
        spawns = [e for e in result if e.type == "watcher_spawn"]
        assert len(spawns) == 1
        assert spawns[0].drama_weight == 5

    def test_watcher_kill(self):
        events = [{"type": "watcher_kill", "victim": "A"}]
        md = _ks_match([_ks_round(1, events)])
        result = adapt_killswitch_events(md)
        wk = [e for e in result if e.type == "watcher_kill"]
        assert len(wk) == 1
        assert wk[0].drama_weight == 4


class TestKillSwitchAdapterNearDeath:
    """Near-death detection from positions."""

    def test_near_death_from_positions(self):
        positions = [
            {"emoji": "A", "hp": 2, "alive": True},
            {"emoji": "B", "hp": 20, "alive": True},
        ]
        md = _ks_match([_ks_round(1, [], positions)])
        result = adapt_killswitch_events(md)
        nd = [e for e in result if e.type == "near_death"]
        assert len(nd) == 1
        assert "A" in nd[0].participants
        assert nd[0].drama_weight == 4


class TestKillSwitchAdapterTraps:
    """Trap events."""

    def test_trap_trigger(self):
        events = [{"type": "trap_trigger", "victim": "B", "owner": "A", "damage": 3}]
        md = _ks_match([_ks_round(1, events)])
        result = adapt_killswitch_events(md)
        traps = [e for e in result if e.type == "trap_trigger"]
        assert len(traps) == 1
        assert "A" in traps[0].participants


class TestKillSwitchMultiRound:
    """Multi-round match preserves ordering."""

    def test_timestamp_ordering(self):
        r1 = _ks_round(1, [{"type": "hit", "attacker": "A", "target": "B", "damage": 3}])
        r2 = _ks_round(2, [{"type": "kill", "attacker": "A", "victim": "B"}])
        md = _ks_match([r1, r2])
        result = adapt_killswitch_events(md)
        assert len(result) >= 2
        assert result[0].timestamp <= result[-1].timestamp


# -- Code Circuit adapter ----------------------------------------------------


def _cc_replay(frames=None, results=None):
    """Minimal Code Circuit replay fixture."""
    return {
        "track_name": "TestTrack",
        "laps": 5,
        "ticks_per_sec": 30,
        "frames": frames or [],
        "results": results or [],
    }


class TestCircuitAdapterEmpty:
    """Empty inputs produce no events."""

    def test_no_events(self):
        result = adapt_circuit_events(_cc_replay(), [])
        assert result == []


class TestCircuitAdapterOvertake:
    """Overtake events."""

    def test_overtake(self):
        events = [_FakeRaceEvent("OVERTAKE", 150, ["AlphaCar", "BetaCar"],
                            {"position": 2, "lap": 3})]
        result = adapt_circuit_events(_cc_replay(), events)
        ot = [e for e in result if e.type == "overtake"]
        assert len(ot) == 1
        assert "AlphaCar" in ot[0].participants
        assert ot[0].drama_weight == 3
        assert ot[0].data["position"] == 2


class TestCircuitAdapterBattle:
    """Battle events."""

    def test_battle(self):
        events = [_FakeRaceEvent("BATTLE", 300, ["A", "B"],
                            {"gap": 0.5, "duration_frames": 120})]
        result = adapt_circuit_events(_cc_replay(), events)
        b = [e for e in result if e.type == "battle"]
        assert len(b) == 1
        assert b[0].drama_weight == 4


class TestCircuitAdapterIncidents:
    """Spin and safety car events."""

    def test_spin(self):
        events = [_FakeRaceEvent("SPIN", 200, ["CarX"])]
        result = adapt_circuit_events(_cc_replay(), events)
        spins = [e for e in result if e.type == "spin"]
        assert len(spins) == 1
        assert spins[0].drama_weight == 3

    def test_safety_car(self):
        events = [_FakeRaceEvent("SAFETY_CAR", 500, ["CarX"], {"reason": "incident"})]
        result = adapt_circuit_events(_cc_replay(), events)
        sc = [e for e in result if e.type == "safety_car"]
        assert len(sc) == 1
        assert sc[0].drama_weight == 5


class TestCircuitAdapterPitAndFastest:
    """Pit stop and fastest lap."""

    def test_pit_stop(self):
        events = [_FakeRaceEvent("PIT_STOP", 400, ["CarA"], {"compound": "soft"})]
        result = adapt_circuit_events(_cc_replay(), events)
        pits = [e for e in result if e.type == "pit_stop"]
        assert len(pits) == 1
        assert pits[0].drama_weight == 1

    def test_fastest_lap(self):
        events = [_FakeRaceEvent("FASTEST_LAP", 0, ["CarA"], {"time": 72.5})]
        result = adapt_circuit_events(_cc_replay(), events)
        fl = [e for e in result if e.type == "fastest_lap"]
        assert len(fl) == 1
        assert fl[0].drama_weight == 2


class TestCircuitTimestamp:
    """Tick → seconds conversion."""

    def test_tick_to_seconds(self):
        events = [_FakeRaceEvent("SPIN", 150, ["Car"])]
        replay = _cc_replay()
        result = adapt_circuit_events(replay, events)
        assert result[0].timestamp == 5.0  # 150 / 30


class TestEventTypesDocumented:
    """EVENT_TYPES documents all types with drama_weight rationale."""

    def test_all_types_have_weight(self):
        for etype, info in EVENT_TYPES.items():
            assert "weight" in info, f"{etype} missing weight"
            assert "rationale" in info, f"{etype} missing rationale"

    def test_weights_are_positive(self):
        for etype, info in EVENT_TYPES.items():
            assert info["weight"] >= 0, f"{etype} has negative weight"
