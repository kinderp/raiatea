#!/bin/sh
set -eu

fail() {
  printf '%s\n' "$1" >&2
  exit 1
}

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
STATE_DIR=$SCRIPT_DIR/.raiatea-runtime
STATE_FILE=$STATE_DIR/server-state.json
[ -f "$STATE_FILE" ] && [ ! -L "$STATE_FILE" ] || fail STATE_STALE

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

if ! STATE=$(
  "$PYTHON" - "$STATE_FILE" <<'PY'
import json, pathlib, sys
path = pathlib.Path(sys.argv[1])
try:
    value = json.loads(path.read_text(encoding="utf-8"))
except Exception:
    raise SystemExit(1)
if set(value) != {"entrypoint", "host", "marker", "pid", "port"}:
    raise SystemExit(1)
if value["marker"] != "raiatea-launch-state-v1" or value["host"] != "127.0.0.1" or value["entrypoint"] != "pilot/index.html":
    raise SystemExit(1)
pid = value["pid"]
port = value["port"]
if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 1:
    raise SystemExit(1)
if isinstance(port, bool) or not isinstance(port, int) or not 1024 <= port <= 65535:
    raise SystemExit(1)
print(f"{pid} {port}")
PY
); then
  fail STATE_STALE
fi
set -- $STATE
PID=$1
PORT=$2

kill -0 "$PID" 2>/dev/null || { rm -f "$STATE_FILE"; fail STATE_STALE; }

case "$(uname -s 2>/dev/null || printf unknown)" in
  Linux)
    CMDLINE=$(tr '\000' ' ' < "/proc/$PID/cmdline" 2>/dev/null || true)
    case "$CMDLINE" in
      *"http.server $PORT"*"--bind 127.0.0.1"*"--directory $SCRIPT_DIR/pilot"*) ;;
      *) fail STATE_FOREIGN_PROCESS ;;
    esac
    ;;
  *)
    CMDLINE=$(ps -p "$PID" -o command= 2>/dev/null || true)
    case "$CMDLINE" in
      *"http.server $PORT"*"--bind 127.0.0.1"*"$SCRIPT_DIR/pilot"*) ;;
      *) fail STATE_FOREIGN_PROCESS ;;
    esac
    ;;
esac

kill "$PID" 2>/dev/null || fail STOP_FAILED
attempt=0
while kill -0 "$PID" 2>/dev/null && [ "$attempt" -lt 40 ]; do
  sleep 0.1
  attempt=$((attempt + 1))
done
if kill -0 "$PID" 2>/dev/null; then
  kill -KILL "$PID" 2>/dev/null || fail STOP_FAILED
fi
rm -f "$STATE_FILE" "$STATE_DIR/server.log"
rmdir "$STATE_DIR" 2>/dev/null || true
printf 'Raiatea stopped on port %s.\n' "$PORT"
