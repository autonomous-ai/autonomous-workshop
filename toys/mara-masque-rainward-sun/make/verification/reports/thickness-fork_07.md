# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_fork_07.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/thickness-fork_07.md`

part_fork_07.step.py: 0.29 cm3 solid, grid 0.133 mm (95x65x35), 16096 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 16096 samples) |
| thickness distribution | PASS | median 4.00 mm, p95 11.60 mm, max 12.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.04 of 0.29 cm3 (15%) in 1 pocket(s) |
| filament that would save | PASS | 0.01 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

## Captured tool output

The following is the exact stdout from this report-producing command.

```text
part_fork_07.step.py: 0.29 cm3 solid, grid 0.133 mm (95x65x35), 16096 surface samples, thickness resolved to 0.067 mm
  PASS  wall >= 0.80 mm (+/-0.07)      0.0% of surface below (0 of 16096 samples)
  PASS  thickness distribution         median 4.00 mm, p95 11.60 mm, max 12.00 mm
  WARN  hollowable at 1.20 mm wall     0.04 of 0.29 cm3 (15%) in 1 pocket(s)
  PASS  filament that would save       0.01 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty
RESULT: printable at this wall
  wrote <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/thickness-fork_07.md
```

Printed STEP SHA-256: `6cbabf6bba9c44729d60e7a142f87c2df9b28d906f313d19df4fa47aad1cc4ee`. Captured log SHA-256: `f77d43f0548e0952e2acff963f9e0c667f34ad353d88e1f911f0f49230a6a40b`.
