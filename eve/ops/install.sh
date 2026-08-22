#!/bin/bash
# Install Eve's two launchd agents (tick every 30 min + hourly watchdog).
# Idempotent: re-running boots out any loaded copy first, then bootstraps the
# fresh plist - so this is also the "redeploy" command after a plist edit.
#
# Refuses to install a broken deploy: text2cad's receipt is that the money
# goes to harness bugs, not product bugs - a launchd agent pointed at a
# missing CLI or a non-importing package would fail silently every 30 minutes
# until the watchdog's 6h stale alarm. Fail loudly NOW instead.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGENTS_DIR="$HOME/Library/LaunchAgents"
GUI_DOMAIN="gui/$(id -u)"
LABELS="ai.autonomous.eve ai.autonomous.eve.watchdog"

# --- Refusal guards (catch broken deploys before launchd loops on them) -----
if [ ! -f "$REPO/bin/eve" ]; then
    echo "REFUSING to install: $REPO/bin/eve is missing." >&2
    echo "The tick agent runs 'python3 bin/eve tick --run-agent'; installing" >&2
    echo "now would just fill state/logs/tick.log with launchd spawn errors." >&2
    echo "Fix: deploy Eve's CLI first, then re-run ops/install.sh." >&2
    exit 1
fi
if ! (cd "$REPO" && /usr/bin/python3 -c 'import eve.cli, eve.meta') >/dev/null 2>&1; then
    echo "REFUSING to install: 'python3 -c \"import eve.cli\"' fails from $REPO." >&2
    echo "The eve package is broken or missing - every tick would crash." >&2
    echo "Fix: run it yourself to see the error:" >&2
    echo "  cd '$REPO' && /usr/bin/python3 -c 'import eve.cli, eve.meta'" >&2
    exit 1
fi

# --- Install -----------------------------------------------------------------
mkdir -p "$REPO/state/logs" "$AGENTS_DIR"

for LABEL in $LABELS; do
    PLIST_SRC="$REPO/ops/launchd/$LABEL.plist"
    PLIST_DST="$AGENTS_DIR/$LABEL.plist"
    if [ ! -f "$PLIST_SRC" ]; then
        echo "REFUSING: $PLIST_SRC missing (partial checkout?)." >&2
        exit 1
    fi
    cp "$PLIST_SRC" "$PLIST_DST"
    # bootout first so re-install picks up plist changes; ignore "not loaded".
    launchctl bootout "$GUI_DOMAIN/$LABEL" 2>/dev/null || true
    launchctl bootstrap "$GUI_DOMAIN" "$PLIST_DST"
    echo "installed + loaded: $LABEL"
done

# --- Status + operator crib sheet --------------------------------------------
echo ""
echo "status:"
launchctl list | grep "ai\.autonomous\.eve" || true
echo ""
echo "watch logs:   tail -f '$REPO/state/logs/tick.log'"
echo "watchdog log: tail -f '$REPO/state/logs/watchdog.log'"
echo "tick now:     launchctl kickstart $GUI_DOMAIN/ai.autonomous.eve"
echo "stop:         '$REPO/ops/uninstall.sh'   (or: launchctl bootout $GUI_DOMAIN/ai.autonomous.eve)"
