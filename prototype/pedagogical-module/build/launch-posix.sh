#!/bin/sh
set -eu

fail() {
  printf '%s\n' "$1" >&2
  exit 1
}

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
RELEASE_DIR=$SCRIPT_DIR
PORT=8000
OPEN_BROWSER=1

while [ "$#" -gt 0 ]; do
  case "$1" in
    --no-open) OPEN_BROWSER=0 ;;
    --port)
      shift
      [ "$#" -gt 0 ] || fail PORT_INVALID
      PORT=$1
      ;;
    *) fail PORT_INVALID ;;
  esac
  shift
done

case "$PORT" in
  ''|*[!0-9]*) fail PORT_INVALID ;;
esac
[ "$PORT" -ge 1024 ] 2>/dev/null && [ "$PORT" -le 65535 ] 2>/dev/null || fail PORT_INVALID

PYTHON=
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1; then
    if "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)' >/dev/null 2>&1; then
      PYTHON=$candidate
      break
    fi
  fi
done
[ -n "$PYTHON" ] || fail PYTHON_NOT_FOUND

for required in RELEASE-NOTES.md SHA256SUMS release-manifest.json pilot/index.html; do
  [ -f "$RELEASE_DIR/$required" ] && [ ! -L "$RELEASE_DIR/$required" ] || fail RELEASE_FILE_UNSAFE
done

"$PYTHON" - "$RELEASE_DIR" <<'PY' || fail RELEASE_IDENTITY_MISMATCH
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
prefix = "raiatea-evaluator-"
if not root.name.startswith(prefix) or root.name == prefix:
    raise SystemExit(1)
manifest = json.loads((root / "release-manifest.json").read_text(encoding="utf-8"))
if manifest.get("format") != "raiatea-evaluator-release":
    raise SystemExit(1)
if manifest.get("releaseVersion") != root.name[len(prefix):]:
    raise SystemExit(1)
PY

STATE_DIR=$RELEASE_DIR/.raiatea-runtime
STATE_FILE=$STATE_DIR/server-state.json
LOG_FILE=$STATE_DIR/server.log
[ ! -e "$STATE_FILE" ] || fail STATE_ALREADY_EXISTS

"$PYTHON" - "$PORT" <<'PY' || fail PORT_IN_USE
import socket, sys
port = int(sys.argv[1])
s = socket.socket()
try:
    s.bind(("127.0.0.1", port))
finally:
    s.close()
PY

mkdir -p "$STATE_DIR"
TMP_STATE=$STATE_DIR/.server-state.$$
SERVER_PID=
cleanup_failed_launch() {
  if [ -n "$SERVER_PID" ]; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
  rm -f "$TMP_STATE" "$STATE_FILE"
}
trap cleanup_failed_launch HUP INT TERM

"$PYTHON" -m http.server "$PORT" --bind 127.0.0.1 --directory "$RELEASE_DIR/pilot" >"$LOG_FILE" 2>&1 &
SERVER_PID=$!

READY=0
attempt=0
while [ "$attempt" -lt 40 ]; do
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    cleanup_failed_launch
    fail SERVER_START_FAILED
  fi
  if "$PYTHON" - "$PORT" <<'PY' >/dev/null 2>&1
import http.client, sys
c = http.client.HTTPConnection("127.0.0.1", int(sys.argv[1]), timeout=0.25)
c.request("GET", "/index.html")
r = c.getresponse()
raise SystemExit(0 if r.status == 200 else 1)
PY
  then
    READY=1
    break
  fi
  attempt=$((attempt + 1))
  sleep 0.1
done
[ "$READY" -eq 1 ] || { cleanup_failed_launch; fail SERVER_NOT_READY; }

"$PYTHON" - "$TMP_STATE" "$SERVER_PID" "$PORT" <<'PY'
import json, pathlib, sys
path = pathlib.Path(sys.argv[1])
value = {
    "marker": "raiatea-launch-state-v1",
    "pid": int(sys.argv[2]),
    "port": int(sys.argv[3]),
    "host": "127.0.0.1",
    "entrypoint": "pilot/index.html",
}
path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
PY
mv "$TMP_STATE" "$STATE_FILE"
trap - HUP INT TERM

URL=http://127.0.0.1:$PORT/index.html
if [ "$OPEN_BROWSER" -eq 1 ]; then
  case "$(uname -s 2>/dev/null || printf unknown)" in
    Darwin) command -v open >/dev/null 2>&1 && open "$URL" >/dev/null 2>&1 || true ;;
    *) command -v xdg-open >/dev/null 2>&1 && xdg-open "$URL" >/dev/null 2>&1 || true ;;
  esac
fi
printf 'Raiatea ready: %s\n' "$URL"
printf 'Stop with: %s/stop-posix.sh\n' "$RELEASE_DIR"
