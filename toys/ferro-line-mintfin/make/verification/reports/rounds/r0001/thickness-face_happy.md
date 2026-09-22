# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_face_happy.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-face_happy.md`

part_face_happy.step.py: 1.34 cm3 solid, grid 0.133 mm (155x220x37), 75251 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 75251 samples) |
| thickness distribution | PASS | median 2.40 mm, p95 23.93 mm, max 31.40 mm |
| hollowable at 1.20 mm wall | WARN | 0.05 of 1.34 cm3 (4%) in 2 pocket(s), 1 too small to shell |
| filament that would save | PASS | 0.01 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
