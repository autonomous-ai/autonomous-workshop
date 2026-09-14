# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_camera_board.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/camera_board/r0002/thickness-camera_board.md`

part_camera_board.step.py: 819.68 cm3 solid, grid 0.452 mm (439x439x62), 359649 surface samples, thickness resolved to 0.226 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.23) | PASS | 0.0% of surface below (0 of 359649 samples); 23 more within measurement error of the limit |
| thickness distribution | PASS | median 22.12 mm, p95 195.96 mm, max 251.27 mm |
| hollowable at 1.20 mm wall | WARN | 694.52 of 819.68 cm3 (85%) in 1 pocket(s) |
| filament that would save | PASS | 104.18 cm3, 129.2 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
