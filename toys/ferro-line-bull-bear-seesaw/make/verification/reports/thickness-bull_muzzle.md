# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_bull_muzzle.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/bull_muzzle/r0002/thickness-bull_muzzle.md`

part_bull_muzzle.step.py: 1.97 cm3 solid, grid 0.133 mm (275x185x60), 93468 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 93468 samples) |
| thickness distribution | PASS | median 3.60 mm, p95 10.67 mm, max 36.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.35 of 1.97 cm3 (18%) in 1 pocket(s), 1 too small to shell |
| filament that would save | PASS | 0.05 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
