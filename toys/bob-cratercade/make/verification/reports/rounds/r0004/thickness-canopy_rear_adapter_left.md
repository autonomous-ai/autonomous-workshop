# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_canopy_rear_adapter_left.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0004/thickness-canopy_rear_adapter_left.md`

part_canopy_rear_adapter_left.step.py: 5.00 cm3 solid, grid 0.133 mm (117x228x252), 239463 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 239463 samples) |
| thickness distribution | PASS | median 2.93 mm, p95 15.73 mm, max 32.93 mm |
| hollowable at 1.20 mm wall | WARN | 1.18 of 5.00 cm3 (24%) in 1 pocket(s) |
| filament that would save | PASS | 0.18 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
