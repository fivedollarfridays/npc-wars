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
# Build the payload with json.dumps so bot sources (which contain real
# newlines) are escaped as valid JSON. A hand-written heredoc + `printf '%b'`
# expands \n into literal control characters, which is invalid JSON and the
# entrypoint's json.loads rejects it.
PY="$(command -v python3 || command -v python)"
[ -n "${PY}" ] || fail "python3 not found on PATH (needed to build the JSON payload)"
PAYLOAD="$("${PY}" - <<'PYEOF'
import json
def bot(name, emoji):
    return "BOT_NAME=%r\nBOT_EMOJI=%r\ndef decide(state):\n    return (\"rest\",)\n" % (name, emoji)
print(json.dumps({
    "bots": [bot("Ay", "A"), bot("Bee", "B"), bot("Cee", "C")],
    "config": {"match_id": 424242, "seed": 7},
}))
PYEOF
)"

OUT="$(printf '%s' "$PAYLOAD" | docker run --rm -i --network=none "${IMAGE}")" \
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
