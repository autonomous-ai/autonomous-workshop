# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_launcher_rod.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0002/thickness-launcher_rod.md`

part_launcher_rod.step.py: 9.79 cm3 solid, grid 0.197 mm (116x436x213), 123360 surface samples, thickness resolved to 0.098 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.10) | PASS | 0.0% of surface below (0 of 123360 samples) |
| thickness distribution | PASS | median 7.98 mm, p95 21.96 mm, max 79.98 mm |
| hollowable at 1.20 mm wall | WARN | 4.79 of 9.79 cm3 (49%) in 1 pocket(s) |
| filament that would save | PASS | 0.72 cm3, 0.9 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
