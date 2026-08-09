# NPC Wars Deploy Guide -- Mac Mini M4

## Prerequisites

- Docker Desktop for macOS (Apple Silicon)
- Git

## Quick Start

```bash
git clone https://github.com/fivedollarfridays/npc-wars.git
cd npc-wars
docker compose up -d
```

The server is now running at `http://localhost:8000`.

## Services

| Service | Port | Description |
|---------|------|-------------|
| app     | 8000 | FastAPI web server |
| redis   | 6379 | Match queue broker |
| worker  | --   | Background match processor |

## Environment Variables

Configure via `docker-compose.yml` environment block or a `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://redis:6379` | Redis connection URL |
| `RESULTS_DIR` | `/data/results` | Match results directory |
| `DB_PATH` | `/data/npcwars.db` | SQLite database path |
| `NPCWARS_CORS_ORIGINS` | `*` | Allowed CORS origins (comma-separated) |
| `HOST` | `0.0.0.0` | Bind address |
| `PORT` | `8000` | API port |
| `NPCWARS_ALLOW_UNSANDBOXED` | *(unset)* | **Never set this in production.** See below. |

### `NPCWARS_ALLOW_UNSANDBOXED` -- the fail-closed sandbox gate (UP-1)

Submitted bot source is arbitrary user Python. `server/docker_sandbox.py`
runs it in an ephemeral, network-less Docker container. If the Docker daemon
or the `npcwars-sandbox:latest` image is missing, `run_sandboxed()` **fails
closed**: it raises `SandboxUnavailableError` and the match/job fails. It
does *not* silently fall back to running the submission inside the API or
worker process.

The in-process fallback exists only for local development and CI, and runs
only when this variable is set to exactly `1`. The check is an exact-match
allow-list -- `true`, `yes`, `on`, `0`, blank, or any other value all mean
"not allowed", so a typo or a truthy-looking value cannot open the hole.

- **Production / deploy: leave it unset.** Do not add it to
  `docker-compose.yml`, `.env`, or any launchd/systemd unit.
- If matches start failing with `SandboxUnavailableError`, fix Docker
  (`docker compose ps`, rebuild the sandbox image from `Dockerfile.sandbox`)
  -- do not set this variable to work around it.
- This gate is what PSC's public arena exposure depends on. Setting it on a
  publicly reachable host means arbitrary submitted code executes in the API
  process.

Regression coverage: `tests/test_sandbox_fail_closed.py`.

## Data Persistence

Match results and the database are stored in a Docker named volume `npcwars-data` mounted at `/data`.

```bash
# Inspect volume
docker volume inspect npc-wars_npcwars-data

# Back up data
docker run --rm -v npc-wars_npcwars-data:/data -v $(pwd):/backup alpine \
  tar czf /backup/npcwars-backup.tar.gz -C /data .
```

## Health Checks

```bash
# App health
curl http://localhost:8000/health

# Redis health
docker compose exec redis redis-cli ping

# All service status
docker compose ps
```

## Updating

```bash
git pull
docker compose build
docker compose up -d
```

## Stopping

```bash
docker compose down        # Stop services, keep data
docker compose down -v     # Stop services and delete data volumes
```
