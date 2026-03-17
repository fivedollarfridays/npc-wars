"""Tests for server.config Settings and Docker production config."""

from __future__ import annotations

from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestSettingsDefaults:
    """Settings should have sensible defaults when no env vars are set."""

    def test_redis_url_default(self) -> None:
        from server.config import Settings

        s = Settings()
        assert s.redis_url == "redis://localhost:6379"

    def test_results_dir_default(self) -> None:
        from server.config import Settings

        s = Settings()
        assert s.results_dir == "results"

    def test_db_path_default(self) -> None:
        from server.config import Settings

        s = Settings()
        assert s.db_path == "data/npcwars.db"

    def test_host_default(self) -> None:
        from server.config import Settings

        s = Settings()
        assert s.host == "0.0.0.0"

    def test_port_default(self) -> None:
        from server.config import Settings

        s = Settings()
        assert s.port == 8000
        assert isinstance(s.port, int)

    def test_cors_origins_default(self) -> None:
        from server.config import Settings

        s = Settings()
        assert "http://localhost:8000" in s.cors_origins
        assert "http://localhost:3000" in s.cors_origins


class TestSettingsFromEnv:
    """Settings should read from environment variables."""

    def test_settings_from_env(self, monkeypatch: object) -> None:
        monkeypatch.setenv("REDIS_URL", "redis://custom:6380")  # type: ignore[attr-defined]
        monkeypatch.setenv("RESULTS_DIR", "/tmp/results")  # type: ignore[attr-defined]
        monkeypatch.setenv("DB_PATH", "/tmp/npcwars.db")  # type: ignore[attr-defined]
        monkeypatch.setenv("HOST", "127.0.0.1")  # type: ignore[attr-defined]
        monkeypatch.setenv("PORT", "9000")  # type: ignore[attr-defined]
        monkeypatch.setenv("NPCWARS_CORS_ORIGINS", "https://example.com")  # type: ignore[attr-defined]

        from server.config import Settings

        s = Settings()
        assert s.redis_url == "redis://custom:6380"
        assert s.results_dir == "/tmp/results"
        assert s.db_path == "/tmp/npcwars.db"
        assert s.host == "127.0.0.1"
        assert s.port == 9000
        assert "https://example.com" in s.cors_origins


class TestSettingsRepr:
    """Settings repr should include key fields."""

    def test_repr_contains_key_fields(self) -> None:
        from server.config import Settings

        s = Settings()
        r = repr(s)
        assert "redis_url" in r
        assert "results_dir" in r
        assert "db_path" in r
        assert "port" in r


class TestDockerCompose:
    """Docker Compose production config validation."""

    def _load_compose(self) -> dict:
        compose_path = PROJECT_ROOT / "docker-compose.yml"
        assert compose_path.exists(), "docker-compose.yml must exist"
        return yaml.safe_load(compose_path.read_text())

    def test_docker_compose_exists_and_valid_yaml(self) -> None:
        data = self._load_compose()
        assert isinstance(data, dict)
        assert "services" in data

    def test_docker_compose_has_three_services(self) -> None:
        data = self._load_compose()
        services = data["services"]
        assert "app" in services
        assert "redis" in services
        assert "worker" in services

    def test_docker_compose_health_checks(self) -> None:
        data = self._load_compose()
        for name in ("app", "redis", "worker"):
            assert "healthcheck" in data["services"][name], f"{name} missing healthcheck"

    def test_docker_compose_volumes(self) -> None:
        data = self._load_compose()
        assert "volumes" in data, "Top-level volumes block required"
        assert "npcwars-data" in data["volumes"]

    def test_docker_compose_env_vars(self) -> None:
        data = self._load_compose()
        app_env = data["services"]["app"].get("environment", [])
        env_str = str(app_env)
        assert "REDIS_URL" in env_str
        assert "RESULTS_DIR" in env_str

    def test_docker_compose_redis_depends(self) -> None:
        data = self._load_compose()
        app_deps = data["services"]["app"].get("depends_on", {})
        assert "redis" in app_deps or "redis" in str(app_deps)


class TestDockerfile:
    """Main Dockerfile validation."""

    def test_dockerfile_exists(self) -> None:
        dockerfile = PROJECT_ROOT / "Dockerfile"
        assert dockerfile.exists(), "Dockerfile must exist"

    def test_dockerfile_exposes_port(self) -> None:
        dockerfile = PROJECT_ROOT / "Dockerfile"
        content = dockerfile.read_text()
        assert "EXPOSE" in content
        assert "8000" in content

    def test_dockerfile_has_cmd(self) -> None:
        dockerfile = PROJECT_ROOT / "Dockerfile"
        content = dockerfile.read_text()
        assert "CMD" in content
        assert "uvicorn" in content
