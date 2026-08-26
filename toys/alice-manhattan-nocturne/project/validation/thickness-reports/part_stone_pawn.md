# Thickness and hollow

`inventors/alice/toys/manhattan-nocturne/project/exports/stl/part_stone_pawn.stl --nozzle 0.4 --report inventors/alice/toys/manhattan-nocturne/project/validation/thickness-reports/part_stone_pawn.md`

inventors/alice/toys/manhattan-nocturne/project/exports/stl/part_stone_pawn.stl: 7.30 cm3 solid, grid 0.133 mm (173x173x335), 158055 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 158055 samples) |
| thickness distribution | PASS | median 13.80 mm, p95 23.00 mm, max 44.00 mm |
| hollowable at 1.20 mm wall | WARN | 4.43 of 7.30 cm3 (61%) in 1 pocket(s) |
| filament that would save | PASS | 0.66 cm3, 0.8 g at 15% infill -- the slicer already leaves most of that space empty |

Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
