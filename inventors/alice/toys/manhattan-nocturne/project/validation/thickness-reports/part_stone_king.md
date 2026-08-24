# Thickness and hollow

`inventors/alice/toys/manhattan-nocturne/project/exports/stl/part_stone_king.stl --nozzle 0.4 --report inventors/alice/toys/manhattan-nocturne/project/validation/thickness-reports/part_stone_king.md`

inventors/alice/toys/manhattan-nocturne/project/exports/stl/part_stone_king.stl: 11.47 cm3 solid, grid 0.154 mm (150x150x487), 193241 surface samples, thickness resolved to 0.077 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.08) | PASS | 0.0% of surface below (0 of 193241 samples) |
| thickness distribution | PASS | median 11.81 mm, p95 35.96 mm, max 74.40 mm |
| hollowable at 1.20 mm wall | WARN | 6.88 of 11.47 cm3 (60%) in 1 pocket(s) |
| filament that would save | PASS | 1.03 cm3, 1.3 g at 15% infill -- the slicer already leaves most of that space empty |

Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
