# Thickness and hollow

`artifacts/make/r0001/product/heritage/part_pannier.step.py --nozzle 0.4 --report artifacts/make/r0001/product/heritage/measure/thickness-pannier.md`

part_pannier.step.py: 10.76 cm3 solid, grid 0.133 mm (290x185x95), 174508 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (45 of 174508 samples); thinnest 0.33 mm at (-85.5, 55.4, 11.9) in 2 region(s); no region is a wall, 2 taper(s) at feature edges (0.05% of surface, budget 2%) |
| thickness distribution | PASS | median 12.00 mm, p95 38.00 mm, max 38.00 mm |
| hollowable at 1.20 mm wall | WARN | 7.22 of 10.76 cm3 (67%) in 1 pocket(s) |
| filament that would save | PASS | 1.08 cm3, 1.3 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.33 mm | (-85.5, 55.4, 11.9) | 19 | 0.8 | 1.2 | 0.64 |
| 2 | taper | 0.33 mm | (-50.5, 55.4, 11.9) | 26 | 0.7 | 1.0 | 0.75 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

## Captured deterministic verdict

The original verifier report above is unchanged. The following fresh check output supplies the verdict emitted only on stdout.

```text
part_pannier.step.py: 10.76 cm3 solid, grid 0.133 mm (290x185x95), 174508 surface samples, thickness resolved to 0.067 mm
  PASS  wall >= 0.80 mm (+/-0.07)      0.0% of surface below (45 of 174508 samples); thinnest 0.33 mm at (-85.5, 55.4, 11.9) in 2 region(s); no region is a wall, 2 taper(s) at feature edges (0.05% of surface, budget 2%)
  PASS  thickness distribution         median 12.00 mm, p95 38.00 mm, max 38.00 mm
  WARN  hollowable at 1.20 mm wall     7.22 of 10.76 cm3 (67%) in 1 pocket(s)
  PASS  filament that would save       1.08 cm3, 1.3 g at 15% infill -- the slicer already leaves most of that space empty
        every thin region, worst first -- repair them in one round, not one per run:
        1. [taper] 0.33 mm at (-85.5, 55.4, 11.9)     19 samples, 0.8 mm2, runs 1.2 mm, band 0.64 mm
        2. [taper] 0.33 mm at (-50.5, 55.4, 11.9)     26 samples, 0.7 mm2, runs 1.0 mm, band 0.75 mm
RESULT: printable at this wall

```
