# Thickness and hollow

`inventors/alice/toys/manhattan-nocturne/project/exports/stl/part_stone_rook.stl --nozzle 0.4 --report inventors/alice/toys/manhattan-nocturne/project/validation/thickness-reports/part_stone_rook.md`

inventors/alice/toys/manhattan-nocturne/project/exports/stl/part_stone_rook.stl: 13.04 cm3 solid, grid 0.140 mm (165x165x412), 251522 surface samples, thickness resolved to 0.070 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 251522 samples) |
| thickness distribution | PASS | median 15.40 mm, p95 52.50 mm, max 56.98 mm |
| hollowable at 1.20 mm wall | WARN | 8.00 of 13.04 cm3 (61%) in 1 pocket(s) |
| filament that would save | PASS | 1.20 cm3, 1.5 g at 15% infill -- the slicer already leaves most of that space empty |

Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
