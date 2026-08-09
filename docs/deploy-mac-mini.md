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
| `NPCWARS_SERVICE_API_KEY` | _(unset)_ | Delegated-identity service key for the PSC relay. See below. |
| `NPCWARS_ALLOW_KEYLESS` | _(unset)_ | Dev-only: re-enables keyless auto-create on submit. **NEVER set in production.** |
| `HOST` | `0.0.0.0` | Bind address |
| `PORT` | `8000` | API port |

### Submission auth (UP-2)

`POST /api/submit-bot` and the lobby routes require an API key. A request with
no `X-API-Key` header is rejected with `401` — the old auto-create-a-player
behaviour only survives behind `NPCWARS_ALLOW_KEYLESS=1` (exact match; unset,
blank, `true`, `yes` are all treated as off). Do **not** set it on any host
reachable from the public tunnel.

**Delegated identity for the PSC relay.** Provision a single service key:

```bash
openssl rand -hex 32   # value for NPCWARS_SERVICE_API_KEY
```

Share it only with the PSC relay's Cloudflare Worker secret — never with an
end user or a browser. When a request authenticates with that key it must also
carry `X-Player-Ref: <opaque token>` (`[A-Za-z0-9_-]{8,128}`) naming the player
it acts for:

| Request | Result |
|---------|--------|
| service key + valid `X-Player-Ref` | accepted; same ref always resolves to the same player |
| service key, no/malformed `X-Player-Ref` | `400` — the service key must always act on behalf of a player |
| any other key (or none) + `X-Player-Ref` | `403` — delegation is never silently ignored |
| unknown key | `401` |

With `NPCWARS_SERVICE_API_KEY` unset, no key is a service key and any
`X-Player-Ref` is rejected with `403`.

The ref is an opaque token (PSC derives it via HMAC): it is stored only as a
SHA-256 hash in the `player_refs` table, is never logged, and never appears in
a player or bot display name.

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
