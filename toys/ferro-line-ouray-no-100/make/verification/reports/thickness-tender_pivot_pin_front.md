# Thickness and hollow

`artifacts/make/r0001/product/cad-project/part_tender_pivot_pin_front.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad-project/measure/thickness-tender_pivot_pin_front.md`

artifacts/make/r0001/product/cad-project/part_tender_pivot_pin_front.stl: 0.08 cm3 solid, grid 0.133 mm (42x42x65), 6724 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 6724 samples) |
| thickness distribution | PASS | median 3.00 mm, p95 8.00 mm, max 8.00 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 0.08 cm3 (0%) in 0 pocket(s), 1 too small to shell |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
