"""Tests for T15.5: skull_flash, pulse_wave, multiball, split_screen effects."""

from conftest import read_viewer_content


def _html() -> str:
    return read_viewer_content()


# --- skull_flash ---


def test_skull_flash_function_exists():
    assert "function skullFlashEffect()" in _html()


def test_skull_flash_keyframes_exists():
    assert "@keyframes skull-flash-fade" in _html()


def test_skull_flash_wired_to_near_death():
    html = _html()
    assert "near_death" in html
    assert "skullFlashEffect" in html
    # The trigger wiring should be inside applySpectacleEffects
    idx_apply = html.index("function applySpectacleEffects")
    idx_end = html.index("}", html.index("// Banners", idx_apply))
    block = html[idx_apply:idx_end]
    assert "near_death" in block
    assert "skullFlashEffect" in block


def test_skull_flash_has_cleanup():
    html = _html()
    idx = html.index("function skullFlashEffect()")
    # Find the closing of the function (next top-level function)
    end = html.index("\nfunction ", idx + 1)
    body = html[idx:end]
    assert "remove()" in body


# --- pulse_wave ---


def test_pulse_wave_function_exists():
    assert "function pulseWaveEffect(x, y)" in _html()


def test_pulse_wave_uses_request_animation_frame():
    html = _html()
    idx = html.index("function pulseWaveEffect(x, y)")
    end = html.index("\nfunction ", idx + 1)
    body = html[idx:end]
    assert "requestAnimationFrame" in body


def test_pulse_wave_wired_to_watcher_attack():
    html = _html()
    idx_apply = html.index("function applySpectacleEffects")
    idx_end = html.index("}", html.index("// Banners", idx_apply))
    block = html[idx_apply:idx_end]
    assert "watcher_attack" in block
    assert "pulseWaveEffect" in block


# --- multiball ---


def test_multiball_function_exists():
    assert "function multiballEffect(positions)" in _html()


def test_multiball_uses_request_animation_frame():
    html = _html()
    idx = html.index("function multiballEffect(positions)")
    end = html.index("\nfunction ", idx + 1)
    body = html[idx:end]
    assert "requestAnimationFrame" in body


def test_multiball_wired_to_chain_bump():
    html = _html()
    idx_apply = html.index("function applySpectacleEffects")
    # Find the end of applySpectacleEffects function body
    idx_end = html.index("}", html.index("// Banners", idx_apply))
    block = html[idx_apply:idx_end]
    assert "multiballEffect" in block


# --- split_screen ---


def test_split_screen_function_exists():
    assert "function splitScreenEffect()" in _html()


def test_split_screen_css_divider():
    assert ".split-screen-divider" in _html()


def test_split_screen_css_glow_animation():
    assert "@keyframes split-divider-glow" in _html()


def test_split_screen_wired_to_last_2():
    html = _html()
    idx_apply = html.index("function applySpectacleEffects")
    idx_end = html.index("}", html.index("// Banners", idx_apply))
    block = html[idx_apply:idx_end]
    assert "splitScreenEffect" in block


# --- no interference ---


def test_all_four_functions_exist():
    html = _html()
    assert "function skullFlashEffect()" in html
    assert "function pulseWaveEffect(x, y)" in html
    assert "function multiballEffect(positions)" in html
    assert "function splitScreenEffect()" in html
