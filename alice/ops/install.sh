#!/bin/zsh
set -euo pipefail
umask 077

WORKER_LABEL="ai.autonomous.alice.worker"
WATCHDOG_LABEL="ai.autonomous.alice.watchdog"
SCRIPT_DIR="${0:A:h}"
ALICE_DIR="${SCRIPT_DIR:h}"
REPO_ROOT="${ALICE_DIR:h}"
PYTHON="$ALICE_DIR/.venv/bin/python"
WATCHDOG_PYTHON="/usr/bin/python3"
CONFIG=""
ENV_FILE=""
ROOT=""
ALLOW_DRY_RUN=0
OFFLINE_TOOL_DIR=""

usage() {
  print -u2 -- "usage: $0 --config /absolute/config.json --env-file /absolute/alice.env --root /absolute/runtime-root [--python /absolute/venv/bin/python] [--allow-dry-run]"
}

while (( $# > 0 )); do
  case "$1" in
    --config) CONFIG="${2:-}"; shift 2 ;;
    --env-file) ENV_FILE="${2:-}"; shift 2 ;;
    --root) ROOT="${2:-}"; shift 2 ;;
    --python) PYTHON="${2:-}"; shift 2 ;;
    --allow-dry-run) ALLOW_DRY_RUN=1; shift ;;
    --offline-test-tool-dir)
      if [[ "${ALICE_SERVICE_OFFLINE_TEST:-}" != "1" ]]; then
        print -u2 -- "offline test tools require ALICE_SERVICE_OFFLINE_TEST=1"
        exit 64
      fi
      OFFLINE_TOOL_DIR="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) usage; exit 64 ;;
  esac
done

