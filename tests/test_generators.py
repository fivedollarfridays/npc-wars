"""Tests for audio/generators.py — stinger sample generators."""

import pytest

from audio.generators import GENERATORS


GENERATOR_NAMES = list(GENERATORS.keys())


class TestGeneratorRegistry:
    """GENERATORS dict maps all expected event types."""

    def test_has_13_generators(self) -> None:
        assert len(GENERATORS) == 13

    @pytest.mark.parametrize("name", GENERATOR_NAMES)
    def test_generator_is_callable(self, name: str) -> None:
        assert callable(GENERATORS[name])


class TestGeneratorOutput:
    """Each generator produces valid 8-bit sample data."""

    @pytest.mark.parametrize("name", GENERATOR_NAMES)
    def test_returns_nonempty_list(self, name: str) -> None:
        samples = GENERATORS[name]()
        assert isinstance(samples, list)
        assert len(samples) > 0

    @pytest.mark.parametrize("name", GENERATOR_NAMES)
    def test_values_in_8bit_range(self, name: str) -> None:
        samples = GENERATORS[name]()
        assert all(0 <= s <= 255 for s in samples), f"{name} has out-of-range values"

    @pytest.mark.parametrize("name", GENERATOR_NAMES)
    def test_not_constant(self, name: str) -> None:
        samples = GENERATORS[name]()
        unique = len(set(samples))
        assert unique > 1, f"{name} produces constant output"

    @pytest.mark.parametrize("name", GENERATOR_NAMES)
    def test_deterministic(self, name: str) -> None:
        a = GENERATORS[name]()
        b = GENERATORS[name]()
        assert a == b, f"{name} is not deterministic"
