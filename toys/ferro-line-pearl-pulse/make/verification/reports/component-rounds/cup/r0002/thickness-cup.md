# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_cup.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/cup/r0002/thickness-cup.md`

part_cup.step.py: 0.64 cm3 solid, grid 0.133 mm (164x164x30), 59689 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 59689 samples) |
| thickness distribution | PASS | median 1.20 mm, p95 8.60 mm, max 8.87 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 0.64 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
