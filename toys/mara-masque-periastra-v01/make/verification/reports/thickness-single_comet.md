# Thickness and hollow

`artifacts/make/r0001/product/cad/part_single_comet.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-single_comet.md`

part_single_comet.step.py: 0.89 cm3 solid, grid 0.133 mm (95x125x57), 31501 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (3 of 31501 samples); thinnest 0.33 mm at (2.0, 4.8, 6.6) in 2 region(s); no region is a wall, 2 taper(s) at feature edges (0.02% of surface, budget 2%); 2 more within measurement error of the limit |
| thickness distribution | PASS | median 6.93 mm, p95 15.80 mm, max 16.07 mm |
| hollowable at 1.20 mm wall | WARN | 0.34 of 0.89 cm3 (38%) in 1 pocket(s) |
| filament that would save | PASS | 0.05 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.33 mm | (2.0, 4.8, 6.6) | 2 | 0.1 | 0.2 | 0.34 |
| 2 | taper | 0.40 mm | (-1.8, 4.7, 6.6) | 1 | 0.0 | 0.0 | 0.30 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

## Tool terminal verdict

The following line is preserved verbatim from this same invocation’s stdout:

```text
RESULT: printable at this wall
```
