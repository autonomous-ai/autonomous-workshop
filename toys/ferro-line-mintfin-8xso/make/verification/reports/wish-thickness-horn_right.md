# Thickness and hollow

`artifacts/make/r0001/product/mintfin/part_horn_right.step.py --nozzle .4 --min-wall 1.2 --report artifacts/make/r0001/product/mintfin/measure/wish-thickness-horn_right.md`

part_horn_right.step.py: 1.11 cm3 solid, grid 0.200 mm (60x70x130), 15035 surface samples, thickness resolved to 0.100 mm

| check | status | detail |
|---|---|---|
| wall >= 1.20 mm (+/-0.10) | PASS | 0.0% of surface below (0 of 15035 samples) |
| thickness distribution | PASS | median 10.20 mm, p95 12.60 mm, max 22.20 mm |
| hollowable at 1.20 mm wall | WARN | 0.50 of 1.11 cm3 (45%) in 1 pocket(s) |
| filament that would save | PASS | 0.08 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
