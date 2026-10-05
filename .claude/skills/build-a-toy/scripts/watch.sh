#!/usr/bin/env bash
# Watch one Workshop run until it stops, printing a line whenever its state
# changes. Run it from the Workshop checkout the run was launched from:
#
#   .claude/skills/build-a-toy/scripts/watch.sh <wish-id> [poll-seconds]
#
# It exits 0 when the run has stopped (any stop_category, or a status other
# than active); the loop then diagnoses the stop. It needs only bash, date and
# `uv`; every path comes from Workshop and Claude Code (see runpaths.py).
set -u
ID=${1:?usage: watch.sh <wish-id> [poll-seconds]}
POLL=${2:-60}
HERE=$(cd "$(dirname "$0")" && pwd)
prev=""
while true; do
  if ! status=$(uv run -q workshop status "$ID" --json 2>/dev/null); then
    sleep "$POLL"
    continue
  fi
  line=$(printf '%s' "$status" | uv run -q python "$HERE/snapshot.py" "$ID")
  code=$?
  if [ "$line" != "$prev" ]; then
    echo "$(date -u +%Y-%m-%dT%H:%MZ) $line"
    prev=$line
  fi
  if [ "$code" -eq 10 ]; then
    exit 0
  fi
  if [ "$code" -ne 0 ]; then
    echo "$(date -u +%Y-%m-%dT%H:%MZ) snapshot failed ($code)" >&2
  fi
  sleep "$POLL"
done
