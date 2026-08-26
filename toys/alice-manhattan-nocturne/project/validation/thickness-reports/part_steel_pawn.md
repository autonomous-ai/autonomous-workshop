# Thickness and hollow

`inventors/alice/toys/manhattan-nocturne/project/exports/stl/part_steel_pawn.stl --nozzle 0.4 --report inventors/alice/toys/manhattan-nocturne/project/validation/thickness-reports/part_steel_pawn.md`

inventors/alice/toys/manhattan-nocturne/project/exports/stl/part_steel_pawn.stl: 7.46 cm3 solid, grid 0.133 mm (173x173x335), 163410 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 163410 samples) |
| thickness distribution | PASS | median 13.87 mm, p95 22.53 mm, max 44.00 mm |
| hollowable at 1.20 mm wall | WARN | 4.50 of 7.46 cm3 (60%) in 1 pocket(s) |
| filament that would save | PASS | 0.67 cm3, 0.8 g at 15% infill -- the slicer already leaves most of that space empty |

Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
