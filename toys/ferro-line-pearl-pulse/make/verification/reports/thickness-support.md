# Thickness and hollow

`artifacts/make/r0001/product/cad/part_support.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-support.md`

part_support.step.py: 17.04 cm3 solid, grid 0.321 mm (185x185x307), 108281 surface samples, thickness resolved to 0.160 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.16) | PASS | 0.0% of surface below (0 of 108281 samples) |
| thickness distribution | PASS | median 5.13 mm, p95 24.23 mm, max 95.30 mm |
| hollowable at 1.20 mm wall | WARN | 5.88 of 17.04 cm3 (34%) in 2 pocket(s) |
| filament that would save | PASS | 0.88 cm3, 1.1 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
