#!/bin/zsh
set -euo pipefail

if [[ "${ALICE_SERVICE_OFFLINE_TEST:-}" == "1" ]]; then
  TEST_TOOLS="${ALICE_SERVICE_OFFLINE_TOOL_DIR:-}"
  if [[ "$TEST_TOOLS" != /* || ! -d "$TEST_TOOLS" || -L "$TEST_TOOLS" ]]; then
    print -u2 -- "offline test tool directory is invalid"
    exit 64
  fi
  PATH="$TEST_TOOLS:/usr/bin:/bin:/usr/sbin:/sbin"
else
  PATH="/usr/bin:/bin:/usr/sbin:/sbin"
fi
export PATH

SCRIPT_DIR="${0:A:h}"
ALICE_DIR="${SCRIPT_DIR:h}"
REPO_ROOT="${ALICE_DIR:h:h}"
CORE_SOURCE_ROOT="$REPO_ROOT/foundation/src"
PYTHON="$ALICE_DIR/.venv/bin/python"
CONFIG=""
ENV_FILE=""
ROOT=""

usage() {
  print -u2 -- "usage: $0 --config /absolute/config.json --env-file /absolute/alice.env --root /absolute/runtime-root [--python /absolute/venv/bin/python]"
}

while (( $# > 0 )); do
  case "$1" in
    --config) CONFIG="${2:-}"; shift 2 ;;
    --env-file) ENV_FILE="${2:-}"; shift 2 ;;
    --root) ROOT="${2:-}"; shift 2 ;;
    --python) PYTHON="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) usage; exit 64 ;;
  esac
done
for value in "$CONFIG" "$ENV_FILE" "$ROOT" "$PYTHON"; do
  if [[ -z "$value" || "$value" != /* ]]; then
    usage
    exit 64
  fi
done
if [[ ! -x "$PYTHON" ]]; then
  print -u2 -- "venv Python is not executable"
  exit 64
fi

DOMAIN="gui/$UID"
WORKER_TARGET="$DOMAIN/ai.autonomous.alice.worker"
WATCHDOG_TARGET="$DOMAIN/ai.autonomous.alice.watchdog"
if ! launchctl print "$WORKER_TARGET" >/dev/null 2>&1; then
  print -u2 -- "Alice worker is not loaded"
  exit 2
fi
if ! launchctl print "$WATCHDOG_TARGET" >/dev/null 2>&1; then
  print -u2 -- "Alice watchdog is not loaded"
  exit 2
fi
"$PYTHON" -m alice.service probe \
  --config "$CONFIG" \
  --env-file "$ENV_FILE" \
  --root "$ROOT" \
  --source-root "$ALICE_DIR" \
  --core-source-root "$CORE_SOURCE_ROOT" \
  --state "$ROOT/var/service/health.json" \
  --watchdog-state "$ROOT/var/service/watchdog-health.json"
