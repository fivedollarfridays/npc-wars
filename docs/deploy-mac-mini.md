# NPC Wars Deploy Guide -- Mac Mini M4

## Prerequisites

- Docker Desktop for macOS (Apple Silicon)
- Git

## Quick Start

```bash
git clone https://github.com/fivedollarfridays/npc-wars.git
cd npc-wars

# 1. Pick a host port if 8000 is taken, and provision the service key
cp .env.example .env
echo "ARENA_HOST_PORT=8010" >> .env
echo "NPCWARS_SERVICE_API_KEY=$(openssl rand -hex 32)" >> .env

# 2. Build the sandbox image on the HOST daemon (REQUIRED -- see below)
docker compose --profile tools build sandbox

# 3. Bring the stack up
docker compose up -d --build

# 4. Prove the whole loop actually works
NPCWARS_SERVICE_API_KEY=<the key from .env> scripts/verify_arena_e2e.sh
```

The server is now running at `http://localhost:${ARENA_HOST_PORT}`.

## Services

| Service | Port | Description |
|---------|------|-------------|
| app     | `${ARENA_HOST_PORT:-8000}` -> 8000 | FastAPI web server (image target `app`) |
| redis   | 6379 | Match queue broker |
| worker  | --   | Background match processor (image target `worker`) |
| sandbox | --   | Build-only unit (profile `tools`) for `npcwars-sandbox:latest` |

### Host port (`ARENA_HOST_PORT`)

The app publishes `"${ARENA_HOST_PORT:-8000}:8000"`. The **container** port is
always 8000; only the host side moves. The default is unchanged (8000), so
existing deployments are unaffected — set `ARENA_HOST_PORT` in `.env` when
something else already owns the port (on the Mac Mini, :8000 belongs to an
unrelated app, so use 8010).

Everything that talks to the arena — `scripts/verify_arena_e2e.sh`, the PSC
relay, the tunnel — must use the same port. The verify script reads
`ARENA_HOST_PORT` (or a full `ARENA_URL`) from the environment.

## Worker sandbox access (docker-out-of-docker)

The worker executes untrusted submitted bot source by shelling out to
`docker run ... npcwars-sandbox:latest` (`server/docker_sandbox.py`). For that
to work inside a container it needs two things, both wired in
`docker-compose.yml`:

1. **A docker CLI.** The `worker` stage of the `Dockerfile` extracts just the
   client binary from Docker's static bundle (no daemon, no containerd — the
   target host is disk-constrained). The `app` stage deliberately does **not**
   get it.
2. **The host docker socket**, bind-mounted read-write:
   `/var/run/docker.sock:/var/run/docker.sock`. The worker therefore drives the
   *host* daemon, and the sandbox container is a sibling of the worker rather
   than a child.

> **Residual risk — read this before exposing the host.**
> Access to `/var/run/docker.sock` is **equivalent to root on the host**: any
> code that runs in the worker container can start a privileged container with
> the host filesystem mounted. This is an accepted trade for keeping the arena
> in a single `docker compose up`. It is tolerable only because of what the
> worker runs: first-party code. Untrusted submitted bot source never executes
> in the worker — it executes in the container the worker spawns, with
> `--network=none --read-only --memory=256m --cpus=1 --pids-limit=50`. The
> internet-facing `app` service has **no** socket mount and no docker CLI, so a
> compromise of the public surface does not directly hand over the daemon.
> If that trade ever stops being acceptable, the alternative is a socket proxy
> restricted to `container create/start/wait/logs/rm` on this one image, or a
> worker running on the host outside compose.

Verify the wiring from inside the worker (this single command proves the CLI,
the socket, and the image all at once):

```bash
docker compose exec worker docker image inspect npcwars-sandbox:latest
```

The worker also runs this as a startup preflight and logs the result:

```
Sandbox preflight OK: docker daemon reachable, image npcwars-sandbox:latest present
```

or, when it is broken, one unmistakable line instead of one opaque error per
job:

```
Sandbox preflight FAILED (docker=False image=False, image npcwars-sandbox:latest): ...
```

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
| `ARENA_HOST_PORT` | `8000` | **Host** port the app is published on (container stays 8000) |
| `NPCWARS_QUEUE_STRICT` | `1` in compose | Require Redis; never fall back to an in-process queue. See below. |
| `NPCWARS_LOG_LEVEL` | `INFO` | Log level for both the app and the worker |
| `NPCWARS_WORKER_HEARTBEAT` | `/tmp/npcwars-worker.heartbeat` | Worker liveness file the healthcheck reads |
| `NPCWARS_WORKER_HEARTBEAT_MAX_AGE` | `60` | Seconds before a heartbeat counts as dead |
| `NPCWARS_ALLOW_UNSANDBOXED` | *(unset)* | **Never set this in production.** See below. |

