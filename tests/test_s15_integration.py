"""Sprint 15 integration gate: verify all viewer polish features are wired."""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PLAY_PY = PROJECT_ROOT / "play.py"


def _html() -> str:
    from conftest import read_viewer_content
    return read_viewer_content()


def _play() -> str:
    return PLAY_PY.read_text(encoding="utf-8")


# ---------- 1. Audio path correctness ----------

class TestAudioPaths:
    def test_audio_uses_parent_relative_path(self):
        src = _html()
        assert "../audio/assets/" in src

    def test_no_bare_audio_assets_path(self):
        src = _html()
        # Remove all correct paths, then check no bare ones remain
        cleaned = src.replace("../audio/assets/", "")
        assert "audio/assets/" not in cleaned


# ---------- 2. All spectacle effect functions exist ----------

EFFECT_FUNCTIONS = [
    "shatterEffect",
    "glitchEffect",
    "darkEntranceEffect",
    "skullFlashEffect",
    "pulseWaveEffect",
    "multiballEffect",
    "splitScreenEffect",
]


class TestEffectFunctionsExist:
    def test_all_effect_functions_defined(self):
        src = _html()
        for fn in EFFECT_FUNCTIONS:
            assert re.search(rf"function\s+{fn}\s*\(", src), (
                f"function {fn} not found in match.html"
            )


# ---------- 3. Effects wired to triggers in applySpectacleEffects ----------

TRIGGER_EFFECT_MAP = {
    "storm_kill": "glitchEffect",
    "watcher_spawn": "darkEntranceEffect",
    "near_death": "skullFlashEffect",
    "chain_bump": "multiballEffect",
    "last_2": "splitScreenEffect",
}


class TestTriggerWiring:
    def test_apply_spectacle_effects_function_exists(self):
        src = _html()
        assert re.search(r"function\s+applySpectacleEffects\s*\(", src)

    def test_trigger_to_effect_mappings(self):
        src = _html()
        # Extract applySpectacleEffects body
        match = re.search(
            r"function\s+applySpectacleEffects\s*\([^)]*\)\s*\{",
            src,
        )
        assert match, "applySpectacleEffects not found"
        start = match.start()
        # Find balanced closing brace
        depth = 0
        body_start = src.index("{", start)
        for i in range(body_start, len(src)):
            if src[i] == "{":
                depth += 1
            elif src[i] == "}":
                depth -= 1
                if depth == 0:
                    body = src[body_start : i + 1]
                    break
        for trigger, effect in TRIGGER_EFFECT_MAP.items():
            assert trigger in body, f"trigger '{trigger}' not in applySpectacleEffects"
            assert effect in body, f"effect '{effect}' not called in applySpectacleEffects"


# ---------- 4. Kill events trigger shatter ----------

class TestKillShatter:
    def test_shatter_called_on_kill_event(self):
        src = _html()
        # The events loop should have kill check calling shatterEffect
        assert re.search(
            r"""evt\.type\s*===?\s*['"]kill['"]""",
            src,
        ), "No kill event type check found"

    def test_shatter_called_near_kill_check(self):
        src = _html()
        # Find the kill event block and verify shatterEffect is nearby
        kill_match = re.search(r"evt\.type\s*===?\s*['\"]kill['\"]", src)
        assert kill_match
        # shatterEffect should appear within 300 chars after the kill check
        after_kill = src[kill_match.start() : kill_match.start() + 300]
        assert "shatterEffect" in after_kill


# ---------- 5. Layout correctness ----------

class TestLayout:
    def test_arena_wrap_flex_1(self):
        src = _html()
        # .arena-wrap should have flex: 1
        arena_section = re.search(
            r"\.arena-wrap\s*\{[^}]*flex:\s*1[^}]*\}",
            src,
            re.DOTALL,
        )
        assert arena_section, ".arena-wrap missing flex: 1"

    def test_sidebar_max_width_250(self):
        src = _html()
        sidebar_section = re.search(
            r"\.sidebar\s*\{[^}]*max-width:\s*250px[^}]*\}",
            src,
            re.DOTALL,
        )
        assert sidebar_section, ".sidebar missing max-width: 250px"

    def test_media_query_1024(self):
        src = _html()
        assert re.search(r"@media\s*\(\s*min-width:\s*1024px\s*\)", src)


# ---------- 6. Interpolation wired ----------

class TestInterpolation:
    def test_playback_loop_exists(self):
        src = _html()
        assert re.search(r"function\s+playbackLoop\s*\(", src)

    def test_request_animation_frame_used(self):
        src = _html()
        assert "requestAnimationFrame" in src

    def test_lerp_function_exists(self):
        src = _html()
        assert re.search(r"function\s+lerp\s*\(", src)

    def test_render_canvas_extracted(self):
        src = _html()
        assert re.search(r"function\s+renderCanvas\s*\(", src)


# ---------- 7. Player profiles wired in play.py ----------

class TestPlayerProfiles:
    def test_profiles_path_in_run_match_call(self):
        src = _play()
        assert "profiles_path=" in src

    def test_profiles_path_variable_created(self):
        src = _play()
        assert "profiles_path" in src
        assert "profiles.json" in src


# ---------- 8. No dead public functions ----------

class TestNoDeadFunctions:
    def test_every_effect_used_at_least_twice(self):
        """Each effect function name should appear at least twice:
        once for definition, once for call site."""
        src = _html()
        for fn in EFFECT_FUNCTIONS:
            count = len(re.findall(re.escape(fn), src))
            assert count >= 2, (
                f"{fn} appears {count} time(s) -- likely dead code"
            )
