#!/bin/bash
# Install Bob's two launchd agents (tick every 30 min + hourly watchdog).
# Idempotent: re-running boots out any loaded copy first, then bootstraps the
# fresh plist - so this is also the "redeploy" command after a plist edit.
#
# Refuses to install a broken deploy: text2cad's receipt is that the money
# goes to harness bugs, not product bugs - a launchd agent pointed at a
# missing bob.py or a non-importing harness would fail silently every 30
# minutes until the watchdog's 6h stale alarm. Fail loudly NOW instead.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
USER_HOME="$(/usr/bin/python3 -c 'import os,pwd; print(pwd.getpwuid(os.getuid()).pw_dir)')"
AGENTS_DIR="$USER_HOME/Library/LaunchAgents"
GUI_DOMAIN="gui/$(id -u)"
LABELS="ai.autonomous.bob ai.autonomous.bob.watchdog"
RENDERER="$REPO/ops/render_launchd.py"
CORE_SRC="${BOB_CORE_SRC:-$REPO/../core/src}"

# --- Refusal guards (catch broken deploys before launchd loops on them) -----
if [ ! -f "$REPO/bob.py" ]; then
    echo "REFUSING to install: $REPO/bob.py is missing." >&2
    echo "The tick agent runs 'python3 bob.py tick'; installing now would" >&2
    echo "just fill state/logs/tick.log with launchd spawn errors." >&2
    echo "Fix: deploy the integrator's bob.py first, then re-run ops/install.sh." >&2
    exit 1
fi
if ! (cd "$REPO" && /usr/bin/python3 -c 'import harness') >/dev/null 2>&1; then
    echo "REFUSING to install: 'python3 -c \"import harness\"' fails from $REPO." >&2
    echo "The harness package is broken or missing - every tick would crash." >&2
    echo "Fix: run it yourself to see the error:" >&2
    echo "  cd '$REPO' && /usr/bin/python3 -c 'import harness'" >&2
    exit 1
fi
if ! (cd "$REPO" && BOB_CORE_SRC="$CORE_SRC" /usr/bin/python3 -c \
    'from harness.core_runtime import require_core; require_core()') >/dev/null 2>&1; then
    echo "REFUSING to install: shared inventor_core is unavailable at $CORE_SRC." >&2
    echo "Bob's artifact and Panda outbox contracts require the repo-level core." >&2
    echo "Fix: deploy core beside bob, or set BOB_CORE_SRC to core/src." >&2
    exit 1
fi
if [ ! -f "$RENDERER" ]; then
    echo "REFUSING to install: $RENDERER is missing." >&2
    exit 1
fi

# --- Install -----------------------------------------------------------------
mkdir -p "$REPO/state/logs" "$AGENTS_DIR"

for LABEL in $LABELS; do
    PLIST_SRC="$REPO/ops/launchd/$LABEL.plist.in"
    PLIST_DST="$AGENTS_DIR/$LABEL.plist"
    if [ ! -f "$PLIST_SRC" ]; then
        echo "REFUSING: $PLIST_SRC missing (partial checkout?)." >&2
        exit 1
    fi
    /usr/bin/python3 "$RENDERER" \
        --template "$PLIST_SRC" \
        --output "$PLIST_DST" \
        --repo "$REPO" \
        --home "$USER_HOME" \
        --core-src "$CORE_SRC"
    /usr/bin/plutil -lint "$PLIST_DST" >/dev/null
    # bootout first so re-install picks up plist changes; ignore "not loaded".
    launchctl bootout "$GUI_DOMAIN/$LABEL" 2>/dev/null || true
    launchctl bootstrap "$GUI_DOMAIN" "$PLIST_DST"
    echo "installed + loaded: $LABEL"
done

# --- Status + operator crib sheet --------------------------------------------
echo ""
echo "status:"
launchctl list | grep "ai\.autonomous\.bob" || true
echo ""
echo "watch logs:   tail -f '$REPO/state/logs/tick.log'"
echo "watchdog log: tail -f '$REPO/state/logs/watchdog.log'"
echo "tick now:     launchctl kickstart $GUI_DOMAIN/ai.autonomous.bob"
echo "stop:         '$REPO/ops/uninstall.sh'   (or: launchctl bootout $GUI_DOMAIN/ai.autonomous.bob)"
