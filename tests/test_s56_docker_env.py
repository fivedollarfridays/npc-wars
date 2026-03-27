"""Tests for T56.2: .dockerignore and .env.example files."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class TestDockerignore:
    """Verify .dockerignore exists and excludes non-runtime paths."""

    def test_exists(self):
        assert (ROOT / ".dockerignore").exists()

    def test_excludes_git(self):
        content = (ROOT / ".dockerignore").read_text()
        assert ".git" in content.splitlines()

    def test_excludes_tests(self):
        content = (ROOT / ".dockerignore").read_text()
        assert "tests" in content.splitlines()

    def test_excludes_pycache(self):
        content = (ROOT / ".dockerignore").read_text()
        assert "__pycache__" in content.splitlines()

    def test_excludes_env_files(self):
        content = (ROOT / ".dockerignore").read_text()
        lines = content.splitlines()
        assert ".env" in lines
        assert ".env.*" in lines

    def test_excludes_docs(self):
        content = (ROOT / ".dockerignore").read_text()
        assert "docs" in content.splitlines()


class TestEnvExample:
    """Verify .env.example exists with all required variables."""

    def test_exists(self):
        assert (ROOT / ".env.example").exists()

    def test_has_all_required_vars(self):
        content = (ROOT / ".env.example").read_text()
        required = [
            "DB_PATH",
            "HOST",
            "PORT",
            "REDIS_URL",
            "NPCWARS_CORS_ORIGINS",
            "NPCWARS_SECURE_COOKIES",
            "RESULTS_DIR",
        ]
        for var in required:
            assert var in content, f"Missing {var}"

    def test_has_default_values(self):
        content = (ROOT / ".env.example").read_text()
        assert "DB_PATH=" in content
        assert "PORT=" in content

    def test_has_comments(self):
        content = (ROOT / ".env.example").read_text()
        comment_lines = [l for l in content.splitlines() if l.startswith("#")]
        assert len(comment_lines) >= 3, "Expected at least 3 comment lines"
