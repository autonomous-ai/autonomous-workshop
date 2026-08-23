#!/bin/zsh
set -euo pipefail

if [[ "${ALICE_SERVICE_OFFLINE_TEST:-}" == "1" ]]; then
  TEST_TOOLS="${ALICE_SERVICE_OFFLINE_TOOL_DIR:-}"
  if [[ "$TEST_TOOLS" != /* || ! -d "$TEST_TOOLS" || -L "$TEST_TOOLS" ]]; then
    print -u2 -- "offline test tool directory is invalid"
    exit 64
  fi
  PATH="$TEST_TOOLS:/usr/bin:/bin:/usr/sbin:/sbin"
  USER_HOME="$HOME"
else
  PATH="/usr/bin:/bin:/usr/sbin:/sbin"
  USER_HOME="$(/usr/bin/python3 -c 'import os,pwd; print(pwd.getpwuid(os.getuid()).pw_dir)')"
fi
export PATH
if [[ "$USER_HOME" != /* || ! -d "$USER_HOME" || -L "$USER_HOME" ]]; then
  print -u2 -- "service user home could not be resolved safely"
  exit 64
fi

WORKER_LABEL="ai.autonomous.alice.worker"
WATCHDOG_LABEL="ai.autonomous.alice.watchdog"
DOMAIN="gui/$UID"
WORKER_TARGET="$DOMAIN/$WORKER_LABEL"
WATCHDOG_TARGET="$DOMAIN/$WATCHDOG_LABEL"
LAUNCH_AGENTS="$USER_HOME/Library/LaunchAgents"

if launchctl print "$WATCHDOG_TARGET" >/dev/null 2>&1; then
  launchctl bootout "$WATCHDOG_TARGET"
fi
if launchctl print "$WORKER_TARGET" >/dev/null 2>&1; then
  launchctl bootout "$WORKER_TARGET"
fi

if launchctl print "$WATCHDOG_TARGET" >/dev/null 2>&1; then
  print -u2 -- "Alice watchdog is still loaded; refusing to report success"
  exit 2
fi
if launchctl print "$WORKER_TARGET" >/dev/null 2>&1; then
  print -u2 -- "Alice worker is still loaded; refusing to report success"
  exit 2
fi

rm -f "$LAUNCH_AGENTS/$WATCHDOG_LABEL.plist"
rm -f "$LAUNCH_AGENTS/$WORKER_LABEL.plist"
print -- "Alice worker and watchdog are absent; runtime state was retained"
