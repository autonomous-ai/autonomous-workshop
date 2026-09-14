# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_flipper_right_rotor.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0006/thickness-flipper_right_rotor.md`

part_flipper_right_rotor.step.py: 16.81 cm3 solid, grid 0.228 mm (416x364x71), 129164 surface samples, thickness resolved to 0.114 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.11) | PASS | 0.0% of surface below (0 of 129164 samples) |
| thickness distribution | PASS | median 7.98 mm, p95 23.94 mm, max 66.93 mm |
| hollowable at 1.20 mm wall | WARN | 9.59 of 16.81 cm3 (57%) in 1 pocket(s) |
| filament that would save | PASS | 1.44 cm3, 1.8 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
