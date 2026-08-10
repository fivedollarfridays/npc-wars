#!/usr/bin/env bash
# Decisive proof that the Docker sandbox path runs a REAL match.
#
# Builds Dockerfile.sandbox, pipes a real 3-bot payload to the container over
# stdin (exactly as server.docker_sandbox._run_in_docker does), and asserts the
# stdout is an actual match_data dict (has a winner + rounds) and NOT the old
# {"status":"sandbox_ok"} stub. Exits non-zero with a clear FAIL on any problem.
#
# Run this on a machine WITH a Docker daemon (the dev rig has none):
#   scripts/verify_sandbox_container.sh
set -euo pipefail

IMAGE="npcwars-sandbox:latest"
# Repo root = parent of this script's dir, so it works from anywhere.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

fail() { echo "FAIL: $*" >&2; exit 1; }

command -v docker >/dev/null 2>&1 || fail "docker not found on PATH"

echo "== Building ${IMAGE} from Dockerfile.sandbox =="
# BuildKit honors Dockerfile.sandbox.dockerignore (keeps data/ in context).
DOCKER_BUILDKIT=1 docker build -f Dockerfile.sandbox -t "${IMAGE}" . \
  || fail "image build failed"

echo "== Running a real 3-bot match through the container (stdin -> stdout) =="
REST_BOT='def decide(state):\n    return ("rest",)'
read -r -d '' PAYLOAD <<JSON || true
{"bots":[
  "BOT_NAME=\"Ay\"\nBOT_EMOJI=\"A\"\n${REST_BOT}",
  "BOT_NAME=\"Bee\"\nBOT_EMOJI=\"B\"\n${REST_BOT}",
  "BOT_NAME=\"Cee\"\nBOT_EMOJI=\"C\"\n${REST_BOT}"
],"config":{"match_id":424242,"seed":7}}
JSON

OUT="$(printf '%b' "$PAYLOAD" | docker run --rm -i --network=none "${IMAGE}")" \
  || fail "container exited non-zero"

echo "---- container stdout (head) ----"
echo "$OUT" | head -c 400; echo; echo "---------------------------------"

echo "$OUT" | grep -q 'sandbox_ok' && fail "container returned the sandbox_ok STUB, not a match"
echo "$OUT" | grep -q '"winner"' || fail "no 'winner' in output — not a real match"
echo "$OUT" | grep -q '"rounds"' || fail "no 'rounds' in output — not a real match"
echo "$OUT" | grep -q '"match_id": 424242' \
  || echo "$OUT" | grep -q '"match_id":424242' \
  || fail "match_id from payload did not flow through"

echo "PASS: Docker sandbox ran a real match (winner + rounds present, not sandbox_ok)."
