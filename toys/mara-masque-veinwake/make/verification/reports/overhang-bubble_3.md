# Overhang and support

`artifacts/make/r0001/product/cad/veinwake/part_bubble_3.step.py --angle 45.0 --report artifacts/make/r0001/product/cad/veinwake/measure/overhang-bubble_3.md`

part_bubble_3.step.py: 30.7 cm2 of surface, grid 0.400 mm, 0 unsupported samples over 0 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 20.0% of the surface faces down that steeply; 0 region(s) need support, 0 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.

## Proposal-format compatibility summary

Manager-authored format bridge from the unchanged passing table above and final verifier exit 0; not an additional measurement. Raw reporter bytes: `raw-verifier-reports/overhang-bubble_3.md`, SHA-256 `3aee6af14517e9e66b1567342b2f898baf180fcd5858b590d42794e79a617a89`.

RESULT: prints unsupported
