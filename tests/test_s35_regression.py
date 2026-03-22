"""S35 balance regression -- equipment bots must be competitive but not dominant."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.equipment import EQUIPMENT_BUDGET, validate_equipment

RESULTS_PATH = Path(__file__).resolve().parent.parent / "tools" / "equipment_balance_results.json"

_HAS_RESULTS = RESULTS_PATH.exists()


# ── Equipment validation tests (always run) ────────────────────────


class TestBotEquipmentValid:
    """Every bot with BOT_EQUIPMENT must pass validation and budget."""

    @pytest.fixture()
    def _load_bot(self):
        """Helper to load a bot module by filename."""
        from engine.bot_scanner import load_bot_module

        def _load(filename: str):
            bot_path = Path(__file__).resolve().parent.parent / "bots" / filename
            return load_bot_module(str(bot_path), f"bot_{filename[:-3]}")

        return _load

    def test_reaper_equipment(self, _load_bot) -> None:
        mod = _load_bot("reaper.py")
        equip = getattr(mod, "BOT_EQUIPMENT", None)
        assert equip is not None, "reaper.py missing BOT_EQUIPMENT"
        ok, msg = validate_equipment(equip)
        assert ok, f"reaper.py invalid equipment: {msg}"

    def test_aggro_equipment(self, _load_bot) -> None:
        mod = _load_bot("example_aggro.py")
        equip = getattr(mod, "BOT_EQUIPMENT", None)
        assert equip is not None, "example_aggro.py missing BOT_EQUIPMENT"
        ok, msg = validate_equipment(equip)
        assert ok, f"example_aggro.py invalid equipment: {msg}"

    def test_tank_equipment(self, _load_bot) -> None:
        mod = _load_bot("example_tank.py")
        equip = getattr(mod, "BOT_EQUIPMENT", None)
        assert equip is not None, "example_tank.py missing BOT_EQUIPMENT"
        ok, msg = validate_equipment(equip)
        assert ok, f"example_tank.py invalid equipment: {msg}"

    def test_trapper_equipment(self, _load_bot) -> None:
        mod = _load_bot("example_trapper.py")
        equip = getattr(mod, "BOT_EQUIPMENT", None)
        assert equip is not None, "example_trapper.py missing BOT_EQUIPMENT"
        ok, msg = validate_equipment(equip)
        assert ok, f"example_trapper.py invalid equipment: {msg}"

    def test_kiter_equipment(self, _load_bot) -> None:
        mod = _load_bot("example_kiter.py")
        equip = getattr(mod, "BOT_EQUIPMENT", None)
        assert equip is not None, "example_kiter.py missing BOT_EQUIPMENT"
        ok, msg = validate_equipment(equip)
        assert ok, f"example_kiter.py invalid equipment: {msg}"

    def test_goose_equipment(self, _load_bot) -> None:
        mod = _load_bot("goose_loose.py")
        equip = getattr(mod, "BOT_EQUIPMENT", None)
        assert equip is not None, "goose_loose.py missing BOT_EQUIPMENT"
        ok, msg = validate_equipment(equip)
        assert ok, f"goose_loose.py invalid equipment: {msg}"

    def test_knight_equipment(self, _load_bot) -> None:
        mod = _load_bot("example_knight.py")
        equip = getattr(mod, "BOT_EQUIPMENT", None)
        assert equip is not None, "example_knight.py missing BOT_EQUIPMENT"
        ok, msg = validate_equipment(equip)
        assert ok, f"example_knight.py invalid equipment: {msg}"

    def test_all_under_budget(self, _load_bot) -> None:
        """Every bot with equipment must be at or under budget."""
        filenames = [
            "reaper.py", "example_aggro.py", "example_tank.py",
            "example_trapper.py", "example_kiter.py", "goose_loose.py",
            "example_knight.py",
        ]
        for fn in filenames:
            mod = _load_bot(fn)
            equip = getattr(mod, "BOT_EQUIPMENT", None)
            if equip is None:
                continue
            ok, msg = validate_equipment(equip)
            assert ok, f"{fn}: {msg}"
            # Extract cost from message like "Valid: 15/40 credits"
            cost = int(msg.split(":")[1].split("/")[0].strip())
            assert cost <= EQUIPMENT_BUDGET, f"{fn} over budget: {cost}"


# ── Balance regression tests (run only after sim) ──────────────────


@pytest.mark.skipif(not _HAS_RESULTS, reason="equipment_balance_results.json not generated")
class TestEquipmentBalance:
    """Verify equipment-equipped bots are balanced."""

    def test_no_bot_above_65_percent(self) -> None:
        data = json.loads(RESULTS_PATH.read_text())
        for name, stats in data.items():
            if name.startswith("_"):
                continue
            wr = stats["win_rate"]
            assert wr < 66.0, f"{name} win rate {wr}% exceeds 65% cap"

    def test_all_bots_have_games(self) -> None:
        data = json.loads(RESULTS_PATH.read_text())
        for name, stats in data.items():
            if name.startswith("_"):
                continue
            assert stats["total"] >= 20, f"{name} has too few games ({stats['total']})"
