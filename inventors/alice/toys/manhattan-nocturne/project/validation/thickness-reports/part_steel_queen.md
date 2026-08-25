# Thickness and hollow

`inventors/alice/toys/manhattan-nocturne/project/exports/stl/part_steel_queen.stl --nozzle 0.4 --report inventors/alice/toys/manhattan-nocturne/project/validation/thickness-reports/part_steel_queen.md`

inventors/alice/toys/manhattan-nocturne/project/exports/stl/part_steel_queen.stl: 11.89 cm3 solid, grid 0.147 mm (158x158x467), 230444 surface samples, thickness resolved to 0.074 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 230444 samples) |
| thickness distribution | PASS | median 13.82 mm, p95 44.91 mm, max 67.91 mm |
| hollowable at 1.20 mm wall | WARN | 6.94 of 11.89 cm3 (58%) in 1 pocket(s) |
| filament that would save | PASS | 1.04 cm3, 1.3 g at 15% infill -- the slicer already leaves most of that space empty |

Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