`RESULTS_DIR` and `DB_PATH` must be **identical for `app` and `worker`** and
must point into the shared `npcwars-data` volume (`/data/...`). They are
container-local paths otherwise: before UP-5 the app ignored `RESULTS_DIR`
entirely and read `./results` inside its own container, so a match the worker
had genuinely written was invisible to `/api/match/{id}` and the leaderboard.

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

### Build the sandbox image (REQUIRED for bring-up)

The fail-closed gate above is only *real* if the `npcwars-sandbox:latest`
image actually exists and runs matches. Build it as part of bring-up — it is a
compose service under the `tools` profile, so it never *starts*, it only
builds:

```bash
docker compose --profile tools build sandbox
```

It must be built on the **host** daemon, which is what the command above does
and is exactly the daemon the worker reaches through the mounted socket. The
equivalent plain-docker form is:

```bash
docker build -f Dockerfile.sandbox -t npcwars-sandbox:latest .
```

The image is deliberately minimal: the engine is stdlib-only
(`pyproject` `dependencies = []`), so there is **no `pip install`** — it copies
only `engine/`, `data/`, and the `sandbox_entry.py` entrypoint. `sandbox_entry.py`
reads a `{"bots":[...], "config":{...}}` payload on stdin, compiles each bot
with `engine.bot_loader.load_bot_from_source`, runs a real match via
`engine.game.run_match`, and prints the match JSON to stdout — which is exactly
the contract `server/docker_sandbox.py::_run_in_docker` expects.

> Before UP-4 this image failed to build (it copied a since-renamed `npcwars/`
> dir) and its `CMD` was a stub that ignored stdin and returned
> `{"status": "sandbox_ok"}` instead of a match. The Docker path had never run
> a real match.

**If the image is missing, submission matches fail closed** with
`SandboxUnavailableError` (production leaves `NPCWARS_ALLOW_UNSANDBOXED` unset),
so building the image is what makes safe production execution possible. Verify
the built image on a Docker host with:

```bash
scripts/verify_sandbox_container.sh
```

It builds the image, pipes a real 3-bot payload through the container, and
asserts the output is a genuine match (winner + rounds) and not the old
`sandbox_ok` stub — printing a clear `PASS`/`FAIL`.

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

### Submission matches (UP-3)

`POST /api/submit-bot` now enqueues a real match, not just a cosmetic
`job_id`. Jobs on the match queue carry a `kind` discriminator:

| `kind` | Executor | Bot payload | Source |
|--------|----------|-------------|--------|
| `"submission"` | `run_sandboxed()` | untrusted SOURCE strings | player submissions |
| _(absent)_ | `run_match()` | pre-compiled `decide_func` configs | lobby / tournament |

The **worker** routes on `kind`. A submission job runs the submitter's stored
source plus AI fill-opponent sources through the fail-closed sandbox, writes a
normal `match_NNN.json` (so SSE replay, `/m/{id}` share, and the ladder pick it
up unchanged), binds the match to the submitting player in `match_players`
(discoverable via `GET /api/lobby/history`), and credits the submitter's
coins. There is **no new queue, port, or env var** — the same `redis` + single
`worker` service handle both job kinds.

Operational note: submission matches depend on the sandbox, so they obey the
`NPCWARS_ALLOW_UNSANDBOXED` gate above. In production (Docker present, variable
unset) they run in the container; if the sandbox is unavailable the job is
logged and marked failed (`Submission job … FAILED closed`) with **no match
file written** — the worker loop keeps running. Because the worker allocates
each submission's `match_id` from the results directory at run time, keep a
**single** worker replica (the default compose topology) to avoid id races.

## Data Persistence

Match results and the database are stored in a Docker named volume `npcwars-data` mounted at `/data`.

```bash
# Inspect volume
docker volume inspect npc-wars_npcwars-data

# Back up data
docker run --rm -v npc-wars_npcwars-data:/data -v $(pwd):/backup alpine \
  tar czf /backup/npcwars-backup.tar.gz -C /data .
```

## Queue integrity (`NPCWARS_QUEUE_STRICT`)

`server/queue.py` falls back to an in-process `InMemoryQueue` when Redis is
unreachable. That is fine for a single-process dev run and for the test suite.
In compose it is a silent data-loss shape: the **app** would enqueue into its
own container's memory and the **worker** would poll its own, so submissions
return `202` and no match ever runs, with no error anywhere.

