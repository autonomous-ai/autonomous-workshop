# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_fork_13.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/thickness-fork_13.md`

part_fork_13.step.py: 0.29 cm3 solid, grid 0.133 mm (95x65x35), 16096 surface samples, thickness resolved to 0.067 mm

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
part_fork_13.step.py: 0.29 cm3 solid, grid 0.133 mm (95x65x35), 16096 surface samples, thickness resolved to 0.067 mm
  PASS  wall >= 0.80 mm (+/-0.07)      0.0% of surface below (0 of 16096 samples)
  PASS  thickness distribution         median 4.00 mm, p95 11.60 mm, max 12.00 mm
  WARN  hollowable at 1.20 mm wall     0.04 of 0.29 cm3 (15%) in 1 pocket(s)
  PASS  filament that would save       0.01 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty
RESULT: printable at this wall
  wrote <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/thickness-fork_13.md
```

Printed STEP SHA-256: `bac0b55d4f0b3400ec55d6fc80b93e8a9e988981b3e39edfd9b4dfc54f62520d`. Captured log SHA-256: `1c9e6150260a5ef77f84bbde303c5f738f6b653967e94a5978769cebb5e454d2`.
