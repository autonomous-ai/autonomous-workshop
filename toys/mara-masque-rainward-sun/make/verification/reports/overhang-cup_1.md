# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_cup_1.step.py --angle 45 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/overhang-cup_1.md`

part_cup_1.step.py: 95.6 cm2 of surface, grid 0.400 mm, 0 unsupported samples over 0 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 14.5% of the surface faces down that steeply; 0 region(s) need support, 0 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.

## Captured tool output

The following is the exact stdout from this report-producing command.

```text
part_cup_1.step.py: 95.6 cm2 of surface, grid 0.400 mm, 0 unsupported samples over 0 region(s)
  PASS  no face under 45 deg needs support     14.5% of the surface faces down that steeply; 0 region(s) need support, 0 bridge, 0 below 1 mm2
  PASS  bridges within 12 mm                   0 region(s), longest span 0.0 mm
RESULT: prints unsupported
  wrote <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/overhang-cup_1.md
```

Printed STEP SHA-256: `3d950a6f11937b5556d9b3a0b1a657684e7f465d05f183d155a00ddc733df583`. Captured log SHA-256: `dded1e5d115c0eaa12e6220df39689816b844513fdb6ce09350faa39c096bd67`.
