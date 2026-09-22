# Thickness and hollow

`artifacts/make/r0001/product/mintfin/part_spike.step.py --nozzle .4 --min-wall 1.2 --report artifacts/make/r0001/product/mintfin/measure/wish-thickness-spike.md`

part_spike.step.py: 0.30 cm3 solid, grid 0.200 mm (45x45x65), 6570 surface samples, thickness resolved to 0.100 mm

| check | status | detail |
|---|---|---|
| wall >= 1.20 mm (+/-0.10) | PASS | 0.0% of surface below (0 of 6570 samples) |
| thickness distribution | PASS | median 6.80 mm, p95 8.40 mm, max 12.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.07 of 0.30 cm3 (25%) in 1 pocket(s) |
| filament that would save | PASS | 0.01 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
