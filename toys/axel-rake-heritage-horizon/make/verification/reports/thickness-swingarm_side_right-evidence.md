# Thickness and hollow

`artifacts/make/r0001/product/heritage/part_swingarm_side_right.step.py --nozzle 0.4 --report artifacts/make/r0001/product/heritage/measure/thickness-swingarm_side_right.md`

part_swingarm_side_right.step.py: 2.27 cm3 solid, grid 0.133 mm (428x218x88), 110848 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 110848 samples) |
| thickness distribution | PASS | median 4.00 mm, p95 10.93 mm, max 51.73 mm |
| hollowable at 1.20 mm wall | WARN | 0.42 of 2.27 cm3 (19%) in 1 pocket(s) |
| filament that would save | PASS | 0.06 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

## Captured deterministic verdict

The original verifier report above is unchanged. The following fresh check output supplies the verdict emitted only on stdout.

```text
part_swingarm_side_right.step.py: 2.27 cm3 solid, grid 0.133 mm (428x218x88), 110848 surface samples, thickness resolved to 0.067 mm
  PASS  wall >= 0.80 mm (+/-0.07)      0.0% of surface below (0 of 110848 samples)
  PASS  thickness distribution         median 4.00 mm, p95 10.93 mm, max 51.73 mm
  WARN  hollowable at 1.20 mm wall     0.42 of 2.27 cm3 (19%) in 1 pocket(s)
  PASS  filament that would save       0.06 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty
RESULT: printable at this wall

```
