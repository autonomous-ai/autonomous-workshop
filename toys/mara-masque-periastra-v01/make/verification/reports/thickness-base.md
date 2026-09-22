# Thickness and hollow

`artifacts/make/r0001/product/cad/part_base.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-base.md`

part_base.step.py: 390.66 cm3 solid, grid 0.452 mm (425x426x58), 360251 surface samples, thickness resolved to 0.226 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.23) | PASS | 0.0% of surface below (0 of 360251 samples) |
| thickness distribution | PASS | median 10.84 mm, p95 189.64 mm, max 256.01 mm |
| hollowable at 1.20 mm wall | WARN | 272.05 of 390.66 cm3 (70%) in 1 pocket(s) |
| filament that would save | PASS | 40.81 cm3, 50.6 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

## Tool terminal verdict

The following line is preserved verbatim from this same invocation’s stdout:

```text
RESULT: printable at this wall
```
