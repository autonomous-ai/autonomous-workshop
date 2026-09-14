# Overhang and support

`artifacts/make/r0001/product/cad/part_white_rook.step.py --angle 45.0 --report artifacts/make/r0001/product/cad/measure/overhang-white_rook.md`

part_white_rook.step.py: 20.4 cm2 of surface, grid 0.400 mm, 0 unsupported samples over 0 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 9.8% of the surface faces down that steeply; 0 region(s) need support, 0 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.

## Recorded tool stdout verdict

RESULT: prints unsupported

Recorded in `measure/rounds/r0001/overhang-white_rook.log` (sha256 737938c24b4b8c8944fea10987b03e92296079d9ffd89551376cd4598e47d234). The final verifier reran the same geometry and returned exit 0; report measurement bodies match.