Compose therefore sets `NPCWARS_QUEUE_STRICT=1` on both `app` and `worker`.
With it on, an unreachable Redis raises `QueueBackendUnavailableError` instead
of falling back — the app fails to boot, the worker logs it loudly. The gate
is an exact match on `"1"`, same convention as the sandbox and keyless gates.

Both processes log which backend they got at startup, so a split brain is
visible in the first lines of each container's logs:

```
server.queue: Queue backend ready: redis (strict=True, key=npcwars:match_queue)
```

## Worker logs and liveness

**Reading worker logs.** The worker configures the root logger to stdout at
`NPCWARS_LOG_LEVEL` (default `INFO`) on startup — before UP-5 it never called
`logging.basicConfig`, so `docker compose logs worker` was empty even with
`PYTHONUNBUFFERED=1`.

```bash
docker compose logs -f worker          # follow
docker compose logs --tail=200 worker  # recent
NPCWARS_LOG_LEVEL=DEBUG docker compose up -d worker
```

A healthy worker prints, in order: its DB path, its heartbeat file, its queue
backend, its sandbox preflight, then `Worker started, polling queue...`, then
one `Submission match N completed for player ...` per submission.

**Liveness.** The healthcheck is `python -m server.heartbeat`, not the old
`python -c "print('ok')"` — that stub reported `Up (healthy)` during a live
bring-up while the poll loop was not running at all. The loop now touches
`NPCWARS_WORKER_HEARTBEAT` every cycle (including idle cycles) and the
healthcheck exits non-zero once that file is missing or older than
`NPCWARS_WORKER_HEARTBEAT_MAX_AGE` (60s), so a stalled loop turns the
container **unhealthy**.

The loop also log-and-continues: a poisoned job or a transient queue error is
logged with a traceback and the worker keeps polling, and any unhandled
exception is logged before the process exits.

```bash
docker compose ps                                   # worker must be (healthy)
docker compose exec worker python -m server.heartbeat  # prints the age
```

## Verifying the whole loop (`scripts/verify_arena_e2e.sh`)

Health checks prove the containers are up; they do not prove a bot can be
submitted and come back as a replay. This script does, against a running
stack:

```bash
NPCWARS_SERVICE_API_KEY=<service key> scripts/verify_arena_e2e.sh
```

It prints `PASS` only if **all five** hold:

1. a bot submits through the UP-2 delegated contract (service key +
   `X-Player-Ref`) and gets `202` + a `job_id`;
2. the worker produces a match within a bounded wait (`ARENA_WAIT_SECS`,
   default 180s);
3. the match ran **through the Docker sandbox** — asserted by proving
   `NPCWARS_ALLOW_UNSANDBOXED` is unset *inside the worker* (so the in-process
   path is impossible), that the worker reaches `npcwars-sandbox:latest`
   through the mounted socket, and that the worker logged the submission
   completing with no `FAILED closed`;
4. the match is readable by its natural id at `/api/match/{id}` **and**
   `/api/match/{id}/stream`;
5. the submitter appears on `/api/leaderboard`.

On failure it prints `FAIL: <reason>` plus the last 40 lines of the worker log
and exits non-zero. Knobs: `ARENA_HOST_PORT`, `ARENA_URL`,
`ARENA_WORKER_SERVICE`, `ARENA_APP_SERVICE`, `ARENA_WAIT_SECS`,
`DOCKER_COMPOSE`. It mints a fresh `X-Player-Ref` per run, so back-to-back
runs do not trip the 1-submission-per-30s rate limit.

The application-side contracts it depends on are also pinned by
`tests/test_up5_arena_e2e_contract.py`, which rehearses the same five steps
in-process (real queue, real worker, real match) so drift fails in CI rather
than on the host.

## Health Checks

```bash
# App health (use your ARENA_HOST_PORT)
curl http://localhost:8010/health

# Redis health
docker compose exec redis redis-cli ping

# All service status
docker compose ps
```

## Updating

```bash
git pull
docker compose build                          # app + worker
docker compose --profile tools build sandbox  # rebuild the sandbox image too
docker compose up -d
NPCWARS_SERVICE_API_KEY=<service key> scripts/verify_arena_e2e.sh
```

Rebuild the sandbox image whenever `engine/`, `data/` or `sandbox_entry.py`
changes: `docker compose build` alone skips it (it is behind the `tools`
profile), and the worker would keep running matches with stale engine code.

## Stopping

```bash
docker compose down        # Stop services, keep data
docker compose down -v     # Stop services and delete data volumes
```
