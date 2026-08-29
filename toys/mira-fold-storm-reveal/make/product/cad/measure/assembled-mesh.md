# Required root assembled STL mesh check

Command:

```text
python .agents/skills/cad/scripts/check_mesh artifacts/make/r0001/product/assembled.stl --bed 220x220x220 --assembly
```

Observed result for `assembled.stl` sha256 `38d9ff1110a47083584f00eb7eb794e74f6a49ea778f357d988f7ad194b936c0`:

- 2910 triangles, 1459 vertices.
- PASS: zero sliver triangles under the gate threshold.
- PASS: watertight, zero boundary edges.
- PASS: manifold edges and vertices.
- PASS: consistent winding.
- PASS: positive volume, 29.84 cm3.
- PASS: three connected shells, expected for the three separately printable pieces in the assembled review export.
- PASS: fits the 220 x 220 x 220 mm bed at 87.0 x 65.0 x 12.8 mm.
- Result: printable assembly mesh under `--assembly`; the three `cad/part_*.stl` files remain the actual print targets and carry independent thickness reports.

