# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_launcher_guide_cap.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0009/thickness-launcher_guide_cap.md`

part_launcher_guide_cap.step.py: 3.70 cm3 solid, grid 0.133 mm (230x245x36), 132575 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 132575 samples) |
| thickness distribution | PASS | median 4.13 mm, p95 31.93 mm, max 32.00 mm |
| hollowable at 1.20 mm wall | WARN | 1.20 of 3.70 cm3 (32%) in 1 pocket(s) |
| filament that would save | PASS | 0.18 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
