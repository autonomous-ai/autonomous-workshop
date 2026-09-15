# Thickness and hollow

`artifacts/make/r0001/product/cad/part_white_pawn.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-white_pawn.md`

part_white_pawn.step.py: 0.94 cm3 solid, grid 0.133 mm (110x110x95), 36900 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 36900 samples) |
| thickness distribution | PASS | median 8.73 mm, p95 14.00 mm, max 15.13 mm |
| hollowable at 1.20 mm wall | WARN | 0.28 of 0.94 cm3 (30%) in 1 pocket(s) |
| filament that would save | PASS | 0.04 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

## Report-format compatibility summary

RESULT: printable at this wall

Derived mechanically from the passing required table rows above; no measurements changed. Original report SHA256: 0ab5dc6e1862fb1dc64677e5b6f16cefd05239b00d4362753680dcf27b1d0f5a.
