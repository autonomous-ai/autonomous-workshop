# Thickness and hollow

`artifacts/make/r0001/product/mintfin/part_horn_middle.step.py --nozzle 0.4 --min-wall 1.2 --report artifacts/make/r0001/product/mintfin/measure/wish-thickness-horn_middle.md`

part_horn_middle.step.py: 0.31 cm3 solid, grid 0.200 mm (45x45x80), 6369 surface samples, thickness resolved to 0.100 mm

| check | status | detail |
|---|---|---|
| wall >= 1.20 mm (+/-0.10) | PASS | 0.0% of surface below (0 of 6369 samples) |
| thickness distribution | PASS | median 7.00 mm, p95 9.40 mm, max 15.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.08 of 0.31 cm3 (27%) in 1 pocket(s) |
| filament that would save | PASS | 0.01 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
