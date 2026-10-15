#!/usr/bin/env bash
# Write Wiki Rules back to the upstream autonomous-product-to-cad wiki through
# GitHub only. The owner's local checkout of that repository is never read or
# written: its hooks merge commits into its main, and sessions run there.
#
#   wiki_writeback.sh clone <dir>   fresh clone of origin/main into a new <dir>
#   wiki_writeback.sh push  <dir>   lint, rebase onto origin/main, push to main
#
# Between the two, write pages under <dir>/skills/wiki/ with its own
# `skills/wiki/scripts/wiki new|lint` and commit them. `push` refuses a commit
# that touches anything outside skills/wiki/, and stops on a rebase conflict.
set -euo pipefail

# The clone URL reuses the transport of this Workshop checkout's origin (an
# SSH host alias here), swapping only the repository name.
REPO=autonomous-product-to-cad
URL=${WIKI_UPSTREAM_URL:-$(git remote get-url origin | sed -E 's#[^/:]+(\.git)?$#'"$REPO"'.git#')}
ATTEMPTS=3

die() { echo "wiki_writeback: $*" >&2; exit 1; }

cmd=${1:-}; dir=${2:-}
[ -n "$cmd" ] && [ -n "$dir" ] || die "usage: $0 clone|push <dir>"

case "$cmd" in
  clone)
    [ -e "$dir" ] && die "$dir exists; clone into a new directory"
    git clone --quiet --filter=blob:none --single-branch --branch main "$URL" "$dir"
    # No hook of any kind runs in this clone.
    git -C "$dir" config core.hooksPath /dev/null
    echo "$dir"
    ;;
  push)
    [ -d "$dir/.git" ] || die "$dir is not a clone made by '$0 clone'"
    [ "$(git -C "$dir" config core.hooksPath || true)" = /dev/null ] \
      || die "$dir was not made by '$0 clone'"
    [ -z "$(git -C "$dir" status --porcelain)" ] || die "commit or discard the changes in $dir first"
    for attempt in $(seq "$ATTEMPTS"); do
      git -C "$dir" fetch --quiet origin main
      ahead=$(git -C "$dir" rev-list --count origin/main..HEAD)
      [ "$ahead" -gt 0 ] || { echo "wiki_writeback: nothing to push"; exit 0; }
      outside=$(git -C "$dir" diff --name-only origin/main...HEAD | grep -v '^skills/wiki/' || true)
      [ -z "$outside" ] || die "commits touch files outside skills/wiki/: $outside"
      if ! git -C "$dir" rebase --quiet origin/main; then
        git -C "$dir" rebase --abort || true
        die "rebase onto origin/main conflicted; merge by hand in $dir (keep both rules), commit, push again"
      fi
      (cd "$dir" && python3 skills/wiki/scripts/wiki lint) || die "wiki lint failed in $dir"
      if git -C "$dir" push --quiet origin HEAD:main; then
        echo "wiki_writeback: pushed $ahead commit(s) to $URL main at $(git -C "$dir" rev-parse --short HEAD)"
        exit 0
      fi
      echo "wiki_writeback: push raced (attempt $attempt of $ATTEMPTS); refetching" >&2
    done
    die "push failed $ATTEMPTS times"
    ;;
  *) die "unknown command $cmd" ;;
esac
