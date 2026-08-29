# Host-layout CAD output reproducibility

Host rejection `45887357248b2c13877263d64dfd6b1cb306bbcea3a64fc7ad409cf8921ccb55`
proved that the prior proposal still changed a declared CAD output after the
isolated verifier passed. The geometry was not the remaining defect.

The earlier audit invoked the verifier with a long workspace-relative project
path. Its three thickness reports therefore stored `artifacts/...` paths. The
host invokes the same verifier from a temporary parent with the CAD directory
named exactly `project`; `check_thickness` deterministically rewrote those
declared reports with `project/...` paths, changing their bytes.

This revision ships the exact reports produced by:

```text
cd <isolated-parent>
"$WORKSHOP_PYTHON" <cad-skill>/scripts/verify_project project --fresh --exports --strict-fit
```

The repaired declared outputs are:

| declared output | SHA-256 |
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

Five independent cache-free generation processes, including four explicit
Python hash seeds, produced identical STEP bytes for the combined entry and
all three printable entries. A complete host-layout run also reproduced every
STEP, STL, and GLB byte above. The default `verification-pipeline.md` is a
run log containing a timestamp and elapsed durations; it is evidence, not a
declared reproducible CAD output.

This is byte-stability evidence only. It does not establish a successful
physical print, fit, wear life, or human response.
