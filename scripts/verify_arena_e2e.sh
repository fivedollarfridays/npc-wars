#!/usr/bin/env bash
# End-to-end proof that the containerized arena can actually run a submission.
#
# Run this ON THE DOCKER HOST, against a running stack:
#
#   docker compose --profile tools build sandbox   # sandbox image on the host daemon
#   docker compose up -d --build
#   NPCWARS_SERVICE_API_KEY=<the service key> scripts/verify_arena_e2e.sh
#
# It asserts, in order, and prints PASS only if ALL of them hold:
#   1. a bot submits through the UP-2 delegated contract (service key +
#      X-Player-Ref) and gets 202 + job_id;
#   2. the worker produces a match within a bounded wait;
#   3. that match ran THROUGH THE DOCKER SANDBOX, not the in-process path;
#   4. the match is readable by its natural id at /api/match/{id} AND
#      /api/match/{id}/stream (UP-3 replay resolution);
#   5. the submitter appears on /api/leaderboard.
#
# How (3) is proven, since "it ran" alone would not distinguish the paths:
#   * the worker container is asserted to have NPCWARS_ALLOW_UNSANDBOXED unset,
#     and server/docker_sandbox.py::run_sandboxed refuses the in-process
#     fallback unless that variable is exactly "1" -- so an in-process run is
#     impossible in this container;
#   * the worker is asserted to reach the sandbox image through its mounted
#     /var/run/docker.sock (docker image inspect npcwars-sandbox:latest, run
#     INSIDE the worker);
#   * the worker logs are asserted to show the submission completing with no
#     "FAILED closed".
#   A completed submission under those three conditions can only have executed
#   in the sandbox container.
#
# Env knobs (all optional except the service key):
#   NPCWARS_SERVICE_API_KEY  required -- the provisioned service key
#   ARENA_HOST_PORT          host port the app is published on (default 8000)
#   ARENA_URL                full base URL (default http://localhost:$ARENA_HOST_PORT)
#   ARENA_WORKER_SERVICE     compose service name for the worker (default worker)
#   ARENA_APP_SERVICE        compose service name for the API (default app)
#   ARENA_WAIT_SECS          bounded wait for the match (default 180)
#   DOCKER_COMPOSE           compose command (default "docker compose")
set -euo pipefail

# Repo root = parent of this script's dir, so it works from anywhere.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

: "${ARENA_HOST_PORT:=8000}"
: "${ARENA_URL:=http://localhost:${ARENA_HOST_PORT}}"
: "${ARENA_WORKER_SERVICE:=worker}"
: "${ARENA_APP_SERVICE:=app}"
: "${ARENA_WAIT_SECS:=180}"
: "${DOCKER_COMPOSE:=docker compose}"

SANDBOX_IMAGE="npcwars-sandbox:latest"
STEP=0

ok() { echo "   ok  -- $*"; }
step() { STEP=$((STEP + 1)); echo; echo "== [${STEP}] $*"; }

dump_worker_logs() {
  echo "---- last 40 lines of ${ARENA_WORKER_SERVICE} logs ----" >&2
  ${DOCKER_COMPOSE} logs --no-color --tail=40 "${ARENA_WORKER_SERVICE}" 2>&1 >&2 || true
  echo "-------------------------------------------------------" >&2
}

fail() {
  echo >&2
  echo "FAIL: $*" >&2
  dump_worker_logs
  exit 1
}

command -v curl >/dev/null 2>&1 || { echo "FAIL: curl not found" >&2; exit 1; }
PY="$(command -v python3 || command -v python || true)"
[ -n "${PY}" ] || { echo "FAIL: python3 not found (needed to build JSON)" >&2; exit 1; }
[ -n "${NPCWARS_SERVICE_API_KEY:-}" ] || {
  echo "FAIL: NPCWARS_SERVICE_API_KEY is not set -- UP-2 requires a service key" >&2
  exit 1
}

# ---------------------------------------------------------------------------
# Python helpers. Every JSON value is built and read with json.dumps/json.load:
# hand-writing JSON with printf '%b' breaks the moment a bot source's real
# newlines land inside a JSON string (invalid JSON, rejected on parse).
# ---------------------------------------------------------------------------
read -r -d '' BUILD_PAYLOAD_PY <<'PYEOF' || true
import json, sys
marker = sys.argv[1]
source = (
    'BOT_NAME = "E2E Probe %s"\n'
    'BOT_EMOJI = "%s"\n'
    'BOT_BIO = "arena end-to-end probe"\n'
    '\n'
    'def decide(state):\n'
    '    return ("rest",)\n'
) % (marker, marker)
print(json.dumps({"source": source}))
PYEOF

read -r -d '' GET_KEY_PY <<'PYEOF' || true
import json, sys
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(1)
value = data.get(sys.argv[1]) if isinstance(data, dict) else None
if value in (None, "", []):
    sys.exit(1)
print(value)
PYEOF

