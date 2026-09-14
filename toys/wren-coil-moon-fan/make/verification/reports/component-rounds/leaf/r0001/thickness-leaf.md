# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_leaf.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/leaf/r0001/thickness-leaf.md`

part_leaf.step.py: 6.41 cm3 solid, grid 0.133 mm (507x650x36), 335342 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 335342 samples) |
| thickness distribution | PASS | median 2.40 mm, p95 22.33 mm, max 62.13 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 6.41 cm3 (0%) in 0 pocket(s), 1 too small to shell |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
