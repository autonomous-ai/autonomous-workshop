# 3D viewer runtime

The prebuilt CAD viewer from `autonomous-ai/autonomous-vibe`
(`skills/cad-viewer/scripts/viewer/`, commit `81b886b01e79ee65eb259f8324767ef4c844bfad`),
vendored byte-for-byte: `backend/server.mjs` (one esbuild bundle, no `node_modules`)
and `dist/` (the built page). MIT, copyright 2026 earthtojake — see `LICENSE` here
and the repository's `THIRD_PARTY_NOTICES.md`.

`harness/toolchain/viewer.sh` runs it as the Harness 3D pane. It is not used by
Workshop's own product runs. To update it, copy the same three paths from a newer
Vibe commit and record the commit here.
