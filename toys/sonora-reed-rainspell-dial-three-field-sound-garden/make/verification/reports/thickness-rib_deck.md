# Thickness and hollow

`project/part_rib_deck.stl --nozzle 0.4 --report project/measure/thickness-rib_deck.md`

project/part_rib_deck.stl: 13.46 cm3 solid, grid 0.154 mm (704x702x23), 405819 surface samples, thickness resolved to 0.077 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.08) | PASS | 0.0% of surface below (0 of 405819 samples); 571 more within measurement error of the limit |
| thickness distribution | PASS | median 1.54 mm, p95 2.32 mm, max 40.21 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 13.46 cm3 (0%) in 0 pocket(s), 3 too small to shell |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
