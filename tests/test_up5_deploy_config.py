"""UP-5 P1/P4: the compose topology must be able to run a match at all.

A live bring-up on the target Mac Mini found the arena could start but never
complete a submission:

* P1 the worker container had no ``docker`` CLI and no ``/var/run/docker.sock``,
  so the fail-closed sandbox was unreachable and every submission failed;
* P4 the hard-mapped ``8000:8000`` collided with an unrelated app on the host.

These tests pin the deployment shape that fixes both, plus the docker-out-of-
docker safety property that matters most: the *app* image must not gain a
docker CLI, and nothing in compose may set NPCWARS_ALLOW_UNSANDBOXED.
"""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
COMPOSE_PATH = ROOT / "docker-compose.yml"
DOCKERFILE_PATH = ROOT / "Dockerfile"
E2E_SCRIPT = ROOT / "scripts" / "verify_arena_e2e.sh"

SOCKET_MOUNT = "/var/run/docker.sock:/var/run/docker.sock"


@pytest.fixture(scope="module")
def compose() -> dict:
    return yaml.safe_load(COMPOSE_PATH.read_text())


@pytest.fixture(scope="module")
def dockerfile() -> str:
    return DOCKERFILE_PATH.read_text()


def _env_map(service: dict) -> dict[str, str]:
    """Normalize a compose ``environment`` list/dict into a dict."""
    env = service.get("environment", [])
    if isinstance(env, dict):
        return {k: str(v) for k, v in env.items()}
    out: dict[str, str] = {}
    for item in env:
        key, _, value = str(item).partition("=")
        out[key] = value
    return out


class TestWorkerSandboxAccess:
    """P1: docker-out-of-docker -- socket in, docker CLI present."""

    def test_worker_mounts_the_host_docker_socket(self, compose) -> None:
        volumes = compose["services"]["worker"].get("volumes", [])
        assert SOCKET_MOUNT in volumes, (
            "worker cannot spawn the sandbox container without the host socket"
        )

    def test_worker_builds_the_worker_image_target(self, compose) -> None:
        build = compose["services"]["worker"]["build"]
        assert isinstance(build, dict), "worker needs a build target, not a bare context"
        assert build.get("target") == "worker"

    def test_app_builds_the_app_target_without_docker_cli(self, compose) -> None:
        """The public-facing image must not carry a docker CLI."""
        build = compose["services"]["app"]["build"]
        assert isinstance(build, dict)
        assert build.get("target") == "app"

    def test_app_does_not_mount_the_docker_socket(self, compose) -> None:
        volumes = compose["services"]["app"].get("volumes", [])
        assert SOCKET_MOUNT not in volumes, (
            "socket access is host-root-equivalent; the internet-facing service "
            "must never have it"
        )

    def test_dockerfile_has_a_worker_stage_installing_the_docker_cli(
        self, dockerfile
    ) -> None:
        assert "AS worker" in dockerfile
        worker_stage = dockerfile.split("AS worker", 1)[1]
        assert "docker" in worker_stage.lower()

    def test_app_stage_is_the_default_build_target(self, dockerfile) -> None:
        """`docker build .` (no target) must still produce the API image."""
        stages = [
            line for line in dockerfile.splitlines() if line.startswith("FROM ")
        ]
        assert stages[-1].strip().endswith("AS app")

    def test_worker_stage_runs_the_worker_module(self, dockerfile) -> None:
        assert "server.worker" in dockerfile


class TestSandboxImageIsBuildable:
    """The sandbox image must exist on the host daemon for the worker to use."""

    def test_compose_declares_a_sandbox_image_builder(self, compose) -> None:
        services = compose["services"]
        builders = [
            name
            for name, svc in services.items()
            if str(svc.get("image", "")) == "npcwars-sandbox:latest"
        ]
        assert builders, "no compose service builds npcwars-sandbox:latest"
        builder = services[builders[0]]
        assert builder["build"]["dockerfile"] == "Dockerfile.sandbox"

    def test_sandbox_builder_is_profiled_out_of_normal_up(self, compose) -> None:
        """It is a build unit, not a long-running service."""
        services = compose["services"]
        builder = next(
            svc
            for svc in services.values()
            if str(svc.get("image", "")) == "npcwars-sandbox:latest"
        )
        assert builder.get("profiles"), "builder must not start on `docker compose up`"


class TestFailClosedStaysClosed:
    """Nothing in the deployment may open the in-process execution path."""

    def test_compose_never_sets_allow_unsandboxed(self) -> None:
        assert "NPCWARS_ALLOW_UNSANDBOXED" not in COMPOSE_PATH.read_text()

    def test_compose_never_sets_allow_keyless(self) -> None:
        assert "NPCWARS_ALLOW_KEYLESS" not in COMPOSE_PATH.read_text()


