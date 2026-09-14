# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_return_floor_2.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0005/thickness-return_floor_2.md`

part_return_floor_2.step.py: 12.29 cm3 solid, grid 0.133 mm (380x828x35), 388761 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 388761 samples) |
| thickness distribution | PASS | median 4.00 mm, p95 26.00 mm, max 109.73 mm |
| hollowable at 1.20 mm wall | WARN | 4.21 of 12.29 cm3 (34%) in 1 pocket(s) |
| filament that would save | PASS | 0.63 cm3, 0.8 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
