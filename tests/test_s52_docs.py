"""Tests for S52 documentation updates — road-to-completion.md."""

from pathlib import Path


def test_roadmap_exists():
    assert Path("docs/road-to-completion.md").exists()


def test_roadmap_not_stale_phase3a():
    content = Path("docs/road-to-completion.md").read_text()
    assert "Phase 3A next" not in content
    assert "Phase 2 complete. Phase 3A next" not in content


def test_roadmap_reflects_current_state():
    content = Path("docs/road-to-completion.md").read_text()
    assert "S52" in content or "Sprint 52" in content


def test_roadmap_has_rival_system():
    content = Path("docs/road-to-completion.md").read_text()
    assert "Rival" in content or "rival" in content


def test_roadmap_sprint_count_updated():
    content = Path("docs/road-to-completion.md").read_text()
    # Should not say "39 sprints" anymore
    assert "39 sprints" not in content


def test_roadmap_has_updated_date():
    content = Path("docs/road-to-completion.md").read_text()
    # Should have a 2026-03 date, not the old one only
    assert "2026-03-2" in content  # Matches 2026-03-23 or 2026-03-26


def test_roadmap_phase3a_marked_done():
    content = Path("docs/road-to-completion.md").read_text()
    # Phase 3A should be marked as completed
    assert "Phase 3A" in content
    # Should contain a done/complete indicator near Phase 3A
    lower = content.lower()
    assert "phase 3a" in lower
    # Check for completion markers
    has_done = any(
        marker in content
        for marker in ["3A: Playable Product ✅", "3A ✅", "Phase 3A (Done)"]
    )
    assert has_done, "Phase 3A should be marked as done/complete"


def test_roadmap_phase3b_marked_done():
    content = Path("docs/road-to-completion.md").read_text()
    has_done = any(
        marker in content
        for marker in ["3B: Spectacle ✅", "3B ✅", "Phase 3B (Done)"]
    )
    assert has_done, "Phase 3B should be marked as done/complete"


def test_roadmap_phase4_reflects_reality():
    content = Path("docs/road-to-completion.md").read_text()
    # Phase 4 should NOT talk about Racing/SDK anymore
    assert "Code Circuit" not in content or "SDK Extraction" not in content
    # Should mention security hardening and launch readiness
    assert "Security" in content or "security" in content
    assert "Launch" in content or "launch" in content


def test_roadmap_phase5_training_wheels():
    content = Path("docs/road-to-completion.md").read_text()
    assert "Phase 5" in content
    assert "Training" in content or "training" in content


def test_roadmap_rival_tiers():
    content = Path("docs/road-to-completion.md").read_text()
    # Should mention at least some rival tiers
    assert "Bully" in content
    assert "Mirror" in content


def test_roadmap_no_old_sprint_count():
    content = Path("docs/road-to-completion.md").read_text()
    assert "12 sprints" not in content
    assert "14 sprints" not in content
    assert "11 sprints remaining" not in content


def test_roadmap_test_count_updated():
    content = Path("docs/road-to-completion.md").read_text()
    assert "3,600+ tests" not in content


def test_roadmap_has_pypi_row():
    content = Path("docs/road-to-completion.md").read_text()
    assert "PyPI" in content


def test_roadmap_has_security_row():
    content = Path("docs/road-to-completion.md").read_text()
    assert "Security Hardening" in content or "security hardening" in content
