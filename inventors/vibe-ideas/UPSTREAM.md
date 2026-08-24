# Upstream snapshot

- Source: https://github.com/reinSPQR/vibe-ideas
- Commit: `ed3d1e876faed95b1bf785af2fae2a8133354517`
- Imported: 2026-08-23 as a complete tracked source snapshot, without Git
  history. No credential-bearing file was found.
- Root license: none found. The bundled `cadcode/LICENSE` is MIT, but that does
  not automatically cover the root pipeline. Confirm team permission or add a
  root license before redistribution outside this project.

## Monorepo overlays and local lock

The source snapshot is identified by the commit above. This monorepo adds a
snapshot banner to `README.md` plus `inventor.json`, root `TASTE.md`, and this
`UPSTREAM.md`. `snapshots.lock.json` binds the complete resulting local
folder, including these overlays. It is a local integrity lock, not proof that
every local byte equals the named upstream commit.

## Why it is here

This inventor contributes the deepest board-game-specific workflow: mechanical
rules lint, executable simulation, isolated LLM table play and exact replay,
animation review, ergonomics, interference/motion checks, bounded rework, human
approval gates, and a strong draft-send package.

It remains a reference until Workshop replaces unsafe infrastructure. In particular,
its queue accepts non-adjacent target states and lacks a fencing token; rules
completion tests freshness rather than parsing PASS; shipping can proceed with
missing or failed gate evidence; and its self-improvement path mutates/cleans the
live worktree.
