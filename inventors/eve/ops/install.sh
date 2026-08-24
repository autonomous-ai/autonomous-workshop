#!/bin/bash
# Install Eve's two launchd agents (one-step drive every 30 min + watchdog).
# Idempotent: re-running boots out any loaded copy first, then bootstraps the
# fresh plist - so this is also the "redeploy" command after a plist edit.
#
# Refuses to install a broken deploy: text2cad's receipt is that the money
# goes to harness bugs, not product bugs - a launchd agent pointed at a
# missing CLI or a non-importing package would fail silently every 30 minutes
# until the watchdog's 6h stale alarm. Fail loudly NOW instead.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
USER_HOME="$(/usr/bin/python3 -c 'import os,pwd; print(pwd.getpwuid(os.getuid()).pw_dir)')"
AGENTS_DIR="$USER_HOME/Library/LaunchAgents"
GUI_DOMAIN="gui/$(id -u)"
LABELS="ai.autonomous.eve ai.autonomous.eve.watchdog"
RENDERER="$REPO/ops/render_launchd.py"
WORKSHOP_SRC_CURRENT="${EVE_WORKSHOP_SRC:-}"
WORKSHOP_SRC_LEGACY="${EVE_CORE_SRC:-}"
if [ -n "$WORKSHOP_SRC_CURRENT" ] && [ -n "$WORKSHOP_SRC_LEGACY" ] && \
   [ "$WORKSHOP_SRC_CURRENT" != "$WORKSHOP_SRC_LEGACY" ]; then
    WORKSHOP_SRC_CURRENT_REAL="$(cd "$WORKSHOP_SRC_CURRENT" 2>/dev/null && pwd -P)" || true
    WORKSHOP_SRC_LEGACY_REAL="$(cd "$WORKSHOP_SRC_LEGACY" 2>/dev/null && pwd -P)" || true
    if [ -z "$WORKSHOP_SRC_CURRENT_REAL" ] || \
       [ -z "$WORKSHOP_SRC_LEGACY_REAL" ] || \
       [ "$WORKSHOP_SRC_CURRENT_REAL" != "$WORKSHOP_SRC_LEGACY_REAL" ]; then
        echo "REFUSING to install: EVE_WORKSHOP_SRC conflicts with legacy EVE_CORE_SRC." >&2
        exit 1
    fi
    WORKSHOP_SRC_CURRENT="$WORKSHOP_SRC_CURRENT_REAL"
fi
WORKSHOP_SRC="${WORKSHOP_SRC_CURRENT:-${WORKSHOP_SRC_LEGACY:-$REPO/../../src}}"

# --- Refusal guards (catch broken deploys before launchd loops on them) -----
if [ ! -f "$REPO/bin/eve" ]; then
    echo "REFUSING to install: $REPO/bin/eve is missing." >&2
    echo "The driver agent runs 'python3 bin/eve drive --steps 1'; installing" >&2
    echo "now would just fill state/logs/tick.log with launchd spawn errors." >&2
    echo "Fix: deploy Eve's CLI first, then re-run ops/install.sh." >&2
    exit 1
fi
case "$WORKSHOP_SRC" in
    /*) ;;
    *)
        echo "REFUSING to install: EVE_WORKSHOP_SRC must be an absolute path." >&2
        exit 1
        ;;
esac
if [ ! -d "$WORKSHOP_SRC" ]; then
    echo "REFUSING to install: Workshop source directory is missing: $WORKSHOP_SRC" >&2
    echo "Fix: deploy the repository-root src package, or set EVE_WORKSHOP_SRC explicitly." >&2
    exit 1
fi
WORKSHOP_SRC="$(cd "$WORKSHOP_SRC" && pwd -P)"
if [ ! -f "$WORKSHOP_SRC/inventor_workshop/__init__.py" ]; then
    echo "REFUSING to install: inventor_workshop is unavailable at $WORKSHOP_SRC." >&2
    echo "Fix: deploy the repository-root src package, or set EVE_WORKSHOP_SRC explicitly." >&2
    exit 1
fi
if ! (
    cd "$REPO" &&
    EVE_WORKSHOP_SRC="$WORKSHOP_SRC" PYTHONPATH="$WORKSHOP_SRC" /usr/bin/python3 -c \
        'import os; from pathlib import Path; import eve.cli, eve.meta, inventor_workshop; expected=(Path(os.environ["EVE_WORKSHOP_SRC"])/"inventor_workshop"/"__init__.py").resolve(strict=True); actual=Path(inventor_workshop.__file__).resolve(strict=True); raise SystemExit(0 if actual == expected else "wrong inventor_workshop: %s" % actual)'
) >/dev/null 2>&1; then
    echo "REFUSING to install: Eve cannot import the exact Workshop at $WORKSHOP_SRC." >&2
    echo "Every scheduled drive must reach this checkout's artifact boundary." >&2
    echo "Fix: deploy the repository-root src package, or set EVE_WORKSHOP_SRC explicitly." >&2
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
        --workshop-src "$WORKSHOP_SRC"
    /usr/bin/plutil -lint "$PLIST_DST" >/dev/null
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
echo "drive now:    launchctl kickstart $GUI_DOMAIN/ai.autonomous.eve"
echo "stop:         '$REPO/ops/uninstall.sh'   (or: launchctl bootout $GUI_DOMAIN/ai.autonomous.eve)"
