# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_fork_09.step.py --angle 45 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/overhang-fork_09.md`

part_fork_09.step.py: 3.2 cm2 of surface, grid 0.400 mm, 0 unsupported samples over 0 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 22.6% of the surface faces down that steeply; 0 region(s) need support, 0 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.

## Captured tool output

The following is the exact stdout from this report-producing command.

```text
part_fork_09.step.py: 3.2 cm2 of surface, grid 0.400 mm, 0 unsupported samples over 0 region(s)
  PASS  no face under 45 deg needs support     22.6% of the surface faces down that steeply; 0 region(s) need support, 0 bridge, 0 below 1 mm2
  PASS  bridges within 12 mm                   0 region(s), longest span 0.0 mm
RESULT: prints unsupported
  wrote <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/overhang-fork_09.md
```

Printed STEP SHA-256: `189d6c13d66fbddca3ea54f8261c0441a8b186e645500f61c9f78d72529f78ce`. Captured log SHA-256: `1f8417aacb965d8237315a4b978b76f54b88a8b8327223bf1ead508661b246fb`.
