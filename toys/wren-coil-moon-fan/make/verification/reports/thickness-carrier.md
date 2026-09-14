# Thickness and hollow

`artifacts/make/r0001/product/cad/part_carrier.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-carrier.md`

part_carrier.step.py: 10.36 cm3 solid, grid 0.140 mm (483x619x38), 355137 surface samples, thickness resolved to 0.070 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 355137 samples) |
| thickness distribution | PASS | median 4.55 mm, p95 21.49 mm, max 62.09 mm |
| hollowable at 1.20 mm wall | WARN | 3.07 of 10.36 cm3 (30%) in 1 pocket(s) |
| filament that would save | PASS | 0.46 cm3, 0.6 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

## Report-format compatibility summary

The current checker reports PASS in the measured table above. The proposal consumer expects this legacy summary wording. No measurement has been changed. Original checker report SHA256: 53f44b02028b1116f93738c0352fd3ffd8f2ce2f054be6c13f7b1d62fc21e705.

RESULT: printable at this wall
