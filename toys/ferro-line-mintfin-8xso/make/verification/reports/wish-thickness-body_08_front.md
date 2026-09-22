# Thickness and hollow

`artifacts/make/r0001/product/mintfin/part_body_08_front.step.py --nozzle .4 --min-wall 1.2 --report artifacts/make/r0001/product/mintfin/measure/wish-thickness-body_08_front.md`

part_body_08_front.step.py: 0.64 cm3 solid, grid 0.200 mm (73x96x58), 15357 surface samples, thickness resolved to 0.100 mm

| check | status | detail |
|---|---|---|
| wall >= 1.20 mm (+/-0.10) | PASS | 0.0% of surface below (0 of 15357 samples) |
| thickness distribution | PASS | median 4.20 mm, p95 10.20 mm, max 13.60 mm |
| hollowable at 1.20 mm wall | WARN | 0.15 of 0.64 cm3 (23%) in 1 pocket(s) |
| filament that would save | PASS | 0.02 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
