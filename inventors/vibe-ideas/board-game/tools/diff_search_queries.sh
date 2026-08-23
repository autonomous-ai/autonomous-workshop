#!/usr/bin/env bash
# diff_search_queries.sh — generate the standard set of WebSearch queries to
# run against a specific idea's MECHANISM/FEATURE (not just its game name)
# before finalizing it, per the Turn-1 lesson that differentiation is the
# systemic weak point.
#
# Usage: ./diff_search_queries.sh "magnetic modular deck box"
#
# Prints one query per line. Run each through WebSearch and read the top
# results before writing the idea's "differentiation" field. If any query
# turns up an existing product doing essentially the same mechanism, either
# drop the idea or sharpen it to a narrower, unclaimed sub-feature.

if [ -z "$1" ]; then
  echo "Usage: $0 \"<mechanism or feature phrase, no game name>\"" >&2
  exit 1
fi

FEATURE="$1"

cat <<EOF
$FEATURE
$FEATURE printable
$FEATURE 3d print
$FEATURE etsy
$FEATURE thingiverse
$FEATURE printables
$FEATURE makerworld
EOF

cat <<'WARN' >&2

REMINDER (differentiation regressed 7.6->5.6/15 in Turn 2 despite this
script existing): running these queries is not enough — actually open the
top 2-3 results per query and read them. A free hobbyist listing that does
roughly the same mechanism still falsifies an absolute claim. If any result
is a close match, do NOT write an absolute claim ("no existing design does
X", "every existing product requires Y") in the differentiation field —
either drop the idea or narrow the claim to a specific unclaimed
sub-feature/combination that the results did not contradict.

CRITICAL (Turn 4 fix — demand fell 36.7->30.0/55 over Turns 1-3 as a direct
side effect of this narrowing step): when you rescope to a narrower
sub-feature, narrow WHAT is built, never WHO buys it. Do not "solve" a
collision by pivoting the buyer from a mainstream game fanbase/general
hobbyist market to a small demographic (accessibility niche, institutional/
library buyers, a con-culture subgroup, a single legacy game's
completionists) — niche buyer segments have repeatedly capped demand at
22-35/55 even when fully verified. Keep the buyer broad; narrow only the
feature/combination.
WARN
