"""Tests for audio/waveforms.py — low-level waveform primitives."""

from pathlib import Path

from audio.waveforms import (
    SAMPLE_RATE,
    apply_decay,
    noise_samples,
    sine_samples,
    square_samples,
    write_wav,
)


class TestSineSamples:
    """sine_samples generates valid 8-bit unsigned sine waves."""

    def test_correct_length(self) -> None:
        samples = sine_samples(440, 0.5)
        assert len(samples) == int(SAMPLE_RATE * 0.5)

    def test_values_in_8bit_range(self) -> None:
        samples = sine_samples(440, 0.3, volume=200)
        assert all(0 <= s <= 255 for s in samples)

    def test_center_is_128(self) -> None:
        samples = sine_samples(440, 1.0)
        avg = sum(samples) / len(samples)
        assert 120 < avg < 136  # approximately centered

    def test_zero_volume_is_flat(self) -> None:
        samples = sine_samples(440, 0.1, volume=0)
        assert all(s == 128 for s in samples)


class TestSquareSamples:
    """square_samples generates valid 8-bit unsigned square waves."""

    def test_correct_length(self) -> None:
        samples = square_samples(440, 0.5)
        assert len(samples) == int(SAMPLE_RATE * 0.5)

    def test_values_in_8bit_range(self) -> None:
        samples = square_samples(440, 0.3, volume=200)
        assert all(0 <= s <= 255 for s in samples)

    def test_only_two_distinct_values(self) -> None:
        samples = square_samples(440, 0.5, volume=100)
        unique = set(samples)
        assert len(unique) == 2

    def test_high_and_low_symmetric(self) -> None:
        samples = square_samples(440, 0.5, volume=100)
        unique = sorted(set(samples))
        assert unique[0] == 128 - 50
        assert unique[1] == 128 + 50


class TestNoiseSamples:
    """noise_samples generates deterministic pseudo-random noise."""

    def test_correct_length(self) -> None:
        samples = noise_samples(0.5)
        assert len(samples) == int(SAMPLE_RATE * 0.5)

    def test_values_in_8bit_range(self) -> None:
        samples = noise_samples(0.5, volume=200)
        assert all(0 <= s <= 255 for s in samples)

    def test_deterministic(self) -> None:
        a = noise_samples(0.1)
        b = noise_samples(0.1)
        assert a == b

    def test_not_constant(self) -> None:
        samples = noise_samples(0.5)
        assert len(set(samples)) > 10


class TestApplyDecay:
    """apply_decay applies linear decay envelope."""

    def test_preserves_length(self) -> None:
        original = [200] * 100
        result = apply_decay(original, 0.5)
        assert len(result) == len(original)

    def test_values_in_8bit_range(self) -> None:
        original = sine_samples(440, 0.5)
        result = apply_decay(original)
        assert all(0 <= s <= 255 for s in result)

    def test_end_approaches_center(self) -> None:
        original = [255] * 1000
        result = apply_decay(original, 0.0)
        assert abs(result[-1] - 128) < 5


class TestWriteWav:
    """write_wav creates valid WAV files."""

    def test_creates_file(self, tmp_path: Path) -> None:
        path = tmp_path / "test.wav"
        write_wav(path, [128] * 100)
        assert path.exists()

    def test_riff_header(self, tmp_path: Path) -> None:
        path = tmp_path / "test.wav"
        write_wav(path, sine_samples(440, 0.1))
        with open(path, "rb") as f:
            assert f.read(4) == b"RIFF"

    def test_nonzero_size(self, tmp_path: Path) -> None:
        path = tmp_path / "test.wav"
        write_wav(path, sine_samples(440, 0.1))
        assert path.stat().st_size > 44  # WAV header is 44 bytes
