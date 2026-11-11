- `tools/build_worktree.py` makes a light worktree: a sparse checkout of
  everything except `toys/*`, `toys-spec/*` and `inbox/*` (only
  `toys/README.md` stays), plus copies of only the named input files and,
  for `--seed-source`, exactly `APPROVAL.json` and the files
  `seed_manifest` lists, at the same paths with their modification times.
  A plain `git worktree add` checked out every tracked toy archive (about
  3 GB per build worktree). `build-a-toy`'s loop launch, harness-fix and
  refresh worktrees and `resync-vendored-skills` now use it; the loop runs
  `tools/sync-to-main.sh` after a completed round so its toy reaches the
  main checkout.
