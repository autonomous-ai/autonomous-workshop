# Thickness and hollow

`artifacts/make/r0001/product/cad/crema_click/part_foot_plug.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/crema_click/measure/thickness-foot_plug.md`

part_foot_plug.step.py: 13.86 cm3 solid, grid 0.147 mm (385x386x77), 286978 surface samples, thickness resolved to 0.074 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 286978 samples) |
| thickness distribution | PASS | median 5.44 mm, p95 55.93 mm, max 56.01 mm |
| hollowable at 1.20 mm wall | WARN | 6.95 of 13.86 cm3 (50%) in 4 pocket(s) |
| filament that would save | PASS | 1.04 cm3, 1.3 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

RESULT: printable at this wall
