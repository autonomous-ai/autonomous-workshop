# Thickness and hollow

`artifacts/make/r0001/product/cad/part_black_rook.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-black_rook.md`

part_black_rook.step.py: 1.34 cm3 solid, grid 0.133 mm (92x92x140), 47461 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 47461 samples) |
| thickness distribution | PASS | median 8.00 mm, p95 17.93 mm, max 18.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.49 of 1.34 cm3 (36%) in 1 pocket(s) |
| filament that would save | PASS | 0.07 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

## Report-format compatibility summary

RESULT: printable at this wall

Derived mechanically from the passing required table rows above; no measurements changed. Original report SHA256: d0e99ff9cc09012bc824ce993531777e72d2e0f4c79e763e3e1d5125cdf15f53.