if [[ -n "$OFFLINE_TOOL_DIR" ]]; then
  if [[ "$OFFLINE_TOOL_DIR" != /* || ! -d "$OFFLINE_TOOL_DIR" || -L "$OFFLINE_TOOL_DIR" ]]; then
    print -u2 -- "offline test tool directory must be an absolute non-symlink directory"
    exit 64
  fi
  PATH="$OFFLINE_TOOL_DIR:/usr/bin:/bin:/usr/sbin:/sbin"
else
  PATH="/usr/bin:/bin:/usr/sbin:/sbin"
fi
export PATH

for value in "$CONFIG" "$ENV_FILE" "$ROOT" "$PYTHON"; do
  if [[ -z "$value" || "$value" != /* ]]; then
    usage
    exit 64
  fi
done
if [[ ! -f "$CONFIG" || -L "$CONFIG" ]]; then
  print -u2 -- "config must be a non-symlink regular file"
  exit 64
fi
if [[ ! -f "$ENV_FILE" || -L "$ENV_FILE" ]]; then
  print -u2 -- "environment file must be a non-symlink regular file"
  exit 64
fi
if [[ ! -x "$PYTHON" ]]; then
  print -u2 -- "venv Python is not executable"
  exit 64
fi
if [[ ! -x "$WATCHDOG_PYTHON" ]]; then
  print -u2 -- "independent /usr/bin/python3 watchdog runtime is unavailable"
  exit 64
fi
if [[ -n "$OFFLINE_TOOL_DIR" ]]; then
  USER_HOME="$HOME"
else
  USER_HOME="$("$WATCHDOG_PYTHON" -c 'import os,pwd; print(pwd.getpwuid(os.getuid()).pw_dir)')"
fi
if [[ "$USER_HOME" != /* || ! -d "$USER_HOME" || -L "$USER_HOME" ]]; then
  print -u2 -- "service user home could not be resolved safely"
  exit 64
fi
if ! "$PYTHON" -c 'import sys; raise SystemExit(0 if sys.prefix != sys.base_prefix else 1)'; then
  print -u2 -- "--python must point to a virtual-environment Python"
  exit 64
fi
if ! "$PYTHON" -c 'import pathlib, sys, alice.service; expected = pathlib.Path(sys.argv[1]).resolve(); actual = pathlib.Path(alice.service.__file__).resolve(); raise SystemExit(0 if actual == expected else 1)' "$ALICE_DIR/src/alice/service.py"; then
  print -u2 -- "venv must use this Alice checkout (install it editable first)"
  exit 64
fi
if [[ -n "$(git -C "$REPO_ROOT" status --porcelain=v1 --untracked-files=all -- alice)" ]]; then
  print -u2 -- "refusing to install from a dirty Alice subtree"
  exit 65
fi

PREFLIGHT=("$PYTHON" -m alice.service preflight --config "$CONFIG" --env-file "$ENV_FILE" --root "$ROOT" --source-root "$ALICE_DIR")
if (( ALLOW_DRY_RUN )); then
  PREFLIGHT+=(--allow-dry-run)
fi
"${PREFLIGHT[@]}"

SERVICE_DIR="$ROOT/var/service"
STATE="$SERVICE_DIR/health.json"
LOCK="$SERVICE_DIR/worker.lock"
RATE_STATE="$SERVICE_DIR/alert-rate.json"
WATCHDOG_STATE="$SERVICE_DIR/watchdog-health.json"
WATCHDOG_SCRIPT="$SERVICE_DIR/watchdog.py"
mkdir -p "$SERVICE_DIR"
chmod 700 "$SERVICE_DIR"

DOMAIN="gui/$UID"
WORKER_TARGET="$DOMAIN/$WORKER_LABEL"
WATCHDOG_TARGET="$DOMAIN/$WATCHDOG_LABEL"
LAUNCH_AGENTS="$USER_HOME/Library/LaunchAgents"
WORKER_PLIST="$LAUNCH_AGENTS/$WORKER_LABEL.plist"
WATCHDOG_PLIST="$LAUNCH_AGENTS/$WATCHDOG_LABEL.plist"
mkdir -p "$LAUNCH_AGENTS"

WORKER_WAS_LOADED=0
WATCHDOG_WAS_LOADED=0
launchctl print "$WORKER_TARGET" >/dev/null 2>&1 && WORKER_WAS_LOADED=1
launchctl print "$WATCHDOG_TARGET" >/dev/null 2>&1 && WATCHDOG_WAS_LOADED=1
if (( WORKER_WAS_LOADED )) && [[ ! -f "$WORKER_PLIST" ]]; then
  print -u2 -- "loaded Alice worker has no restorable plist; refusing replacement"
  exit 66
fi
if (( WATCHDOG_WAS_LOADED )) && [[ ! -f "$WATCHDOG_PLIST" ]]; then
  print -u2 -- "loaded Alice watchdog has no restorable plist; refusing replacement"
  exit 66
fi

BACKUP_BASE="/private/tmp"
[[ -d "$BACKUP_BASE" ]] || BACKUP_BASE="/tmp"
BACKUP_DIR="$(mktemp -d "$BACKUP_BASE/alice-launchd.XXXXXX")"
[[ -f "$WORKER_PLIST" ]] && cp -p "$WORKER_PLIST" "$BACKUP_DIR/worker.plist"
[[ -f "$WATCHDOG_PLIST" ]] && cp -p "$WATCHDOG_PLIST" "$BACKUP_DIR/watchdog.plist"
[[ -f "$WATCHDOG_SCRIPT" ]] && cp -p "$WATCHDOG_SCRIPT" "$BACKUP_DIR/watchdog.py"

rollback() {
  local code="${1:-70}"
  (( code == 0 )) && code=70
  local rollback_ok=1
  trap - ERR INT TERM
  set +e
  launchctl bootout "$WATCHDOG_TARGET" >/dev/null 2>&1
  launchctl bootout "$WORKER_TARGET" >/dev/null 2>&1
  if [[ -f "$BACKUP_DIR/worker.plist" ]]; then
    cp -p "$BACKUP_DIR/worker.plist" "$WORKER_PLIST" || rollback_ok=0
  else
    rm -f "$WORKER_PLIST" || rollback_ok=0
  fi
  if [[ -f "$BACKUP_DIR/watchdog.plist" ]]; then
    cp -p "$BACKUP_DIR/watchdog.plist" "$WATCHDOG_PLIST" || rollback_ok=0
  else
    rm -f "$WATCHDOG_PLIST" || rollback_ok=0
  fi
  if [[ -f "$BACKUP_DIR/watchdog.py" ]]; then
    cp -p "$BACKUP_DIR/watchdog.py" "$WATCHDOG_SCRIPT" || rollback_ok=0
  else
    rm -f "$WATCHDOG_SCRIPT" || rollback_ok=0
  fi
  if (( WORKER_WAS_LOADED )); then
    launchctl bootstrap "$DOMAIN" "$WORKER_PLIST" >/dev/null 2>&1 || rollback_ok=0
  fi
  if (( WATCHDOG_WAS_LOADED )); then
    launchctl bootstrap "$DOMAIN" "$WATCHDOG_PLIST" >/dev/null 2>&1 || rollback_ok=0
  fi
  if (( WORKER_WAS_LOADED )); then
    launchctl print "$WORKER_TARGET" >/dev/null 2>&1 || rollback_ok=0
  elif launchctl print "$WORKER_TARGET" >/dev/null 2>&1; then
    rollback_ok=0
  fi
  if (( WATCHDOG_WAS_LOADED )); then
    launchctl print "$WATCHDOG_TARGET" >/dev/null 2>&1 || rollback_ok=0
  elif launchctl print "$WATCHDOG_TARGET" >/dev/null 2>&1; then
    rollback_ok=0
  fi
  rm -rf "$BACKUP_DIR"
  if (( ! rollback_ok )); then
    print -u2 -- "Alice launchd installation failed and rollback verification was incomplete; runtime state was retained"
    exit 70
  fi
  print -u2 -- "Alice launchd installation failed; prior jobs were restored and runtime state was retained"
  exit "$code"
}
trap 'rollback $?' ERR
trap 'rollback 130' INT
trap 'rollback 143' TERM

install -m 700 "$SCRIPT_DIR/watchdog.py" "$WATCHDOG_SCRIPT"

"$PYTHON" -m alice.service render-plists \
  --worker-template "$SCRIPT_DIR/$WORKER_LABEL.plist.in" \
  --watchdog-template "$SCRIPT_DIR/$WATCHDOG_LABEL.plist.in" \
  --worker-output "$WORKER_PLIST" \
  --watchdog-output "$WATCHDOG_PLIST" \
  --python "$PYTHON" \
  --watchdog-python "$WATCHDOG_PYTHON" \
  --watchdog-script "$WATCHDOG_SCRIPT" \
  --config "$CONFIG" \
  --env-file "$ENV_FILE" \
  --root "$ROOT" \
  --source-root "$ALICE_DIR" \
  --state "$STATE" \
  --lock "$LOCK" \
  --rate-state "$RATE_STATE" \
  --watchdog-state "$WATCHDOG_STATE" \
  --launchd-target "$WORKER_TARGET" >/dev/null

plutil -lint "$WORKER_PLIST" >/dev/null
plutil -lint "$WATCHDOG_PLIST" >/dev/null

START_EPOCH="$(date +%s)"
launchctl bootout "$WATCHDOG_TARGET" >/dev/null 2>&1 || true
launchctl bootout "$WORKER_TARGET" >/dev/null 2>&1 || true
launchctl bootstrap "$DOMAIN" "$WORKER_PLIST"
launchctl bootstrap "$DOMAIN" "$WATCHDOG_PLIST"
launchctl enable "$WORKER_TARGET"
launchctl enable "$WATCHDOG_TARGET"
launchctl kickstart -k "$WORKER_TARGET"
launchctl kickstart -k "$WATCHDOG_TARGET"

launchctl print "$WORKER_TARGET" >/dev/null
launchctl print "$WATCHDOG_TARGET" >/dev/null
"$PYTHON" -m alice.service wait-healthy \
  --config "$CONFIG" \
  --env-file "$ENV_FILE" \
  --root "$ROOT" \
  --source-root "$ALICE_DIR" \
  --state "$STATE" \
  --watchdog-state "$WATCHDOG_STATE" \
  --started-after-epoch "$START_EPOCH" \
  --timeout-seconds 90 >/dev/null

trap - ERR INT TERM
rm -rf "$BACKUP_DIR"
print -- "Alice worker and protective watchdog are installed and healthy"
