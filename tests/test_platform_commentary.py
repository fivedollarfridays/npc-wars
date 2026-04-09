"""Tests for platform commentary contract (T61.2)."""
from __future__ import annotations

import dataclasses
from typing import Any

from engine.platform_commentary import (
    CommentaryLine,
    CommentaryContract,
    VALID_TONES,
    VALID_LINE_TYPES,
)


# -- CommentaryLine dataclass --------------------------------------------------


class TestCommentaryLineShape:
    """CommentaryLine has required fields with correct types."""

    def test_required_fields(self):
        line = CommentaryLine(
            timestamp=3.0, text="Bot charges forward!", tone="hype",
            line_type="play_by_play",
        )
        assert line.timestamp == 3.0
        assert line.text == "Bot charges forward!"
        assert line.tone == "hype"
        assert line.line_type == "play_by_play"

    def test_is_frozen(self):
        line = CommentaryLine(
            timestamp=1.0, text="test", tone="calm", line_type="color",
        )
        try:
            line.tone = "chaos"  # type: ignore[misc]
            raise AssertionError("Should be frozen")
        except (dataclasses.FrozenInstanceError, AttributeError):
            pass

    def test_is_dataclass(self):
        assert dataclasses.is_dataclass(CommentaryLine)

    def test_asdict(self):
        line = CommentaryLine(
            timestamp=2.0, text="Overtake!", tone="intense",
            line_type="play_by_play",
        )
        d = dataclasses.asdict(line)
        assert d == {
            "timestamp": 2.0, "text": "Overtake!",
            "tone": "intense", "line_type": "play_by_play",
        }


class TestValidTones:
    """All five drama tones are defined."""

    def test_five_tones(self):
        assert VALID_TONES == {"calm", "heating", "intense", "hype", "chaos"}


class TestValidLineTypes:
    """All three line types are defined."""

    def test_three_types(self):
        assert VALID_LINE_TYPES == {"play_by_play", "color", "analysis"}


# -- CommentaryContract protocol -----------------------------------------------


class _FakeCommentarySource:
    """Minimal implementation of CommentaryContract for testing."""

    def generate_commentary(self, **kwargs: Any) -> list[CommentaryLine]:
        return [
            CommentaryLine(timestamp=1.0, text="Action!", tone="calm", line_type="play_by_play"),
        ]


class TestCommentaryContract:
    """Protocol is structurally matched."""

    def test_fake_source_satisfies_protocol(self):
        src: CommentaryContract = _FakeCommentarySource()
        result = src.generate_commentary()
        assert isinstance(result, list)
        assert all(isinstance(line, CommentaryLine) for line in result)


# -- Kill Switch conformance ---------------------------------------------------


class TestKillSwitchConformance:
    """Kill Switch generate_commentary returns list[CommentaryLine]."""

    def test_returns_platform_commentary_lines(self):
        from engine.commentary import generate_commentary

        rounds = [{"round": 1, "storm_border": 5, "positions": [
            {"emoji": "A", "action": "move north", "hp": 50, "alive": True, "x": 3, "y": 3},
            {"emoji": "B", "action": "move south", "hp": 50, "alive": True, "x": 5, "y": 5},
        ], "events": []}]
        md = {
            "match_id": 1, "winner": "A",
            "players": [{"emoji": "A"}, {"emoji": "B"}],
            "rounds": rounds, "eliminations": [],
            "stats": {"A": {"kills": 0, "archetype": "Bruiser", "equipment": {}},
                       "B": {"kills": 0, "archetype": "Assassin", "equipment": {}}},
            "duration_rounds": 1,
        }
        result = generate_commentary(md, {}, {})
        assert isinstance(result, list)
        assert len(result) > 0
        for line in result:
            assert isinstance(line, CommentaryLine)
            assert line.tone in VALID_TONES
            assert line.line_type in VALID_LINE_TYPES
            assert isinstance(line.timestamp, (int, float))
            assert isinstance(line.text, str)


# -- Code Circuit conformance --------------------------------------------------


class TestCodeCircuitConformance:
    """Code Circuit generate_circuit_commentary returns list[CommentaryLine]."""

    def test_returns_platform_commentary_lines(self):
        from engine.circuit_commentary import generate_circuit_commentary

        replay = {
            "track_name": "TestTrack", "laps": 5, "ticks_per_sec": 30,
            "frames": [], "results": [
                {"car": "AlphaCar", "position": 1},
                {"car": "BetaCar", "position": 2},
            ],
        }

        class FakeEvent:
            def __init__(self, etype, tick, cars, data=None):
                self.type = etype
                self.tick = tick
                self.cars = cars
                self.data = data or {}

        race_events = [
            FakeEvent("OVERTAKE", 150, ["AlphaCar", "BetaCar"], {"position": 2}),
            FakeEvent("BATTLE", 300, ["AlphaCar", "BetaCar"], {"gap": 0.3}),
            FakeEvent("SPIN", 500, ["BetaCar"], {}),
        ]
        result = generate_circuit_commentary(replay, race_events)
        assert isinstance(result, list)
        assert len(result) > 0
        for line in result:
            assert isinstance(line, CommentaryLine)
            assert line.tone in VALID_TONES
            assert line.line_type in VALID_LINE_TYPES
            assert isinstance(line.timestamp, (int, float))
            assert isinstance(line.text, str)
