"""Structural tests for synthesized audio stingers in the viewer."""

from pathlib import Path


AUDIO_JS = Path(__file__).parent.parent / "viewer" / "js" / "audio.js"
EVENTS_JS = Path(__file__).parent.parent / "viewer" / "js" / "events.js"


def _read_audio() -> str:
    return AUDIO_JS.read_text(encoding="utf-8")


def _read_events() -> str:
    return EVENTS_JS.read_text(encoding="utf-8")


# --- AudioEngine synth methods ---


def test_audio_has_play_synth_method():
    """AudioEngine must have a playSynth(type) method."""
    src = _read_audio()
    assert "playSynth(" in src


def test_audio_has_synth_tone_method():
    """AudioEngine must have a _synthTone helper."""
    src = _read_audio()
    assert "_synthTone(" in src


def test_audio_has_synth_sweep_method():
    """AudioEngine must have a _synthSweep helper."""
    src = _read_audio()
    assert "_synthSweep(" in src


def test_audio_has_synth_noise_method():
    """AudioEngine must have a _synthNoise helper."""
    src = _read_audio()
    assert "_synthNoise(" in src


# --- playSynth handles all required event types ---


def test_play_synth_handles_trap_trigger():
    src = _read_audio()
    assert "'trap_trigger'" in src or '"trap_trigger"' in src


def test_play_synth_handles_tactical_activate():
    src = _read_audio()
    assert "'tactical_activate'" in src or '"tactical_activate"' in src


def test_play_synth_handles_ability_damage():
    src = _read_audio()
    assert "'ability_damage'" in src or '"ability_damage"' in src


def test_play_synth_handles_ability_heal():
    src = _read_audio()
    assert "'ability_heal'" in src or '"ability_heal"' in src


def test_play_synth_handles_ability_shield():
    src = _read_audio()
    assert "'ability_shield'" in src or '"ability_shield"' in src


def test_play_synth_handles_ability_slow():
    src = _read_audio()
    assert "'ability_slow'" in src or '"ability_slow"' in src


def test_play_synth_handles_crystal_pickup():
    src = _read_audio()
    assert "'crystal_pickup'" in src or '"crystal_pickup"' in src


def test_play_synth_handles_evolve():
    src = _read_audio()
    assert "'evolve'" in src or '"evolve"' in src


# --- playSynth guards (muted / not ready) ---


def test_play_synth_checks_ready_and_muted():
    """playSynth must bail early when not ready or muted."""
    src = _read_audio()
    # The method should check this.ready and this.muted
    assert "this.ready" in src
    assert "this.muted" in src


# --- events.js wires playSynth calls ---


def test_events_calls_play_synth():
    """events.js must call playSynth for at least one event type."""
    src = _read_events()
    assert "playSynth(" in src


def test_events_synth_trap_trigger():
    src = _read_events()
    assert "playSynth('trap_trigger')" in src or 'playSynth("trap_trigger")' in src


def test_events_synth_tactical_activate():
    src = _read_events()
    assert "playSynth('tactical_activate')" in src or 'playSynth("tactical_activate")' in src


def test_events_synth_ability_damage():
    src = _read_events()
    assert "playSynth('ability_damage')" in src or 'playSynth("ability_damage")' in src


def test_events_synth_ability_heal():
    src = _read_events()
    assert "playSynth('ability_heal')" in src or 'playSynth("ability_heal")' in src


def test_events_synth_ability_shield():
    src = _read_events()
    assert "playSynth('ability_shield')" in src or 'playSynth("ability_shield")' in src


def test_events_synth_ability_slow():
    src = _read_events()
    assert "playSynth('ability_slow')" in src or 'playSynth("ability_slow")' in src


def test_events_synth_crystal_pickup():
    src = _read_events()
    assert "playSynth('crystal_pickup')" in src or 'playSynth("crystal_pickup")' in src


def test_events_synth_evolve():
    src = _read_events()
    assert "playSynth('evolve')" in src or 'playSynth("evolve")' in src


# --- File size guard ---


def test_audio_js_under_300_lines():
    """audio.js must stay under 300 lines after synth additions."""
    lines = AUDIO_JS.read_text(encoding="utf-8").splitlines()
    assert len(lines) < 300, f"audio.js is {len(lines)} lines (limit 300)"


def test_existing_play_method_preserved():
    """The existing play(eventType, tier) method must not be removed."""
    src = _read_audio()
    assert "play(eventType" in src
