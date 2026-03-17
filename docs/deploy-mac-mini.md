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
