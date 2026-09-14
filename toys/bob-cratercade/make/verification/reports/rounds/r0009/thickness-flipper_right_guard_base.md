# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_flipper_right_guard_base.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0009/thickness-flipper_right_guard_base.md`

part_flipper_right_guard_base.step.py: 11.91 cm3 solid, grid 0.264 mm (389x338x79), 131739 surface samples, thickness resolved to 0.132 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.13) | PASS | 0.0% of surface below (0 of 131739 samples) |
| thickness distribution | PASS | median 2.90 mm, p95 25.34 mm, max 104.01 mm |
| hollowable at 1.20 mm wall | WARN | 1.37 of 11.91 cm3 (12%) in 1 pocket(s) |
| filament that would save | PASS | 0.21 cm3, 0.3 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