read -r -d '' NEWEST_MATCH_PY <<'PYEOF' || true
import json, sys
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(1)
matches = data.get("matches") or []
if not matches:
    sys.exit(1)
print(max(int(m) for m in matches))
PYEOF

read -r -d '' CHECK_MATCH_PY <<'PYEOF' || true
import json, sys
match_id, marker = sys.argv[1], sys.argv[2]
data = json.load(sys.stdin)
problems = []
if str(data.get("match_id")) != str(match_id):
    problems.append("match_id %r != %r" % (data.get("match_id"), match_id))
if not data.get("winner"):
    problems.append("no winner")
if not data.get("rounds"):
    problems.append("no rounds")
emojis = [p.get("emoji") for p in data.get("players", [])]
if marker not in emojis:
    problems.append("submitter %r not among players %r" % (marker, emojis))
if problems:
    sys.stderr.write("; ".join(problems))
    sys.exit(1)
print("match %s: winner=%s rounds=%d players=%s"
      % (match_id, data["winner"], len(data["rounds"]), emojis))
PYEOF

read -r -d '' CHECK_LEADERBOARD_PY <<'PYEOF' || true
import json, sys
marker = sys.argv[1]
rows = json.load(sys.stdin)
emojis = [r.get("emoji") for r in rows]
if marker not in emojis:
    sys.stderr.write("submitter %r not on leaderboard (%d rows)" % (marker, len(rows)))
    sys.exit(1)
row = next(r for r in rows if r.get("emoji") == marker)
print("leaderboard entry: matches_played=%s wins=%s" %
      (row.get("matches_played"), row.get("wins")))
PYEOF

json_key() { "${PY}" -c "${GET_KEY_PY}" "$1"; }

# Unique per run: the ref is the UP-2 delegated identity, the marker is the
# bot emoji we later look for in the match file and on the leaderboard.
STAMP="$(date +%s)$$"
PLAYER_REF="e2e-${STAMP}"
MARKER="E2E${STAMP}"

echo "NPC Wars arena E2E"
echo "  url            : ${ARENA_URL}"
echo "  worker service : ${ARENA_WORKER_SERVICE}"
echo "  player ref     : ${PLAYER_REF}"
echo "  bot marker     : ${MARKER}"

# ---------------------------------------------------------------------------
step "Preflight: app healthy, worker can reach the sandbox, fail-closed intact"
# ---------------------------------------------------------------------------
curl -fsS --max-time 15 "${ARENA_URL}/health" >/dev/null \
  || fail "GET ${ARENA_URL}/health failed -- is the stack up and published there? (set ARENA_HOST_PORT or ARENA_URL to match docker-compose)"
ok "app answers /health"

UNSANDBOXED="$(${DOCKER_COMPOSE} exec -T "${ARENA_WORKER_SERVICE}" \
  sh -c 'printenv NPCWARS_ALLOW_UNSANDBOXED || true' 2>/dev/null | tr -d '\r\n')" \
  || fail "cannot exec into the '${ARENA_WORKER_SERVICE}' service -- is it running?"
[ -z "${UNSANDBOXED}" ] \
  || fail "worker has NPCWARS_ALLOW_UNSANDBOXED='${UNSANDBOXED}': the in-process path is open, so this run could NOT prove sandbox execution. Unset it and re-run."
ok "worker has NPCWARS_ALLOW_UNSANDBOXED unset (in-process execution impossible)"

${DOCKER_COMPOSE} exec -T "${ARENA_WORKER_SERVICE}" docker image inspect "${SANDBOX_IMAGE}" \
  >/dev/null 2>&1 \
  || fail "worker cannot see ${SANDBOX_IMAGE} through /var/run/docker.sock. Check the socket mount in docker-compose.yml and build the image: ${DOCKER_COMPOSE} --profile tools build sandbox"
ok "worker reaches the host docker daemon and ${SANDBOX_IMAGE} exists"

for svc in "${ARENA_APP_SERVICE}" "${ARENA_WORKER_SERVICE}"; do
  strict="$(${DOCKER_COMPOSE} exec -T "${svc}" \
    sh -c 'printenv NPCWARS_QUEUE_STRICT || true' 2>/dev/null | tr -d '\r\n' || true)"
  [ "${strict}" = "1" ] \
    || fail "${svc} has NPCWARS_QUEUE_STRICT='${strict}' -- without strict mode it can silently fall back to an in-process queue and strand jobs"
done
ok "app and worker both run with NPCWARS_QUEUE_STRICT=1 (no silent queue split)"

# ---------------------------------------------------------------------------
step "Submit a bot via the UP-2 delegated contract (service key + X-Player-Ref)"
# ---------------------------------------------------------------------------
PAYLOAD="$("${PY}" -c "${BUILD_PAYLOAD_PY}" "${MARKER}")"
SUBMIT_BODY="$(mktemp)"
trap 'rm -f "${SUBMIT_BODY}"' EXIT

