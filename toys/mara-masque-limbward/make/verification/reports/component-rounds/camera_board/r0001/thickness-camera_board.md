# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_camera_board.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/camera_board/r0001/thickness-camera_board.md`

part_camera_board.step.py: 820.66 cm3 solid, grid 0.452 mm (439x439x62), 360483 surface samples, thickness resolved to 0.226 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.23) | PASS | 0.0% of surface below (0 of 360483 samples); 39 more within measurement error of the limit |
| thickness distribution | PASS | median 22.12 mm, p95 195.96 mm, max 251.49 mm |
| hollowable at 1.20 mm wall | WARN | 695.58 of 820.66 cm3 (85%) in 1 pocket(s) |
| filament that would save | PASS | 104.34 cm3, 129.4 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
