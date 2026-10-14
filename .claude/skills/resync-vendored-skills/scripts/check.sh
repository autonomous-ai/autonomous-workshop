#!/usr/bin/env bash
# Report whether upstream autonomous-product-to-cad changed any Make skill
# tree Workshop vendors since the commit LOCK.json records. Read-only: it
# fetches into a private cache clone (hooks off) and never touches the
# owner's local checkout of upstream.
#
# Prints `up-to-date` or `changed <locked> <head> <skill>...` and the cache
# clone path on the last line.
set -euo pipefail
export LC_ALL=C

checkout=$(git rev-parse --show-toplevel)
cache=${XDG_CACHE_HOME:-$HOME/.cache}/workshop-vendor-upstream
lock_rel=src/workshop/make/skills/LOCK.json

origin=$(git -C "$checkout" remote get-url origin)
url=$(sed -E 's#[^/:]+(\.git)?$#autonomous-product-to-cad.git#' <<<"$origin")
if [ ! -d "$cache/.git" ]; then
  git clone --quiet --filter=blob:none --single-branch --branch main "$url" "$cache"
  git -C "$cache" config core.hooksPath /dev/null
fi
git -C "$cache" fetch --quiet origin main
head=$(git -C "$cache" rev-parse origin/main)

git -C "$checkout" fetch --quiet origin main
lock=$(git -C "$checkout" show "origin/main:$lock_rel")
filter='.skills | to_entries[] | select(.value.source_url | endswith("/autonomous-product-to-cad"))'
locked=$(jq -r "[$filter | .value.source_commit] | unique | if length == 1 then .[0] else error(\"vendored skills lock more than one upstream commit\") end" <<<"$lock")
changed=()
while read -r name; do
  git -C "$cache" diff --quiet "$locked" "$head" -- "skills/$name" || changed+=("$name")
done < <(jq -r "$filter | .key" <<<"$lock")

if [ ${#changed[@]} -eq 0 ]; then
  echo "up-to-date ${locked:0:8} (upstream ${head:0:8})"
else
  echo "changed $locked $head ${changed[*]}"
fi
echo "$cache"
