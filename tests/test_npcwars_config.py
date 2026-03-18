"""Tests for npcwars.config -- TOML config reader/writer."""
from __future__ import annotations

import tomllib
from pathlib import Path

from agentgrounds.wars.config import default_config, load_config, write_default_config


# -- Cycle 1: default_config() --


def test_default_config_returns_dict():
    result = default_config()
    assert isinstance(result, dict)


def test_default_config_has_required_keys():
    result = default_config()
    assert "bots_dir" in result
    assert "replays_dir" in result
    assert "seed" in result


def test_default_config_bots_dir():
    assert default_config()["bots_dir"] == "bots"


def test_default_config_replays_dir():
    assert default_config()["replays_dir"] == "replays"


def test_default_config_seed_is_none():
    assert default_config()["seed"] is None


# -- Cycle 2: load_config() --


def test_load_config_nonexistent_returns_defaults(tmp_path: Path):
    result = load_config(tmp_path / "missing.toml")
    assert result == default_config()


def test_load_config_reads_values(tmp_path: Path):
    cfg = tmp_path / "agentgrounds.toml"
    cfg.write_text('bots_dir = "custom_bots"\nseed = 99\n', encoding="utf-8")
    result = load_config(cfg)
    assert result["bots_dir"] == "custom_bots"
    assert result["seed"] == 99


def test_load_config_merges_with_defaults(tmp_path: Path):
    """Missing keys in TOML get filled from defaults."""
    cfg = tmp_path / "agentgrounds.toml"
    cfg.write_text('seed = 42\n', encoding="utf-8")
    result = load_config(cfg)
    assert result["bots_dir"] == "bots"
    assert result["replays_dir"] == "replays"
    assert result["seed"] == 42


# -- Cycle 3: write_default_config() --


def test_write_default_config_creates_file(tmp_path: Path):
    out = tmp_path / "agentgrounds.toml"
    write_default_config(out)
    assert out.exists()


def test_write_default_config_parseable_by_tomllib(tmp_path: Path):
    out = tmp_path / "agentgrounds.toml"
    write_default_config(out)
    with open(out, "rb") as f:
        data = tomllib.load(f)
    assert isinstance(data, dict)


def test_round_trip_write_then_load(tmp_path: Path):
    """write_default_config then load_config returns defaults."""
    out = tmp_path / "agentgrounds.toml"
    write_default_config(out)
    result = load_config(out)
    # Written file has bots_dir and replays_dir but seed is commented out
    assert result["bots_dir"] == "bots"
    assert result["replays_dir"] == "replays"
    assert result["seed"] is None
