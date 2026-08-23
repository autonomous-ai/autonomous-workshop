# Upstream snapshot

- Source: https://github.com/nohope88/text2cad
- Commit: `0cb635eb868bd54408c97d45604704fc9bc8edd4`
- Imported: 2026-08-23 as a source snapshot, without Git history.
- Excluded: `.env.bak-pre-modelmix` and all `*.bak*` source backups.
- Root license: none found. The bundled `skills/cadcode/LICENSE` is MIT, but
  that license does not automatically cover the root pipeline. Confirm team
  permission or add a root license before redistribution outside this project.

## Monorepo overlays and local lock

The source snapshot is identified by the commit above. This monorepo adds a
snapshot banner to `README.md` plus `inventor.json`, root `TASTE.md`, and this
`UPSTREAM.md`; excluded backup files are listed above. `workshop/snapshots.lock.json`
binds the complete resulting local folder, including these overlays. It is a
local integrity lock, not proof that every local byte equals the named upstream
commit.

## Security action required

The excluded environment backup contains non-placeholder Telegram, admin,
MongoDB, and Panda identity values. Their contents were not copied or printed.
Treat them as compromised: rotate/revoke the credentials and purge the file
from upstream Git history.

## Why it is here

The useful domain pieces are its blind discovery panel, fail-closed lens panel,
tiered repairs, cost/starvation postmortems, and mechanism-first CAD workflow.
Do not reuse its file state, ambient environment forwarding, hard-coded paths,
sending path, or live-worktree self-improvement as shared Workshop infrastructure.
