"""Integration tests for the spectacle pipeline end-to-end."""

import inspect

from audio.mixer import build_audio_timeline, build_hype_volume_curve
from engine.game import run_match
from video.video_render import render_match_video

from tests.conftest import bot_config, always_rest, chase_and_attack


VALID_TIERS = {"calm", "heating", "intense", "hype", "chaos"}
SEED = 42


def _build_match(num_bots: int = 6, seed: int = SEED) -> dict:
    """Run a seeded match with a mix of passive and aggressive bots."""
    configs = []
    emojis = [chr(0x1F600 + i) for i in range(num_bots)]
    for i in range(num_bots):
        decide = chase_and_attack if i % 2 == 0 else always_rest
        configs.append(bot_config(f"Bot{i}", emojis[i], decide))
    return run_match(configs, match_id=999, seed=seed)


# ---- Fixture: run once and cache ----
_MATCH_DATA: dict | None = None


def _get_match_data() -> dict:
    global _MATCH_DATA
    if _MATCH_DATA is None:
        _MATCH_DATA = _build_match()
    return _MATCH_DATA


# ---- Test 1: Spectacle metadata in all rounds ----


def test_every_round_has_spectacle_key():
    """Every round in the match must contain spectacle metadata."""
    match_data = _get_match_data()
    rounds = match_data["rounds"]
    assert len(rounds) > 0, "Match should have at least one round"
    for i, rd in enumerate(rounds):
        assert "spectacle" in rd, f"Round {i} missing 'spectacle' key"


def test_spectacle_has_required_fields():
    """Spectacle dict must contain drama_score, tier, triggers, effects."""
    match_data = _get_match_data()
    for i, rd in enumerate(match_data["rounds"]):
        spec = rd["spectacle"]
        assert isinstance(spec["drama_score"], int), f"Round {i}: drama_score not int"
        assert isinstance(spec["tier"], str), f"Round {i}: tier not str"
        assert isinstance(spec["triggers"], list), f"Round {i}: triggers not list"
        assert isinstance(spec["effects"], list), f"Round {i}: effects not list"


# ---- Test 2: Tier assignments are reasonable ----


def test_all_tiers_in_valid_set():
    """Every tier value must be one of the valid tiers."""
    match_data = _get_match_data()
    for i, rd in enumerate(match_data["rounds"]):
        tier = rd["spectacle"]["tier"]
        assert tier in VALID_TIERS, f"Round {i}: invalid tier '{tier}'"


def test_zero_event_rounds_are_calm():
    """Rounds with no events should have tier 'calm'."""
    match_data = _get_match_data()
    for i, rd in enumerate(match_data["rounds"]):
        events = rd.get("events", [])
        spec = rd["spectacle"]
        if len(events) == 0:
            assert spec["tier"] == "calm", (
                f"Round {i}: zero events but tier is '{spec['tier']}'"
            )


# ---- Test 3: Drama score consistency ----


def test_drama_scores_are_non_negative():
    """All drama_score values must be >= 0."""
    match_data = _get_match_data()
    for i, rd in enumerate(match_data["rounds"]):
        score = rd["spectacle"]["drama_score"]
        assert score >= 0, f"Round {i}: drama_score is {score}"


# ---- Test 4: Trigger-effect consistency ----


def test_kill_trigger_produces_shatter():
    """When 'kill' is in triggers, 'shatter' should be in effects."""
    match_data = _get_match_data()
    for i, rd in enumerate(match_data["rounds"]):
        spec = rd["spectacle"]
        if "kill" in spec["triggers"]:
            assert "shatter" in spec["effects"], (
                f"Round {i}: 'kill' trigger but no 'shatter' effect"
            )


def test_kill_streak_trigger_produces_fire_border():
    """When 'kill_streak' is in triggers, 'fire_border' should be in effects."""
    match_data = _get_match_data()
    for i, rd in enumerate(match_data["rounds"]):
        spec = rd["spectacle"]
        if "kill_streak" in spec["triggers"]:
            assert "fire_border" in spec["effects"], (
                f"Round {i}: 'kill_streak' trigger but no 'fire_border' effect"
            )


def test_near_death_trigger_produces_slow_mo():
    """When 'near_death' is in triggers, 'slow_mo' should be in effects."""
    match_data = _get_match_data()
    for i, rd in enumerate(match_data["rounds"]):
        spec = rd["spectacle"]
        if "near_death" in spec["triggers"]:
            assert "slow_mo" in spec["effects"], (
                f"Round {i}: 'near_death' trigger but no 'slow_mo' effect"
            )


def test_chain_bump_trigger_produces_multiball():
    """When 'chain_bump' is in triggers, 'multiball' should be in effects."""
    match_data = _get_match_data()
    for i, rd in enumerate(match_data["rounds"]):
        spec = rd["spectacle"]
        if "chain_bump" in spec["triggers"]:
            assert "multiball" in spec["effects"], (
                f"Round {i}: 'chain_bump' trigger but no 'multiball' effect"
            )


# ---- Test 5: Calm round has baseline values ----


def test_zero_score_round_is_calm():
    """A round with drama_score == 0 should have tier 'calm'."""
    match_data = _get_match_data()
    zero_score_found = False
    for rd in match_data["rounds"]:
        spec = rd["spectacle"]
        if spec["drama_score"] == 0:
            zero_score_found = True
            assert spec["tier"] == "calm", (
                f"drama_score=0 but tier='{spec['tier']}'"
            )
    # If no zero-score rounds, the test is vacuously true but worth noting.
    if not zero_score_found:
        # Still passes -- just means this match was eventful every round.
        pass


# ---- Test 6: Audio timeline from match data ----


def test_audio_timeline_returns_list():
    """build_audio_timeline should return a list."""
    match_data = _get_match_data()
    timeline = build_audio_timeline(match_data)
    assert isinstance(timeline, list)


def test_audio_timeline_entries_are_tuples():
    """Each timeline entry should be a (timestamp_ms, path) tuple."""
    match_data = _get_match_data()
    timeline = build_audio_timeline(match_data)
    for entry in timeline:
        assert isinstance(entry, tuple), f"Entry is {type(entry)}, not tuple"
        assert len(entry) == 2, f"Entry has {len(entry)} elements, expected 2"
        ts, path = entry
        assert isinstance(ts, int), f"Timestamp {ts} is not int"
        assert isinstance(path, str), f"Path {path} is not str"


# ---- Test 7: Hype volume curve from match data ----


def test_hype_volume_curve_one_per_round():
    """build_hype_volume_curve should return one entry per round."""
    match_data = _get_match_data()
    curve = build_hype_volume_curve(match_data)
    assert len(curve) == len(match_data["rounds"])


def test_hype_volume_values_in_range():
    """All hype volume values must be between 0.0 and 1.0."""
    match_data = _get_match_data()
    curve = build_hype_volume_curve(match_data)
    for ts, vol in curve:
        assert 0.0 <= vol <= 1.0, f"Volume {vol} at ts={ts} out of range"


# ---- Test 8: Video render function signature ----


def test_render_match_video_accepts_audio_param():
    """render_match_video must accept an 'audio' parameter."""
    sig = inspect.signature(render_match_video)
    assert "audio" in sig.parameters, (
        "render_match_video missing 'audio' parameter"
    )


def test_render_match_video_audio_default_is_true():
    """render_match_video 'audio' parameter should default to True."""
    sig = inspect.signature(render_match_video)
    audio_param = sig.parameters["audio"]
    assert audio_param.default is True, (
        f"'audio' default is {audio_param.default}, expected True"
    )
