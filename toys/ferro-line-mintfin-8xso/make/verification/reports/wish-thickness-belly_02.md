# Thickness and hollow

`artifacts/make/r0001/product/mintfin/part_belly_02.step.py --nozzle 0.4 --min-wall 1.2 --report artifacts/make/r0001/product/mintfin/measure/wish-thickness-belly_02.md`

part_belly_02.step.py: 0.41 cm3 solid, grid 0.200 mm (238x51x11), 18117 surface samples, thickness resolved to 0.100 mm

| check | status | detail |
|---|---|---|
| wall >= 1.20 mm (+/-0.10) | PASS | 0.0% of surface below (0 of 18117 samples); 8000 more within measurement error of the limit |
| thickness distribution | PASS | median 1.20 mm, p95 8.30 mm, max 45.70 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 0.41 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
