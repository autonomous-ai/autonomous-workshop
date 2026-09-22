# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_belly_01.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/belly_01/r0003/thickness-belly_01.md`

part_belly_01.step.py: 0.35 cm3 solid, grid 0.133 mm (320x72x14), 36738 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 36738 samples) |
| thickness distribution | PASS | median 1.20 mm, p95 8.33 mm, max 41.87 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 0.35 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
