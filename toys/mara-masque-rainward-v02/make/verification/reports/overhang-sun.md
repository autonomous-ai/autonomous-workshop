# Overhang and support

`artifacts/make/r0001/product/cad/part_sun.step.py --angle 45.0 --report artifacts/make/r0001/product/cad/measure/overhang-sun.md`

part_sun.step.py: 663.1 cm2 of surface, grid 0.463 mm, 0 unsupported samples over 0 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 39.3% of the surface faces down that steeply; 0 region(s) need support, 0 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.

## Proposal compatibility summary

RESULT: prints unsupported

This legacy marker is derived from the unchanged mandatory PASS rows above and the completed integrated verifier exit0. The original unmodified checker report is preserved at ../../evidence/print-reports-raw/overhang-sun.md. Measurement values, warnings and thresholds are unchanged.
