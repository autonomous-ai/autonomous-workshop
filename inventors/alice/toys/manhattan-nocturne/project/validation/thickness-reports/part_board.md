# Thickness and hollow

`inventors/alice/toys/manhattan-nocturne/project/exports/stl/part_board.stl --nozzle 0.4 --report inventors/alice/toys/manhattan-nocturne/project/validation/thickness-reports/part_board.md`

inventors/alice/toys/manhattan-nocturne/project/exports/stl/part_board.stl: 503.45 cm3 solid, grid 0.390 mm (630x630x28), 398514 surface samples, thickness resolved to 0.195 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.20) | PASS | 0.0% of surface below (0 of 398514 samples) |
| thickness distribution | PASS | median 8.19 mm, p95 243.77 mm, max 243.77 mm |
| hollowable at 1.20 mm wall | WARN | 356.60 of 503.45 cm3 (71%) in 1 pocket(s) |
| filament that would save | PASS | 53.49 cm3, 66.3 g at 15% infill -- the slicer already leaves most of that space empty |

Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
