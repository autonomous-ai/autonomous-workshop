# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_square_dust_knot.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/square_dust_knot/r0001/thickness-square_dust_knot.md`

part_square_dust_knot.step.py: 2.85 cm3 solid, grid 0.133 mm (170x170x140), 89954 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 89954 samples) |
| thickness distribution | PASS | median 10.53 mm, p95 22.00 mm, max 26.93 mm |
| hollowable at 1.20 mm wall | WARN | 1.13 of 2.85 cm3 (39%) in 1 pocket(s) |
| filament that would save | PASS | 0.17 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
