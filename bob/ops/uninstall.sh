#!/bin/bash
# Remove Bob's launchd agents. Idempotent: safe to run when nothing is
# installed (every step tolerates absence). This is the kill switch's blunt
# end - state/, games/ and logs are left untouched so nothing invented or
# spent is lost; only the schedule stops.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGENTS_DIR="$HOME/Library/LaunchAgents"
GUI_DOMAIN="gui/$(id -u)"
LABELS="ai.autonomous.bob ai.autonomous.bob.watchdog"

for LABEL in $LABELS; do
    if launchctl bootout "$GUI_DOMAIN/$LABEL" 2>/dev/null; then
        echo "unloaded: $LABEL"
    else
        echo "not loaded (ok): $LABEL"
    fi
    if [ -f "$AGENTS_DIR/$LABEL.plist" ]; then
        rm -f "$AGENTS_DIR/$LABEL.plist"
        echo "removed:  $AGENTS_DIR/$LABEL.plist"
    else
        echo "no plist (ok): $AGENTS_DIR/$LABEL.plist"
    fi
done

echo ""
echo "Bob is stopped. State and logs kept at '$REPO/state'."
echo "Reinstall: '$REPO/ops/install.sh'"
