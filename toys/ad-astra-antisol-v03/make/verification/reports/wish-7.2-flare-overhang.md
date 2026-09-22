# Overhang and support

> Provenance: this is the source archive's record of why the star's flame
> feet were narrowed, measured on a scratch build that no longer exists.
> It is kept as the reason for a dimension, not as this run's evidence.
> This run's own overhang verdict for the star is
> `measure/overhang-den_plug.md`, and `part_den_plug.step` is byte-identical
> to the archive copy here.

`.tmp/wishflare/part_den_wish.step.py --angle 45 --report .tmp/wishflare/overhang-wish.md`

part_den_wish.step.py: 43.7 cm2 of surface, grid 0.400 mm, 699 unsupported samples over 2 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 28.5% of the surface faces down that steeply; 2 region(s) need support, 0 bridge, 0 below 1 mm2; worst 53.3 mm2 spanning 10.5 mm |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | overhang | 53.3 | (-17.8, -17.8, 8.2) | 10.5 | 9.2 |
| 2 | overhang | 51.6 | (17.8, -17.9, 8.2) | 10.5 | 9.2 |

RESULT: NEEDS SUPPORT

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
