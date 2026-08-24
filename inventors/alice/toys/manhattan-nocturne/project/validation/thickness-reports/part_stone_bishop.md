# Thickness and hollow

`inventors/alice/toys/manhattan-nocturne/project/exports/stl/part_stone_bishop.stl --nozzle 0.4 --report inventors/alice/toys/manhattan-nocturne/project/validation/thickness-reports/part_stone_bishop.md`

inventors/alice/toys/manhattan-nocturne/project/exports/stl/part_stone_bishop.stl: 10.23 cm3 solid, grid 0.147 mm (158x158x420), 198357 surface samples, thickness resolved to 0.074 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 198357 samples); 1 more within measurement error of the limit |
| thickness distribution | PASS | median 11.76 mm, p95 45.13 mm, max 61.01 mm |
| hollowable at 1.20 mm wall | WARN | 6.05 of 10.23 cm3 (59%) in 1 pocket(s) |
| filament that would save | PASS | 0.91 cm3, 1.1 g at 15% infill -- the slicer already leaves most of that space empty |

Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
