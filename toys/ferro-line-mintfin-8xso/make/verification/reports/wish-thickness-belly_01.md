# Thickness and hollow

`artifacts/make/r0001/product/mintfin/part_belly_01.step.py --nozzle .4 --min-wall 1.2 --report artifacts/make/r0001/product/mintfin/measure/wish-thickness-belly_01.md`

part_belly_01.step.py: 0.35 cm3 solid, grid 0.200 mm (215x50x11), 15859 surface samples, thickness resolved to 0.100 mm

| check | status | detail |
|---|---|---|
| wall >= 1.20 mm (+/-0.10) | PASS | 0.0% of surface below (0 of 15859 samples); 6942 more within measurement error of the limit |
| thickness distribution | PASS | median 1.20 mm, p95 8.20 mm, max 41.80 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 0.35 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
