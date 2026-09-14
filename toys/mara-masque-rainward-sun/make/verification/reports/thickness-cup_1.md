# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_cup_1.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/thickness-cup_1.md`

part_cup_1.step.py: 9.32 cm3 solid, grid 0.170 mm (251x251x169), 325404 surface samples, thickness resolved to 0.085 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.09) | PASS | 0.0% of surface below (0 of 325404 samples) |
| thickness distribution | PASS | median 1.96 mm, p95 27.91 mm, max 42.03 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 9.32 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

## Captured tool output

The following is the exact stdout from this report-producing command.

```text
part_cup_1.step.py: 9.32 cm3 solid, grid 0.170 mm (251x251x169), 325404 surface samples, thickness resolved to 0.085 mm
  PASS  wall >= 0.80 mm (+/-0.09)      0.0% of surface below (0 of 325404 samples)
  PASS  thickness distribution         median 1.96 mm, p95 27.91 mm, max 42.03 mm
  PASS  hollowable at 1.20 mm wall     0.00 of 9.32 cm3 (0%) in 0 pocket(s)
  PASS  filament that would save       0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty
RESULT: printable at this wall
  wrote <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/thickness-cup_1.md
```

Printed STEP SHA-256: `3d950a6f11937b5556d9b3a0b1a657684e7f465d05f183d155a00ddc733df583`. Captured log SHA-256: `09831968fc92e01cf50a6f9031d47ca2aaf5e3d3b82b2b5b69f220b688c40299`.
