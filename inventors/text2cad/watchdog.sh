#!/bin/bash
# Dead-man watchdog (graduated from Tam's brain: silent-channel death must
# alarm — 4-night scraper blackout 6/5-6/8, admindash $13 silent burn 8/9-8/10).
# Cron (UTC): 0 4 * * *  /root/text2cad/watchdog.sh
set -u
cd "$(dirname "$0")"
set -a; source .env 2>/dev/null; set +a
HB=.heartbeat
ALERT=""
if [ ! -f "$HB" ]; then
  ALERT="text2cad watchdog: NO heartbeat file — autoloop has never run"
elif [ "$(( $(date +%s) - $(stat -c %Y "$HB") ))" -gt 100800 ]; then   # >28h
  ALERT="text2cad watchdog: heartbeat stale ($(cat "$HB")) — autoloop silent >28h, check cron/logs on panda"
fi
if [ -n "$ALERT" ] && [ -n "${TELEGRAM_BOT_TOKEN:-}" ]; then
  curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    -d "chat_id=${TELEGRAM_CHAT_DM}" --data-urlencode "text=$ALERT" >/dev/null
fi
