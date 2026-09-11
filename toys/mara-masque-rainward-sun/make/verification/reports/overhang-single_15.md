# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_single_15.step.py --angle 45 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/overhang-single_15.md`

part_single_15.step.py: 2.6 cm2 of surface, grid 0.400 mm, 0 unsupported samples over 0 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 25.0% of the surface faces down that steeply; 0 region(s) need support, 0 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.

## Captured tool output

The following is the exact stdout from this report-producing command.

```text
part_single_15.step.py: 2.6 cm2 of surface, grid 0.400 mm, 0 unsupported samples over 0 region(s)
  PASS  no face under 45 deg needs support     25.0% of the surface faces down that steeply; 0 region(s) need support, 0 bridge, 0 below 1 mm2
  PASS  bridges within 12 mm                   0 region(s), longest span 0.0 mm
RESULT: prints unsupported
  wrote <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/overhang-single_15.md
```

Printed STEP SHA-256: `5be413df5dc3c8fcb1ebd553ce20a429a25ee7bb39b561907bfe3c6d9bf13cf4`. Captured log SHA-256: `c036f30961eebb2d4e3669c928c3b494245626053f500bada16fdfa1cc877c45`.
