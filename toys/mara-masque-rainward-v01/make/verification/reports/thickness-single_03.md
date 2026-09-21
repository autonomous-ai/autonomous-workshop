# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_single_03.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/thickness-single_03.md`

part_single_03.step.py: 0.26 cm3 solid, grid 0.133 mm (95x65x35), 13408 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 13408 samples) |
| thickness distribution | PASS | median 4.00 mm, p95 11.93 mm, max 12.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.05 of 0.26 cm3 (19%) in 1 pocket(s) |
| filament that would save | PASS | 0.01 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

## Captured tool output

The following is the exact stdout from this report-producing command.

```text
part_single_03.step.py: 0.26 cm3 solid, grid 0.133 mm (95x65x35), 13408 surface samples, thickness resolved to 0.067 mm
  PASS  wall >= 0.80 mm (+/-0.07)      0.0% of surface below (0 of 13408 samples)
  PASS  thickness distribution         median 4.00 mm, p95 11.93 mm, max 12.00 mm
  WARN  hollowable at 1.20 mm wall     0.05 of 0.26 cm3 (19%) in 1 pocket(s)
  PASS  filament that would save       0.01 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty
RESULT: printable at this wall
  wrote <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/thickness-single_03.md
```

Printed STEP SHA-256: `2f7429a3a46efea2e01a8ea3140553db54c5c9cb2622918ad5e0b66c7e039a1b`. Captured log SHA-256: `c129e8489a7c7a4baf01ec8666d2602d990d6114d41a9b0e30202295aea6c8c1`.
