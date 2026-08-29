# Complete host-gate output inventory

Host rejection `379d74028fa4f964c4cd90e5ce03f2b0dc02ef66e2969eff66e7d2920ffac65a`
proved that the prior proposal still declared at least one output that the
successful isolated verifier changed. This rejection is authoritative even
though the STEP, STL, GLB, and thickness-report subset had matched locally.

A complete pre/post file inventory of the rejected `cad/` project against an
exact host-layout rebuild found:

- 32 common regular files;
- exactly one changed common file outside the cache:
  `measure/verification-pipeline.md`, whose rejected SHA-256 was
  `921b475a984101a13d4ae3d0020abfea4a391f36fe7cc13be07ebee1e4ef2d3c`;
- 12 rejected cache-tombstone files under `__cadgen__/`;
- 48 fresh run-specific render-package files under rebuilt `__cadgen__/`;
- no other only-shipped or only-rebuilt non-cache files.

The pipeline file necessarily changes because it records the wall-clock time,
elapsed durations, and executed command transcript. The render-package cache
is also explicitly disposable and is rebuilt by `--fresh`. Neither belongs in
the declared product artifact.

The repaired Make contract uses `cad_project/` as its canonical CAD project.
That directory excludes both `__cadgen__/` and
`measure/verification-pipeline.md`. The host verifier may create them inside
its isolated temporary copy, but they are absent from the submitted product
manifest and are not product outputs. Static verification evidence remains in
`measure/verification-host-equivalent.md`.

All persistent generated outputs remain byte-stable:

| persistent output | SHA-256 |
|---|---|
| `assembled.step` | `2cb2c5f02ec499a421bd7c97028c6dabed40b9e46d663dbd45a851c7df7c2a6a` |
| `assembled.glb` | `c61a107094f61583f4def7c8e47bcc31994b6bc14b7541d3d679fe333dda2900` |
| `part_cloud.step` | `4a3ec5ba16292d12bd197f41ae27daf389272bb75fd2195c962d2ef1548753c3` |
| `part_cloud.stl` | `ee088130ebac0afe169bad4bda6af1024f8ac3bfc54761ab7a71b888867a37b1` |
| `measure/thickness-cloud.md` | `8b3e9e2ca101b465d95dde1e87582e73c5be4b88e223a31a820688527ea12f2f` |
| `part_lightning.step` | `421750bfc8bc52520dd9354d49667e9af075ecb16159a905a5044bcef9022115` |
| `part_lightning.stl` | `fb322ec85f5381376c73558f4287dfc0fb01600f085d1964da3afa73a1ceb672` |
| `measure/thickness-lightning.md` | `569ea75a1f259ead3dd136162141d7c2bcaa137a21e404cebc420274e50f955e` |
| `part_rainbow.step` | `f8bafadb838b0e92d4a04a7cd5db2e61a3df8980ca04e1073e2549590b16ada6` |
| `part_rainbow.stl` | `5bce0fc1775c734e5839b2fd1f4b9107b966ff866af3d3a6ca8a20a89ef8b7d5` |
| `measure/thickness-rainbow.md` | `c3fb848763a32d177ffa224503ffd68e8bb0a97b6406757c82a2de755c0d77ed` |

This is deterministic digital evidence only. It does not establish a
successful physical print, fit, wear life, or human response.
