# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_black_king.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-black_king.md`

part_black_king.step.py: 2.52 cm3 solid, grid 0.133 mm (121x125x170), 62378 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 62378 samples) |
| thickness distribution | PASS | median 12.00 mm, p95 21.13 mm, max 23.80 mm |
| hollowable at 1.20 mm wall | WARN | 1.35 of 2.52 cm3 (54%) in 1 pocket(s) |
| filament that would save | PASS | 0.20 cm3, 0.3 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
