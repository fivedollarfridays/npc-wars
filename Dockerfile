# Two images, one shared base, so the docker CLI lands ONLY in the worker.
#
#   base   -- deps + source, shared layers (built once)
#   worker -- base + docker CLI; talks to the HOST daemon over the bind-mounted
#             /var/run/docker.sock to spawn the ephemeral sandbox container
#   app    -- base only; the internet-facing API, deliberately WITHOUT a docker
#             CLI and without the socket (see docker-compose.yml)
#
# `app` is intentionally the LAST stage so a bare `docker build .` still
# produces the API image. Compose names both targets explicitly.

FROM python:3.13-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir ".[server]"

COPY . .


FROM base AS worker

# Client binary only, extracted from Docker's static bundle: no daemon, no
# containerd, no apt repo. The target host is disk-constrained, and
# `apt-get install docker.io` would drag in a whole engine we never run.
ARG DOCKER_CLI_VERSION=27.5.1
RUN set -eux; \
    arch="$(uname -m)"; \
    curl -fsSL "https://download.docker.com/linux/static/stable/${arch}/docker-${DOCKER_CLI_VERSION}.tgz" \
      | tar -xzf - -C /usr/local/bin --strip-components=1 docker/docker; \
    chmod +x /usr/local/bin/docker; \
    docker --version

CMD ["python", "-m", "server.worker"]


FROM base AS app

EXPOSE 8000

CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
