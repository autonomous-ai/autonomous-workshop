# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_tear_back.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0004/thickness-tear_back.md`

part_tear_back.step.py: 24.95 cm3 solid, grid 0.154 mm (453x378x67), 341868 surface samples, thickness resolved to 0.077 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.08) | PASS | 0.0% of surface below (0 of 341868 samples) |
| thickness distribution | PASS | median 9.57 mm, p95 69.07 mm, max 69.15 mm |
| hollowable at 1.20 mm wall | WARN | 15.92 of 24.95 cm3 (64%) in 1 pocket(s), 7 too small to shell |
| filament that would save | PASS | 2.39 cm3, 3.0 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
