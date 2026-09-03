# Thickness and hollow

`artifacts/make/r0001/product/frosting-aloft/part_cap.stl --nozzle 0.4 --report artifacts/make/r0001/product/frosting-aloft/measure/thickness-cap.md`

artifacts/make/r0001/product/frosting-aloft/part_cap.stl: 27.66 cm3 solid, grid 0.197 mm (401x335x78), 260311 surface samples, thickness resolved to 0.098 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.10) | PASS | 0.0% of surface below (0 of 260311 samples) |
| thickness distribution | PASS | median 7.98 mm, p95 63.92 mm, max 78.01 mm |
| hollowable at 1.20 mm wall | WARN | 16.78 of 27.66 cm3 (61%) in 1 pocket(s) |
| filament that would save | PASS | 2.52 cm3, 3.1 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
