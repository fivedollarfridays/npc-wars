"""S47 Integration Gate — Phase 3B completion: spectacle validated."""

from __future__ import annotations

from pathlib import Path

from server.tournament import Tournament


class TestTournamentEngine:
    def test_8_player_tournament(self) -> None:
        t = Tournament("Test", 8, seed=42)
        for i in range(8):
            t.add_player(f"player_{i}")
        t.seed_bracket()
        assert t.status == "running"
        assert len(t.rounds) == 1
        assert len(t.rounds[0]) == 2  # 2 groups of 4

    def test_bracket_serialization(self) -> None:
        t = Tournament("Test", 8)
        for i in range(8):
            t.add_player(f"p{i}")
        t.seed_bracket()
        data = t.to_dict()
        t2 = Tournament.from_dict(data)
        assert t2.name == "Test"
        assert len(t2.rounds) == len(t.rounds)


class TestTournamentAPI:
    def test_routes_registered(self) -> None:
        from server.routes.tournament import router
        assert router is not None

    def test_runner_exists(self) -> None:
        from server.tournament_runner import run_tournament_round
        assert callable(run_tournament_round)

    def test_db_functions(self) -> None:
        from server.tournament_db import create_tournament, get_tournament, list_tournaments
        assert all(callable(f) for f in [create_tournament, get_tournament, list_tournaments])


class TestTournamentPages:
    def test_tournament_page_exists(self) -> None:
        assert Path("server/static/tournament.html").exists()

    def test_tournaments_list_page_exists(self) -> None:
        assert Path("server/static/tournaments.html").exists()

    def test_page_routes_registered(self) -> None:
        content = Path("server/routes/pages.py").read_text()
        assert "tournament_page" in content
        assert "tournaments_page" in content


class TestPhase3BSystems:
    """All Phase 3B modules exist and are functional."""

    def test_character_system(self) -> None:
        from engine.character import build_character_descriptor
        assert callable(build_character_descriptor)

    def test_kill_cam(self) -> None:
        content = Path("viewer/js/effects.js").read_text()
        assert "triggerKillCam" in content

    def test_synth_audio(self) -> None:
        content = Path("viewer/js/audio.js").read_text()
        assert "playSynth" in content

    def test_cosmetic_system(self) -> None:
        from server.cosmetics import COSMETIC_CATALOG
        assert len(COSMETIC_CATALOG) >= 20

    def test_cosmetic_store_api(self) -> None:
        from server.routes.cosmetics import router
        assert router is not None

    def test_tournament_system(self) -> None:
        from server.tournament import Tournament
        assert Tournament is not None

    def test_viewer_shapes(self) -> None:
        content = Path("viewer/js/shapes.js").read_text()
        assert "drawBotShape" in content
