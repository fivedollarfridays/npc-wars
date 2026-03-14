"""Tests for Watcher memory persistence (JSON save/load)."""

from __future__ import annotations

import json
from pathlib import Path

from engine.watcher_memory import PatternTable, load_memory, save_memory


class TestPatternTableSerialization:
    """Tests for to_dict / from_dict methods."""

    def test_to_dict_empty(self) -> None:
        pt = PatternTable()
        assert pt.to_dict() == {}

    def test_to_dict_with_data(self) -> None:
        pt = PatternTable()
        pt.record("alice", "after_damage", "heal")
        pt.record("alice", "after_damage", "heal")
        pt.record("alice", "at_range_1", "attack")

        data = pt.to_dict()
        assert data["alice"]["after_damage"]["heal"] == 2
        assert data["alice"]["at_range_1"]["attack"] == 1
        # Global profile should also be present
        assert data["__global__"]["after_damage"]["heal"] == 2

    def test_to_dict_returns_copy(self) -> None:
        """Mutating the returned dict must not change the PatternTable."""
        pt = PatternTable()
        pt.record("bob", "below_30_hp", "flee")
        data = pt.to_dict()
        data["bob"]["below_30_hp"]["flee"] = 999
        assert pt.get_raw_counts("bob", "below_30_hp")["flee"] == 1

    def test_from_dict_empty(self) -> None:
        pt = PatternTable.from_dict({})
        assert pt.players() == set()

    def test_from_dict_reconstructs_data(self) -> None:
        raw = {
            "alice": {"after_damage": {"heal": 5, "attack": 3}},
            "__global__": {"after_damage": {"heal": 5, "attack": 3}},
        }
        pt = PatternTable.from_dict(raw)
        assert pt.get_raw_counts("alice", "after_damage") == {"heal": 5, "attack": 3}
        assert pt.players() == {"alice"}

    def test_from_dict_roundtrip(self) -> None:
        pt = PatternTable()
        pt.record("alice", "after_damage", "heal")
        pt.record("alice", "after_damage", "attack")
        pt.record("bob", "storm_closing", "flee")

        restored = PatternTable.from_dict(pt.to_dict())
        assert restored.to_dict() == pt.to_dict()


class TestSaveLoadMemory:
    """Tests for save_memory / load_memory file operations."""

    def test_save_creates_file(self, tmp_path: Path) -> None:
        pt = PatternTable()
        pt.record("alice", "after_damage", "heal")
        filepath = tmp_path / "memory.json"

        save_memory(pt, path=str(filepath))

        assert filepath.exists()

    def test_save_json_is_indented(self, tmp_path: Path) -> None:
        pt = PatternTable()
        pt.record("alice", "after_damage", "heal")
        filepath = tmp_path / "memory.json"

        save_memory(pt, path=str(filepath))

        text = filepath.read_text()
        # Indented JSON has newlines and spaces
        assert "\n" in text
        assert "  " in text

    def test_save_creates_parent_dirs(self, tmp_path: Path) -> None:
        pt = PatternTable()
        pt.record("alice", "after_damage", "heal")
        filepath = tmp_path / "sub" / "dir" / "memory.json"

        save_memory(pt, path=str(filepath))

        assert filepath.exists()

    def test_load_returns_pattern_table(self, tmp_path: Path) -> None:
        pt = PatternTable()
        pt.record("alice", "after_damage", "heal")
        pt.record("alice", "after_damage", "heal")
        filepath = tmp_path / "memory.json"

        save_memory(pt, path=str(filepath))
        loaded = load_memory(path=str(filepath))

        assert isinstance(loaded, PatternTable)
        assert loaded.get_raw_counts("alice", "after_damage") == {"heal": 2}

    def test_load_missing_file_returns_empty(self, tmp_path: Path) -> None:
        filepath = tmp_path / "nonexistent.json"

        loaded = load_memory(path=str(filepath))

        assert isinstance(loaded, PatternTable)
        assert loaded.players() == set()
        assert loaded.to_dict() == {}

    def test_roundtrip_preserves_all_data(self, tmp_path: Path) -> None:
        pt = PatternTable()
        pt.record("alice", "after_damage", "heal")
        pt.record("alice", "after_damage", "attack")
        pt.record("alice", "at_range_1", "attack")
        pt.record("bob", "storm_closing", "flee")
        pt.record("bob", "below_30_hp", "heal")
        filepath = tmp_path / "memory.json"

        save_memory(pt, path=str(filepath))
        loaded = load_memory(path=str(filepath))

        assert loaded.to_dict() == pt.to_dict()
        assert loaded.players() == pt.players()

    def test_save_valid_json(self, tmp_path: Path) -> None:
        pt = PatternTable()
        pt.record("alice", "after_damage", "heal")
        filepath = tmp_path / "memory.json"

        save_memory(pt, path=str(filepath))

        # Should parse without error
        data = json.loads(filepath.read_text())
        assert isinstance(data, dict)

    def test_configurable_path(self, tmp_path: Path) -> None:
        pt = PatternTable()
        pt.record("alice", "after_damage", "heal")

        path_a = tmp_path / "a.json"
        path_b = tmp_path / "b.json"

        save_memory(pt, path=str(path_a))
        save_memory(pt, path=str(path_b))

        assert path_a.exists()
        assert path_b.exists()
