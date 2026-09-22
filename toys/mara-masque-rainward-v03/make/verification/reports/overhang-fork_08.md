# Overhang and support

`artifacts/make/r0001/product/cad/part_fork_08.step.py --angle 45.0 --report artifacts/make/r0001/product/cad/measure/overhang-fork_08.md`

part_fork_08.step.py: 2.6 cm2 of surface, grid 0.400 mm, 0 unsupported samples over 0 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 23.8% of the surface faces down that steeply; 0 region(s) need support, 0 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.

## Captured console verdict

The matching current-run check printed the following result. Its measured report content is identical to this final report; only command paths differ. Source: `rounds/r0001/overhang-fork_08.log` (SHA256 `6ea4288035d133449a2a6dc19876376a58f0927d0cde4ba5ef5bc648040e8804`).

RESULT: prints unsupported
