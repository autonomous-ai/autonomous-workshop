# Thickness and hollow

`cad/part_carrier.stl --nozzle 0.4 --report cad/measure/thickness-carrier.md`

cad/part_carrier.stl: 26.03 cm3 solid, grid 0.239 mm (510x445x52), 240680 surface samples, thickness resolved to 0.120 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.12) | PASS | 0.0% of surface below (0 of 240680 samples) |
| thickness distribution | PASS | median 4.79 mm, p95 24.30 mm, max 82.61 mm |
| hollowable at 1.20 mm wall | WARN | 12.11 of 26.03 cm3 (47%) in 2 pocket(s) |
| filament that would save | PASS | 1.82 cm3, 2.3 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
