#!/usr/bin/env bash
# Copy a worktree's untracked toy output and design material into the main
# checkout, where the owner reads it.  New files under toys/, toys-spec/ and
# inbox/ are gitignored, so nothing here is committed: tracked files reach the
# main checkout through Git as before and are never copied.
#
# Only adds and updates (a newer file wins); never deletes.  Private run
# workspaces (toys/wish-*/, toys/.public-example-*/) stay where they are.
# Each toy directory that received files gets a .synced-from line naming the
# source worktree.  Run from any directory inside a worktree; in the main
# checkout itself it does nothing.  Also the Claude Code Stop hook, so it
# always exits 0 and stays quiet unless it copied something.
set -uo pipefail
export LC_ALL=C

DIRS=(toys toys-spec inbox)

top=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
common=$(git -C "$top" rev-parse --path-format=absolute --git-common-dir 2>/dev/null) || exit 0
[ "$(basename "$common")" = .git ] || exit 0
main=$(dirname "$common")
[ "$(cd "$top" && pwd -P)" = "$(cd "$main" && pwd -P)" ] && exit 0
[ -d "$main" ] || exit 0

existing=()
for d in "${DIRS[@]}"; do [ -d "$top/$d" ] && existing+=("$d"); done
[ ${#existing[@]} -gt 0 ] || exit 0

list=$(mktemp) && tracked=$(mktemp) || exit 0
trap 'rm -f "$list" "$tracked"' EXIT

# Untracked files (ignored or not) under the synced directories, minus what
# the main checkout tracks and the private run workspaces.
git -C "$main" ls-files -- "${existing[@]}" 2>/dev/null | sort > "$tracked"
git -C "$top" ls-files -z --others -- "${existing[@]}" 2>/dev/null \
  | tr '\0' '\n' \
  | grep -Ev '^toys/(wish-[^/]*|\.public-example-[^/]*)/|(^|/)\.synced-from$' \
  | sort | comm -23 - "$tracked" > "$list"
[ -s "$list" ] || exit 0

changed=$(rsync -a --update --itemize-changes --files-from="$list" "$top/" "$main/" \
  | awk '$1 ~ /^>f/ { sub(/^[^ ]+ /, ""); print }')
[ -n "$changed" ] || exit 0

source=$(basename "$top")
stamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
printf '%s\n' "$changed" | awk -F/ 'NF > 2 {print $1 "/" $2} NF == 2 {print $1}' | sort -u \
  | while read -r dir; do
      [ -d "$main/$dir" ] && printf '%s %s\n' "$stamp" "$source" >> "$main/$dir/.synced-from"
    done
echo "sync-to-main: copied $(printf '%s\n' "$changed" | wc -l) file(s) from $source into $main" >&2
exit 0
