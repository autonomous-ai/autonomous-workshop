# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/heritage/part_tank_cover.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/heritage/measure/component-rounds/tank_cover/r0001/thickness-tank_cover.md`

part_tank_cover.step.py: 16.57 cm3 solid, grid 0.147 mm (331x195x175), 169546 surface samples, thickness resolved to 0.074 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 169546 samples) |
| thickness distribution | PASS | median 25.14 mm, p95 30.72 mm, max 47.19 mm |
| hollowable at 1.20 mm wall | WARN | 12.29 of 16.57 cm3 (74%) in 1 pocket(s) |
| filament that would save | PASS | 1.84 cm3, 2.3 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
