#!/bin/bash
# One fresh game, end to end: DISCOVER -> phase 1 -> 2 -> 3.
#
# The winner slug is read from DISCOVER's own `WINNER:` line - never inferred.
# The first version guessed "newest out/*/brief.md" and relaunched phase 1 on
# keep-the-light-relay, a FINISHED game from Aug 19, while the real winner sat
# in out/no-ball-games (discover seeds seed.md+discover.md, not brief.md).
# Caught at the 20-minute tick; the reviser was killed before it overwrote the
# old game's gdd. ~$10 of opus went to critiquing a game nobody asked about.
set -o pipefail
cd /root/text2game
log=out/run_$(date -u +%m%d_%H%M).log
{
  echo "== DISCOVER $(date -u +%H:%M)"
  dlog=$(mktemp)
  python3 discover.py 2>&1 | tee "$dlog" || { echo "ABORT: discover failed"; exit 1; }
  slug=$(grep -m1 '^WINNER:' "$dlog" | awk '{print $2}')
  rm -f "$dlog"
  { [ -n "$slug" ] && [ -d "out/$slug" ]; } || { echo "ABORT: no WINNER line or out/$slug missing"; exit 1; }
  echo "== WINNER: $slug"
  ./text2game --slug "$slug" --phase all
} 2>&1 | tee "$log"