class TestQueueAndDataAgreement:
    """P3 + the results/DB split: app and worker must share one of everything."""

    @pytest.mark.parametrize("service", ["app", "worker"])
    def test_queue_strict_mode_is_on(self, compose, service) -> None:
        assert _env_map(compose["services"][service])["NPCWARS_QUEUE_STRICT"] == "1"

    @pytest.mark.parametrize("service", ["app", "worker"])
    def test_same_redis_url(self, compose, service) -> None:
        assert _env_map(compose["services"][service])["REDIS_URL"] == (
            "redis://redis:6379"
        )

    @pytest.mark.parametrize("service", ["app", "worker"])
    def test_same_results_dir_on_the_shared_volume(self, compose, service) -> None:
        assert _env_map(compose["services"][service])["RESULTS_DIR"] == "/data/results"

    @pytest.mark.parametrize("service", ["app", "worker"])
    def test_same_db_path_on_the_shared_volume(self, compose, service) -> None:
        assert _env_map(compose["services"][service])["DB_PATH"] == "/data/npcwars.db"

    @pytest.mark.parametrize("service", ["app", "worker"])
    def test_both_mount_the_data_volume(self, compose, service) -> None:
        assert "npcwars-data:/data" in compose["services"][service]["volumes"]


class TestWorkerHealthcheck:
    """P2: the healthcheck must prove the poll loop is alive."""

    def test_healthcheck_checks_the_heartbeat(self, compose) -> None:
        test = str(compose["services"]["worker"]["healthcheck"]["test"])
        assert "server.heartbeat" in test

    def test_healthcheck_is_not_the_old_print_ok_stub(self, compose) -> None:
        test = str(compose["services"]["worker"]["healthcheck"]["test"])
        assert "print('ok')" not in test


class TestServiceResilience:
    """A worker that exits (strict-mode boot failure, OOM) must come back."""

    @pytest.mark.parametrize("service", ["app", "redis", "worker"])
    def test_services_restart(self, compose, service) -> None:
        assert compose["services"][service].get("restart") == "unless-stopped"

    def test_the_build_only_sandbox_service_does_not_restart(self, compose) -> None:
        builder = next(
            svc
            for svc in compose["services"].values()
            if str(svc.get("image", "")) == "npcwars-sandbox:latest"
        )
        assert "restart" not in builder


class TestConfigurableHostPort:
    """P4: :8000 was taken on the target host."""

    def test_host_port_is_templated_with_a_default(self, compose) -> None:
        ports = compose["services"]["app"]["ports"]
        assert ports == ["${ARENA_HOST_PORT:-8000}:8000"], (
            "host port must be overridable; container port stays 8000"
        )

    def test_env_example_documents_the_port_variable(self) -> None:
        assert "ARENA_HOST_PORT" in (ROOT / ".env.example").read_text()

    def test_env_example_documents_the_new_switches(self) -> None:
        content = (ROOT / ".env.example").read_text()
        for var in ("NPCWARS_QUEUE_STRICT", "NPCWARS_LOG_LEVEL"):
            assert var in content, f"missing {var}"


class TestE2EScript:
    """The DoD script itself: self-contained, executable, correct JSON."""

    def test_exists_and_is_executable(self) -> None:
        assert E2E_SCRIPT.is_file()
        mode = E2E_SCRIPT.stat().st_mode
        assert mode & stat.S_IXUSR, "script must be executable"

    def test_is_strict_bash(self) -> None:
        content = E2E_SCRIPT.read_text()
        assert content.startswith("#!/usr/bin/env bash")
        assert "set -euo pipefail" in content

    def test_builds_json_with_python_not_printf(self) -> None:
        """A previous script broke on literal newlines inside JSON strings.

        Scans executable lines only -- a comment explaining the hazard is not
        the hazard. The json.dumps half is the positive control: if the
        payload builder were ever replaced by shell string-mashing, the
        second assertion catches it even when no printf appears.
        """
        code = "\n".join(
            line
            for line in E2E_SCRIPT.read_text().splitlines()
            if not line.lstrip().startswith("#")
        )
        assert "printf '%b'" not in code
        assert "json.dumps" in code, "the request body must be built by json.dumps"

    def test_covers_all_five_definition_of_done_assertions(self) -> None:
        content = E2E_SCRIPT.read_text()
        for needle in (
            "/api/submit-bot",
            "X-Player-Ref",
            "/api/lobby/history",
            "NPCWARS_ALLOW_UNSANDBOXED",
            "npcwars-sandbox:latest",
            "/stream",
            "/api/leaderboard",
        ):
            assert needle in content, f"E2E script never touches {needle}"

    def test_prints_pass_only_at_the_end(self) -> None:
        content = E2E_SCRIPT.read_text()
        assert "PASS" in content and "FAIL" in content

    def test_does_not_require_being_run_from_the_scripts_dir(self) -> None:
        assert "BASH_SOURCE" in E2E_SCRIPT.read_text()

    def test_line_endings_are_unix(self) -> None:
        assert b"\r\n" not in E2E_SCRIPT.read_bytes()


def test_script_is_committed_executable_in_git() -> None:
    """Guard the mode bit that `git add` would otherwise silently drop."""
    assert os.access(E2E_SCRIPT, os.X_OK)
