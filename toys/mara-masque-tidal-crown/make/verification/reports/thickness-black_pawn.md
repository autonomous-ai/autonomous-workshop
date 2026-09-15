# Thickness and hollow

`artifacts/make/r0001/product/cad/part_black_pawn.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-black_pawn.md`

part_black_pawn.step.py: 0.86 cm3 solid, grid 0.133 mm (92x92x95), 33341 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 33341 samples) |
| thickness distribution | PASS | median 9.53 mm, p95 13.87 mm, max 15.13 mm |
| hollowable at 1.20 mm wall | WARN | 0.27 of 0.86 cm3 (31%) in 1 pocket(s) |
| filament that would save | PASS | 0.04 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

## Report-format compatibility summary

RESULT: printable at this wall

Derived mechanically from the passing required table rows above; no measurements changed. Original report SHA256: 1f88da0b5d92cdd7dc1fd401e9964c6381cf4dc93bf17f975bf960b9f1374a73.