SUBMIT_CODE="$(curl -sS --max-time 30 -o "${SUBMIT_BODY}" -w '%{http_code}' \
  -X POST "${ARENA_URL}/api/submit-bot" \
  -H 'Content-Type: application/json' \
  -H "X-API-Key: ${NPCWARS_SERVICE_API_KEY}" \
  -H "X-Player-Ref: ${PLAYER_REF}" \
  --data-binary "${PAYLOAD}")" || fail "submit request failed"

[ "${SUBMIT_CODE}" = "202" ] \
  || fail "expected 202 from /api/submit-bot, got ${SUBMIT_CODE}: $(head -c 300 "${SUBMIT_BODY}")"
JOB_ID="$(json_key job_id <"${SUBMIT_BODY}")" \
  || fail "202 response carried no job_id: $(head -c 300 "${SUBMIT_BODY}")"
ok "202 accepted, job_id=${JOB_ID}"

# ---------------------------------------------------------------------------
step "Wait (bounded, ${ARENA_WAIT_SECS}s) for the worker to produce the match"
# ---------------------------------------------------------------------------
DEADLINE=$(( $(date +%s) + ARENA_WAIT_SECS ))
MATCH_ID=""
while [ "$(date +%s)" -lt "${DEADLINE}" ]; do
  HISTORY="$(curl -sS --max-time 15 "${ARENA_URL}/api/lobby/history" \
    -H "X-API-Key: ${NPCWARS_SERVICE_API_KEY}" \
    -H "X-Player-Ref: ${PLAYER_REF}" || true)"
  if MATCH_ID="$(printf '%s' "${HISTORY}" | "${PY}" -c "${NEWEST_MATCH_PY}" 2>/dev/null)"; then
    if [ -n "${MATCH_ID}" ]; then
      break
    fi
  fi
  MATCH_ID=""
  sleep 2
done
[ -n "${MATCH_ID}" ] \
  || fail "no match for ${PLAYER_REF} after ${ARENA_WAIT_SECS}s -- the worker never completed the job"
ok "worker produced match ${MATCH_ID}"

# ---------------------------------------------------------------------------
step "Prove the match ran through the Docker sandbox"
# ---------------------------------------------------------------------------
# --no-color: the assertions below are substring matches, and ANSI escapes in
# a TTY-attached run have no business being in them.
WORKER_LOGS="$(${DOCKER_COMPOSE} logs --no-color --tail=500 "${ARENA_WORKER_SERVICE}" 2>&1 || true)"
printf '%s' "${WORKER_LOGS}" | grep -q "FAILED closed" \
  && fail "worker logged a fail-closed submission -- the sandbox was not reachable"
printf '%s' "${WORKER_LOGS}" | grep -q "Submission match ${MATCH_ID} completed" \
  || fail "worker logs do not show 'Submission match ${MATCH_ID} completed' -- the match did not come from the sandboxed submission path"
ok "worker completed the submission with no fail-closed error"
ok "sandbox execution proven: unsandboxed path disabled + sandbox image reachable + submission completed"

# ---------------------------------------------------------------------------
step "Replay resolution: /api/match/${MATCH_ID} and /api/match/${MATCH_ID}/stream"
# ---------------------------------------------------------------------------
MATCH_JSON="$(curl -fsS --max-time 20 "${ARENA_URL}/api/match/${MATCH_ID}")" \
  || fail "GET /api/match/${MATCH_ID} failed (UP-3 natural-id resolution)"
SUMMARY="$(printf '%s' "${MATCH_JSON}" | "${PY}" -c "${CHECK_MATCH_PY}" "${MATCH_ID}" "${MARKER}")" \
  || fail "/api/match/${MATCH_ID} returned an unusable match"
ok "${SUMMARY}"

# The stream sleeps ~1s per round, so read only the head of it: the first
# 'event: round' is what proves the endpoint resolved the same match.
STREAM_OUT="$(curl -sS --max-time 12 -N "${ARENA_URL}/api/match/${MATCH_ID}/stream" 2>/dev/null \
  | head -c 4000 || true)"
printf '%s' "${STREAM_OUT}" | grep -q "event: round" \
  || fail "/api/match/${MATCH_ID}/stream produced no round events (got: $(printf '%s' "${STREAM_OUT}" | head -c 200))"
ok "SSE stream resolved the same match id and emitted round events"

# ---------------------------------------------------------------------------
step "Ladder: the submitter appears on /api/leaderboard"
# ---------------------------------------------------------------------------
LEADERBOARD="$(curl -fsS --max-time 20 "${ARENA_URL}/api/leaderboard")" \
  || fail "GET /api/leaderboard failed"
LB_SUMMARY="$(printf '%s' "${LEADERBOARD}" | "${PY}" -c "${CHECK_LEADERBOARD_PY}" "${MARKER}")" \
  || fail "submitter ${MARKER} is not on the leaderboard"
ok "${LB_SUMMARY}"

echo
echo "PASS: submit -> queue -> sandboxed worker match -> replay (json + stream) -> ladder."
echo "      match_id=${MATCH_ID} job_id=${JOB_ID} bot=${MARKER}"
