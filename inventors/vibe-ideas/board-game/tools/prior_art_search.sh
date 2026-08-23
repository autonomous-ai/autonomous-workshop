#!/usr/bin/env bash
# prior_art_search.sh — generate the mandatory set of WebSearch queries for a
# board-game differentiation claim, per the recurring Turn 4/5/6/8/9 failure:
# "the idea's own search was phrased around a generic category or a
# mechanically-similar game from the WRONG theme, and missed prior art that
# the claim's own literal wording finds instantly." (Vault Breakers missed
# Heist; Orchard Order missed Let's Learn Carousel; Stratum's own stated
# query, run verbatim, found Rack-O as the first result.)
#
# Usage: ./prior_art_search.sh "combination dial vault cracking" "heist theme" "Vault Breakers"
#   arg1 = the mechanism/feature phrase in the idea's OWN words, as if it
#          were the headline pitch of a standalone product (not a rules
#          detail buried in a longer description)
#   arg2 = the idea's theme (optional but strongly recommended — a search
#          aimed at a mechanically-similar game in the WRONG theme has
#          repeatedly missed the real competitor, e.g. searching "desert
#          caravan" comparables for a sailing/wind game missed Cartolan)
#   arg3 = the idea's own title (optional but strongly recommended — Turn 11:
#          "Caravan Ledger" never searched its own name and missed a shipped
#          game literally titled "Caravan" whose core mechanic overlapped)
#
# Prints one query per line. Run EACH one through WebSearch (not just the
# first) and actually read the top 2-3 results before writing the
# "differentiation" field. Only write "not an existing shipped product" if
# every query below comes back clean.

if [ -z "$1" ]; then
  echo "Usage: $0 \"<mechanism/feature phrase, idea's own words>\" [\"<theme>\"] [\"<idea's own title>\"]" >&2
  exit 1
fi

FEATURE="$1"
THEME="${2:-}"
TITLE="${3:-}"

cat <<EOF
$FEATURE
$FEATURE board game
$FEATURE tabletop game BGG
EOF

if [ -n "$THEME" ]; then
  cat <<EOF
$FEATURE $THEME board game
EOF
fi

if [ -n "$TITLE" ]; then
  cat <<EOF
$TITLE board game
$TITLE board game BGG
EOF
fi

cat <<'WARN' >&2

MANDATORY before writing "differentiation":
1. Query 1 must be the mechanism described exactly as the idea's own
   concept/rules text phrases it (Turn 8: Stratum's OWN stated query, run
   verbatim with zero rephrasing, surfaced Rack-O as the #1 result — the
   idea failed not on phrasing but on not reading its own top hit).
2. Treat any rule described almost incidentally ("cards lock into fixed
   slots," "a shared dial everyone reads," "spin a combination dial to
   crack the vault") as a standalone product pitch and search it as such —
   these incidental-sounding rules are consistently the ones that turn out
   to be a classic/shipped game's entire premise (Rack-O, Heist, Let's
   Learn Carousel all matched this pattern).
3. If the idea's mechanism resembles a known game type from a DIFFERENT
   theme (e.g. a wind-routing mechanic that resembles a caravan game), you
   MUST also search the idea's own theme+mechanism combination, not just
   the mechanically-similar game's theme — searching the wrong theme's
   comparables will always miss the real competitor, who ships in the
   idea's own theme (Turn 6: Cartolan: Trade Winds was missed this way).
4. If a hit is a genuinely thin/ambiguous partial match (a one-line BGG
   listing that doesn't confirm or deny the specific mechanism), do not
   treat it as either a clean pass or a full contradiction — note it
   explicitly as inconclusive/partial evidence in the differentiation
   field (Turn 9: "Trump Change" for Rune Trick's dynamic-trump claim).
5. Every NAMED comparable used as supporting evidence (not just the
   absence claim) also needs its own existence-check — a fabricated or
   unfindable "here's what's similar" citation undercuts the idea as much
   as a false "nobody does this" claim (Turn 6: "Gear Towers").
6. ALWAYS also search the idea's own title/name as a plain "<title> board
   game" query, independent of the mechanism search — a title that closely
   echoes an existing shipped game's name is itself a differentiation red
   flag, even when the mechanism search comes back clean (Turn 11:
   "Caravan Ledger" was never checked against a real shipped game literally
   titled "Caravan," whose steal-a-visible-good mechanic overlapped with
   the idea's own "Toll" rule).
WARN
