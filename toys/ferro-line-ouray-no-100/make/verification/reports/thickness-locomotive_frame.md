# Thickness and hollow

`artifacts/make/r0001/product/cad-project/part_locomotive_frame.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad-project/measure/thickness-locomotive_frame.md`

artifacts/make/r0001/product/cad-project/part_locomotive_frame.stl: 3.63 cm3 solid, grid 0.133 mm (781x65x57), 146163 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 146163 samples) |
| thickness distribution | PASS | median 6.00 mm, p95 11.00 mm, max 103.47 mm |
| hollowable at 1.20 mm wall | WARN | 1.13 of 3.63 cm3 (31%) in 1 pocket(s), 3 too small to shell |
| filament that would save | PASS | 0.17 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
