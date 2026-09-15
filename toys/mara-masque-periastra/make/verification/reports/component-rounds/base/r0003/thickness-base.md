# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_base.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/base/r0003/thickness-base.md`

part_base.step.py: 407.26 cm3 solid, grid 0.452 mm (425x426x58), 371042 surface samples, thickness resolved to 0.226 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.23) | PASS | 0.0% of surface below (0 of 371042 samples) |
| thickness distribution | PASS | median 9.93 mm, p95 189.64 mm, max 256.01 mm |
| hollowable at 1.20 mm wall | WARN | 274.34 of 407.26 cm3 (67%) in 1 pocket(s) |
| filament that would save | PASS | 41.15 cm3, 51.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
