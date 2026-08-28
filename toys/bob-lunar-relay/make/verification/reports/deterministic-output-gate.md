# Declared CAD output determinism repair

- Stage subject: `d95b96b58d402e97c65f3c541e1a13bbfc6476efffc1929dae6eda09a95fb721`
- Rejected failure: `declared-cad-output-changed` after the host's isolated
  `verify_project project --fresh --exports --strict-fit` returned exit 0.
- Host finding accepted as authoritative: the source tree was unchanged, but a
  declared generated CAD output changed.

## Diagnosis

An exact-layout reproduction changed only the combined `moon_relay.step` among
the generated CAD outputs. Its rejected-project hash
`367b04a0ab8061e0caafe31f47806a211250f4600488172405692c6d4917877e`
became
`739d3ee9006f4e10fb9fa8f8046ff50d43b6de693b27e1fc837de9fc15e7a888`.
The STEP diff was confined to a permutation of base and axle presentation-style
records. Geometry records, labels, placements, source metadata, part STEP
files, STL files, and the exported GLB were otherwise unchanged. Open CASCADE
was serializing multiple per-child assembly colors through an order that was
not stable between fresh processes.

The three thickness reports and the pipeline report also changed because those
Markdown records intentionally embed the invocation path, elapsed time, and
recording time. They are evidence outputs, not declared CAD geometry.

## Repair

`moon_relay_lib.py` now constructs the combined assembly without per-child
colors. Labels, placements, solids, and part-local colors remain. This removes
the nondeterministic STEP style map while preserving the three printable part
entries and the separately reviewed assembled-STL presentation.

- Repaired library SHA-256:
  `e226c86ed04ba185b45c2fc1ebdbd79322a619b129d003a4dad56b288d8c0bee`.
- Deterministic combined STEP SHA-256:
  `fb738df2e44e549d143adab29504d1626b76192a8354cdd857cc2e2ad48c86ae`.
- Deterministic combined GLB SHA-256:
  `be382d3bfa2538768d346491c8b51c208f074ffd820989d299b141d3ad0d2413`.
- Combined STL SHA-256, unchanged:
  `2a1381d19a83878f90a96842b16c710dad0520547eb16d5d609e3e3d6cedb4da`.

## Stability proof

Two independent copied projects were freshly generated in separate Python
processes. Both combined STEP files had SHA-256
`fb738df2e44e549d143adab29504d1626b76192a8354cdd857cc2e2ad48c86ae`.

A third clean project copy then passed the complete host-equivalent command:

`verify_project project --fresh --exports --strict-fit`

Result: **PASS** (exit 0). Its pipeline report had SHA-256
`0d5e76360d766699cee8eb2864d1f64b370e0772f7efccdccddc4a06ae150b98`.
Before/after hashes were identical for the combined STEP, combined GLB,
combined STL, all three printable-part STEP files, and all three printable-part
STL files. The only changed files were the four regenerated Markdown reports
described above.

An exact CAD `inspect diff` against the rejected primary STEP reports no
topology, geometry, count, center, size, or bounding-box change: both assemblies
contain three shapes, 97 faces, 240 edges, and occupy 92 × 54 × 25 mm.

This is deterministic digital evidence only. It does not claim a successful
print or physical fit.
