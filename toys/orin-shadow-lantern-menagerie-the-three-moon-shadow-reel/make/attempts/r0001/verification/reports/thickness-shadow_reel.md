# Thickness and hollow

`artifacts/make/r0001/product/cad/part_shadow_reel.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-shadow_reel.md`

artifacts/make/r0001/product/cad/part_shadow_reel.stl: 12.43 cm3 solid, grid 0.170 mm (675x675x24), 394589 surface samples, thickness resolved to 0.085 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.09) | PASS | 0.0% of surface below (0 of 394589 samples) |
| thickness distribution | PASS | median 3.23 mm, p95 19.82 mm, max 60.16 mm |
| hollowable at 1.20 mm wall | WARN | 1.84 of 12.43 cm3 (15%) in 1 pocket(s) |
| filament that would save | PASS | 0.28 cm3, 0.3 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
