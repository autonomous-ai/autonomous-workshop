# Thickness and hollow

`artifacts/make/r0001/product/mintfin/part_body_07_front.step.py --nozzle .4 --min-wall 1.2 --report artifacts/make/r0001/product/mintfin/measure/wish-thickness-body_07_front.md`

part_body_07_front.step.py: 0.62 cm3 solid, grid 0.200 mm (102x90x49), 17708 surface samples, thickness resolved to 0.100 mm

| check | status | detail |
|---|---|---|
| wall >= 1.20 mm (+/-0.10) | PASS | 0.0% of surface below (0 of 17708 samples); 4430 more within measurement error of the limit |
| thickness distribution | PASS | median 1.20 mm, p95 9.00 mm, max 11.50 mm |
| hollowable at 1.20 mm wall | WARN | 0.14 of 0.62 cm3 (23%) in 1 pocket(s) |
| filament that would save | PASS | 0.02 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
