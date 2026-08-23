#!/bin/bash
# Eve dead-man watchdog. Runs hourly from launchd (ai.autonomous.eve.watchdog),
# deliberately NOT from inside Eve's one-step drive: a dead main loop cannot
# report its own death (text2cad receipt: "silent-channel death must alarm - 4-night
# scraper blackout 6/5-6/8, admindash $13 silent burn 8/9-8/10").
#
# Two alarms:
#   1. Heartbeat stale: state/DAYBOOK.json (each drive touches it via
#      meta.tick, per DESIGN.md) is missing or its mtime is older than 6h.
#      Drives fire every 30 min, so 6h = 12 missed launches - well past any
#      normal back-off but fast enough that a dead night costs 6 hours.
#   2. Fresh Traceback: the last 50 lines of state/logs/tick.log contain
#      'Traceback' AND the log is newer than the last traceback alarm -
#      a crash the tick loop itself never got to report.
#
# Markers rate-limit the DMs (the watchdog is hourly; without them one dead
# night = 12 identical pings and Dee mutes the channel - a muted alarm is no
# alarm). Heartbeat re-alarms at most every 6h; traceback re-alarms only when
# the log has been written since the last alarm (i.e. a NEW traceback).
set -u

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HEARTBEAT="$REPO/state/DAYBOOK.json"
TICK_LOG="$REPO/state/logs/tick.log"
HB_MARKER="$REPO/state/.watchdog-heartbeat-alarm"
TB_MARKER="$REPO/state/.watchdog-traceback-alarm"
STALE_SECONDS=21600   # 6h: 12 missed 30-min one-step drives
NOW="$(date +%s)"

# Telegram creds come from the environment or from .env at the repo root
# (launchd jobs inherit almost nothing, so .env is the normal path).
if [ -f "$REPO/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    . "$REPO/.env"
    set +a
fi

# mtime portable across macOS (BSD stat) and Linux (GNU stat, for CI).
mtime() {
    stat -f %m "$1" 2>/dev/null || stat -c %Y "$1" 2>/dev/null
}

# Fire-and-forget Telegram DM via raw curl (text2cad pattern, ~30s timeout).
# Without creds we still shout to stderr -> watchdog.log, never fail silently.
alert() {
    local msg="eve watchdog: $1"
    if [ -n "${EVE_TELEGRAM_TOKEN:-}" ] && [ -n "${EVE_TELEGRAM_CHAT:-}" ]; then
        curl -sS --max-time 30 \
            "https://api.telegram.org/bot${EVE_TELEGRAM_TOKEN}/sendMessage" \
            -d "chat_id=${EVE_TELEGRAM_CHAT}" \
            --data-urlencode "text=${msg}" >/dev/null \
            || echo "watchdog: telegram send FAILED: ${msg}" >&2
    else
        echo "watchdog: ALARM (no EVE_TELEGRAM_TOKEN/CHAT set): ${msg}" >&2
    fi
}

# --- Alarm 1: heartbeat stale or missing ------------------------------------
HB_STALE=0
if [ ! -f "$HEARTBEAT" ]; then
    # Missing counts as stale: a deploy that never ticked once must alarm
    # too, not just one that stopped.
    HB_STALE=1
    HB_AGE="never written"
else
    HB_MTIME="$(mtime "$HEARTBEAT")"
    HB_AGE_S=$((NOW - HB_MTIME))
    if [ "$HB_AGE_S" -gt "$STALE_SECONDS" ]; then
        HB_STALE=1
    fi
    HB_AGE="$((HB_AGE_S / 3600))h $(( (HB_AGE_S % 3600) / 60 ))m ago"
fi

if [ "$HB_STALE" -eq 1 ]; then
    RECENT_ALARM=0
    if [ -f "$HB_MARKER" ]; then
        MARKER_AGE=$((NOW - $(mtime "$HB_MARKER")))
        [ "$MARKER_AGE" -lt "$STALE_SECONDS" ] && RECENT_ALARM=1
    fi
    if [ "$RECENT_ALARM" -eq 0 ]; then
        alert "HEARTBEAT STALE - state/DAYBOOK.json last touched ${HB_AGE} (threshold 6h). The drive loop is not running. Check: tail -50 '$TICK_LOG' ; launchctl print gui/$(id -u)/ai.autonomous.eve"
        mkdir -p "$(dirname "$HB_MARKER")"
        touch "$HB_MARKER"
    fi
fi

# --- Alarm 2: fresh Traceback in the tick log --------------------------------
if [ -f "$TICK_LOG" ] && tail -n 50 "$TICK_LOG" | grep -q "Traceback"; then
    LOG_MTIME="$(mtime "$TICK_LOG")"
    MARKER_MTIME=0
    [ -f "$TB_MARKER" ] && MARKER_MTIME="$(mtime "$TB_MARKER")"
    # Alarm only when the log was written AFTER the last alarm: the same
    # stuck traceback must not DM every hour, but a new crash always does.
    if [ "$LOG_MTIME" -gt "$MARKER_MTIME" ]; then
        SNIPPET="$(tail -n 50 "$TICK_LOG" | grep -A 3 "Traceback" | head -8)"
        alert "TRACEBACK in tick.log - the drive loop is crashing. Last crash lines:
${SNIPPET}
Full log: tail -50 '$TICK_LOG'"
        mkdir -p "$(dirname "$TB_MARKER")"
        touch "$TB_MARKER"
    fi
fi

exit 0
