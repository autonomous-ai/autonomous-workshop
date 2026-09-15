# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_launcher_housing.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0003/thickness-launcher_housing.md`

part_launcher_housing.step.py: 38.65 cm3 solid, grid 0.264 mm (194x687x82), 328439 surface samples, thickness resolved to 0.132 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.13) | PASS | 0.0% of surface below (0 of 328439 samples); 647 more within measurement error of the limit |
| thickness distribution | PASS | median 3.04 mm, p95 24.02 mm, max 180.04 mm |
| hollowable at 1.20 mm wall | WARN | 9.41 of 38.65 cm3 (24%) in 1 pocket(s) |
| filament that would save | PASS | 1.41 cm3, 1.8 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
