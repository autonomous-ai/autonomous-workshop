# Thickness and hollow

`artifacts/make/r0001/product/heritage/part_wheel.step.py --nozzle 0.4 --report artifacts/make/r0001/product/heritage/measure/thickness-wheel.md`

part_wheel.step.py: 27.68 cm3 solid, grid 0.154 mm (354x354x86), 274915 surface samples, thickness resolved to 0.077 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.08) | PASS | 0.0% of surface below (0 of 274915 samples) |
| thickness distribution | PASS | median 12.50 mm, p95 25.54 mm, max 25.93 mm |
| hollowable at 1.20 mm wall | WARN | 19.67 of 27.68 cm3 (71%) in 1 pocket(s) |
| filament that would save | PASS | 2.95 cm3, 3.7 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

## Captured deterministic verdict

The original verifier report above is unchanged. The following fresh check output supplies the verdict emitted only on stdout.

```text
part_wheel.step.py: 27.68 cm3 solid, grid 0.154 mm (354x354x86), 274915 surface samples, thickness resolved to 0.077 mm
  PASS  wall >= 0.80 mm (+/-0.08)      0.0% of surface below (0 of 274915 samples)
  PASS  thickness distribution         median 12.50 mm, p95 25.54 mm, max 25.93 mm
  WARN  hollowable at 1.20 mm wall     19.67 of 27.68 cm3 (71%) in 1 pocket(s)
  PASS  filament that would save       2.95 cm3, 3.7 g at 15% infill -- the slicer already leaves most of that space empty
RESULT: printable at this wall

```
