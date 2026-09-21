# Thickness and hollow

`artifacts/make/r0001/product/cad/part_cup_2.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-cup_2.md`

part_cup_2.step.py: 9.32 cm3 solid, grid 0.170 mm (251x251x169), 325404 surface samples, thickness resolved to 0.085 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.09) | PASS | 0.0% of surface below (0 of 325404 samples) |
| thickness distribution | PASS | median 1.96 mm, p95 27.91 mm, max 42.03 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 9.32 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

## Captured console verdict

The matching current-run check printed the following result. Its measured report content is identical to this final report; only command paths differ. Source: `rounds/r0001/thickness-cup_2.log` (SHA256 `99a4bf5f4325f93f06218d4389e6296316714423fce87df27057e171e00b2459`).

RESULT: printable at this wall
