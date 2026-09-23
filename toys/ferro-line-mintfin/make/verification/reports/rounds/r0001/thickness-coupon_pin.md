# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_coupon_pin.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-coupon_pin.md`

part_coupon_pin.step.py: 0.48 cm3 solid, grid 0.133 mm (171x68x63), 29068 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 29068 samples); 98 more within measurement error of the limit |
| thickness distribution | PASS | median 2.80 mm, p95 9.07 mm, max 22.40 mm |
| hollowable at 1.20 mm wall | WARN | 0.05 of 0.48 cm3 (10%) in 1 pocket(s) |
| filament that would save | PASS | 0.01 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
