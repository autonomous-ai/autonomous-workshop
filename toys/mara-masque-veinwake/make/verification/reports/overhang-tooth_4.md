# Overhang and support

`artifacts/make/r0001/product/cad/veinwake/part_tooth_4.step.py --angle 45.0 --report artifacts/make/r0001/product/cad/veinwake/measure/overhang-tooth_4.md`

part_tooth_4.step.py: 26.3 cm2 of surface, grid 0.400 mm, 0 unsupported samples over 0 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 23.4% of the surface faces down that steeply; 0 region(s) need support, 0 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.

## Proposal-format compatibility summary

Manager-authored format bridge from the unchanged passing table above and final verifier exit 0; not an additional measurement. Raw reporter bytes: `raw-verifier-reports/overhang-tooth_4.md`, SHA-256 `d8a168abd7bdb2eca5d76596fbf259de9faa01659c71830798a200a654f0bc89`.

RESULT: prints unsupported
