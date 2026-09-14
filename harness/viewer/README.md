# 3D viewer runtime

The prebuilt CAD viewer from `autonomous-ai/autonomous-vibe`
(`skills/cad-viewer/scripts/viewer/`, commit `81b886b01e79ee65eb259f8324767ef4c844bfad`),
vendored: `backend/server.mjs` (one esbuild bundle, no `node_modules`), `dist/` (the built
page), `package.json`, and `packages/cadpy` (the Python STEP-to-GLB converter the server runs on
open; pure Python over OCP, which the Workshop `.venv` already carries). MIT, copyright 2026
earthtojake — see `LICENSE` here and the repository's `THIRD_PARTY_NOTICES.md`.

`harness/toolchain/viewer.sh` runs it as the Harness 3D pane. It is not used by Workshop's own
product runs.

## Local patches to `backend/server.mjs`

Both are marked `// harness:` in the bundle; re-apply them when updating from a newer Vibe commit.

1. `readCatalog` rescans the workspace when its cached scan is older than a second. Upstream fills
   the cache once at startup and refreshes it only after its own STEP-artifact generation, so a
   STEP written by `gen --write` after the server started never appeared, although the page
   re-reads the catalog every couple of seconds.
2. `VIEWER_SKIPPED_DIRECTORIES` also skips `__cadgen__` (cadgen's derived render cache) and
   `.harness`, so the catalog lists models, not cache files.
3. `harnessRefreshStaleStepArtifacts`, called from the `/__cad/catalog` handler: a STEP rewritten
   in place keeps its stale inline `.<name>.step.glb`, and upstream's page regenerates only a
   *missing* artifact on open — so the pane kept the previous shape with a "stale" badge. The
   server now regenerates the artifact of any STEP whose mtime or size changed (or whose artifact
   is missing or stale on first sight), so the next poll carries the new GLB hash and the page
   redraws. Verified in headless Chromium: a cube became a plate with a hole within a few seconds
   of `gen --write`, no reload.
