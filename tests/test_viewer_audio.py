"""Structural tests for Web Audio integration in viewer."""

from conftest import read_viewer_content


def _read_viewer() -> str:
    """Read all viewer files (index.html + js/*.js)."""
    return read_viewer_content()


def test_audio_engine_class_defined():
    """AudioEngine class must be defined in the viewer JS."""
    html = _read_viewer()
    assert "class AudioEngine" in html


def test_audio_engine_has_init_method():
    """AudioEngine must have an init() method."""
    html = _read_viewer()
    assert "init()" in html


def test_audio_engine_has_play_method():
    """AudioEngine must have a play() method with eventType and tier params."""
    html = _read_viewer()
    assert "play(eventType" in html or "play(eventType," in html


def test_audio_engine_has_set_master_volume():
    """AudioEngine must have a setMasterVolume method."""
    html = _read_viewer()
    assert "setMasterVolume(" in html


def test_audio_engine_has_toggle_mute():
    """AudioEngine must have a toggleMute method."""
    html = _read_viewer()
    assert "toggleMute()" in html


def test_volume_slider_element_exists():
    """HTML must contain a volume-slider input element."""
    html = _read_viewer()
    assert 'id="volume-slider"' in html


def test_mute_button_element_exists():
    """HTML must contain a mute-btn button element."""
    html = _read_viewer()
    assert 'id="mute-btn"' in html


def test_audio_controls_css_class():
    """CSS must contain .audio-controls styling."""
    html = _read_viewer()
    assert ".audio-controls" in html


def test_audio_engine_global_variable():
    """A global audioEngine instance must be created."""
    html = _read_viewer()
    assert "audioEngine" in html
    # Must be instantiated
    assert "new AudioEngine()" in html


def test_audio_engine_play_called_in_render_round():
    """renderRound must call audioEngine.play for events."""
    html = _read_viewer()
    assert "audioEngine.play(" in html


def test_volume_persisted_to_local_storage():
    """Volume preference must be saved to localStorage."""
    html = _read_viewer()
    assert "localStorage" in html
    assert "npc-wars-volume" in html


def test_audio_engine_init_called_in_init_viewer():
    """audioEngine.init() must be called during viewer initialization."""
    html = _read_viewer()
    assert "audioEngine.init()" in html
