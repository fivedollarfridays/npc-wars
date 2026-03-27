"""T56.5: Type safety and config consistency tests."""

from pathlib import Path


class TestSubmitTypeSafety:
    """submit.py should have no type: ignore[return-value] suppressions."""

    def test_submit_no_type_ignore_return(self) -> None:
        """submit.py should not have type: ignore[return-value]."""
        source = Path("server/routes/submit.py").read_text()
        assert "type: ignore[return-value]" not in source

    def test_submit_compiles(self) -> None:
        """submit.py should compile without errors."""
        source = Path("server/routes/submit.py").read_text()
        compile(source, "submit.py", "exec")


class TestDbPathConsistency:
    """DB_PATH defaults should be consistent across modules."""

    def test_db_path_defaults_match(self) -> None:
        """app.py and config.py should use the same DB_PATH default."""
        app_source = Path("server/app.py").read_text()
        config_source = Path("server/config.py").read_text()
        # Both should default to data/npcwars.db
        assert "data/npcwars.db" in app_source
        assert "data/npcwars.db" in config_source
