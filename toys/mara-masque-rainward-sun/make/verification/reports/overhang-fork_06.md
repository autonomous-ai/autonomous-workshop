# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_fork_06.step.py --angle 45 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/overhang-fork_06.md`

part_fork_06.step.py: 3.2 cm2 of surface, grid 0.400 mm, 0 unsupported samples over 0 region(s)

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
part_fork_06.step.py: 3.2 cm2 of surface, grid 0.400 mm, 0 unsupported samples over 0 region(s)
  PASS  no face under 45 deg needs support     22.6% of the surface faces down that steeply; 0 region(s) need support, 0 bridge, 0 below 1 mm2
  PASS  bridges within 12 mm                   0 region(s), longest span 0.0 mm
RESULT: prints unsupported
  wrote <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/overhang-fork_06.md
```

Printed STEP SHA-256: `a8960e4d2b9f9f4f82c8f8215ab0513480f3a5ff5d7ae2d23dab1662cb9322c0`. Captured log SHA-256: `fdbfe2eadf5a78265194a9b27f3421b54d9d3f90d29f7d6e5279064d002bbe1f`.
