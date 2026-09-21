# Overhang and support

`artifacts/make/r0001/product/cad/veinwake/part_rind.step.py --angle 45.0 --report artifacts/make/r0001/product/cad/veinwake/measure/overhang-rind.md`

part_rind.step.py: 425.1 cm2 of surface, grid 0.400 mm, 0 unsupported samples over 0 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 38.5% of the surface faces down that steeply; 0 region(s) need support, 0 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.

## Proposal-format compatibility summary

Manager-authored format bridge from the unchanged passing table above and final verifier exit 0; not an additional measurement. Raw reporter bytes: `raw-verifier-reports/overhang-rind.md`, SHA-256 `c1bc84e91fe2f0b6e3739cf1e35b0f619a9f1f7873d645a7cbcff618d8448224`.

RESULT: prints unsupported
