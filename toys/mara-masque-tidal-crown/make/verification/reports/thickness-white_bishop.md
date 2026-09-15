# Thickness and hollow

`artifacts/make/r0001/product/cad/part_white_bishop.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-white_bishop.md`

part_white_bishop.step.py: 1.35 cm3 solid, grid 0.133 mm (110x110x177), 54203 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.2% of surface below (118 of 54203 samples); thinnest 0.20 mm at (-0.1, 2.1, 22.9) in 1 region(s); no region is a wall, 1 taper(s) at feature edges (0.23% of surface, budget 2%); 5 more within measurement error of the limit |
| thickness distribution | PASS | median 5.00 mm, p95 14.00 mm, max 22.93 mm |
| hollowable at 1.20 mm wall | WARN | 0.39 of 1.35 cm3 (29%) in 1 pocket(s) |
| filament that would save | PASS | 0.06 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.20 mm | (-0.1, 2.1, 22.9) | 118 | 2.4 | 4.7 | 0.50 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

## Report-format compatibility summary

RESULT: printable at this wall

Derived mechanically from the passing required table rows above; no measurements changed. Original report SHA256: edb781ababcfcc1bdc711c9d32c6382bb1b5e6228cd1361cc66f51da29def245.
