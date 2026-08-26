# Thickness and hollow

`inventors/alice/toys/manhattan-nocturne/project/exports/stl/part_steel_knight.stl --nozzle 0.4 --report inventors/alice/toys/manhattan-nocturne/project/validation/thickness-reports/part_steel_knight.md`

inventors/alice/toys/manhattan-nocturne/project/exports/stl/part_steel_knight.stl: 8.96 cm3 solid, grid 0.140 mm (165x165x426), 204652 surface samples, thickness resolved to 0.070 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 204652 samples) |
| thickness distribution | PASS | median 10.92 mm, p95 22.54 mm, max 53.90 mm |
| hollowable at 1.20 mm wall | WARN | 4.75 of 8.96 cm3 (53%) in 1 pocket(s) |
| filament that would save | PASS | 0.71 cm3, 0.9 g at 15% infill -- the slicer already leaves most of that space empty |

Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
