# Thickness and hollow

`artifacts/make/r0001/product/cad/part_roof.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-roof.md`

part_roof.step.py: 523.02 cm3 solid, grid 0.576 mm (321x321x102), 218334 surface samples, thickness resolved to 0.288 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.29) | PASS | 0.0% of surface below (0 of 218334 samples); 5 more within measurement error of the limit |
| thickness distribution | PASS | median 14.41 mm, p95 47.83 mm, max 245.49 mm |
| hollowable at 1.20 mm wall | WARN | 433.84 of 523.02 cm3 (83%) in 1 pocket(s) |
| filament that would save | PASS | 65.08 cm3, 80.7 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

## Tool terminal verdict

The following line is preserved verbatim from this same invocation’s stdout:

```text
RESULT: printable at this wall
```
