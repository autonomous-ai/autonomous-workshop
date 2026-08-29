# Thickness and hollow

`artifacts/make/r0001/product/cad/part_rib_deck.stl --min-wall 0.8 --report artifacts/make/r0001/product/cad/measure/thickness-rib-deck.md`

artifacts/make/r0001/product/cad/part_rib_deck.stl: 13.46 cm3 solid, grid 0.154 mm (704x702x23), 405669 surface samples, thickness resolved to 0.077 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.08) | PASS | 0.0% of surface below (0 of 405669 samples); 556 more within measurement error of the limit |
| thickness distribution | PASS | median 1.54 mm, p95 2.32 mm, max 40.21 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 13.46 cm3 (0%) in 0 pocket(s), 3 too small to shell |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
