# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_launcher_rod.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0009/thickness-launcher_rod.md`

part_launcher_rod.step.py: 9.16 cm3 solid, grid 0.170 mm (246x504x93), 154618 surface samples, thickness resolved to 0.085 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.09) | PASS | 0.0% of surface below (0 of 154618 samples) |
| thickness distribution | PASS | median 8.00 mm, p95 21.95 mm, max 79.98 mm |
| hollowable at 1.20 mm wall | WARN | 4.48 of 9.16 cm3 (49%) in 1 pocket(s) |
| filament that would save | PASS | 0.67 cm3, 0.8 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
