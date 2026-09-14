# Thickness and hollow

`artifacts/make/r0001/product/heritage/part_fork_bridge_right.step.py --nozzle 0.4 --report artifacts/make/r0001/product/heritage/measure/thickness-fork_bridge_right.md`

part_fork_bridge_right.step.py: 1.32 cm3 solid, grid 0.133 mm (170x140x59), 54471 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (1 of 54471 samples); thinnest 0.27 mm at (52.8, 82.0, 0.0) in 1 region(s); no region is a wall, 1 taper(s) at feature edges (0.00% of surface, budget 2%) |
| thickness distribution | PASS | median 5.93 mm, p95 14.93 mm, max 16.93 mm |
| hollowable at 1.20 mm wall | WARN | 0.38 of 1.32 cm3 (29%) in 1 pocket(s) |
| filament that would save | PASS | 0.06 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.27 mm | (52.8, 82.0, 0.0) | 1 | 0.0 | 0.0 | 0.14 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

## Captured deterministic verdict

The original verifier report above is unchanged. The following fresh check output supplies the verdict emitted only on stdout.

```text
part_fork_bridge_right.step.py: 1.32 cm3 solid, grid 0.133 mm (170x140x59), 54471 surface samples, thickness resolved to 0.067 mm
  PASS  wall >= 0.80 mm (+/-0.07)      0.0% of surface below (1 of 54471 samples); thinnest 0.27 mm at (52.8, 82.0, 0.0) in 1 region(s); no region is a wall, 1 taper(s) at feature edges (0.00% of surface, budget 2%)
  PASS  thickness distribution         median 5.93 mm, p95 14.93 mm, max 16.93 mm
  WARN  hollowable at 1.20 mm wall     0.38 of 1.32 cm3 (29%) in 1 pocket(s)
  PASS  filament that would save       0.06 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty
        every thin region, worst first -- repair them in one round, not one per run:
        1. [taper] 0.27 mm at (52.8, 82.0, 0.0)      1 samples, 0.0 mm2, runs 0.0 mm, band 0.14 mm
RESULT: printable at this wall

```
