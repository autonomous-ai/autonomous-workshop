# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_die_2.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/thickness-die_2.md`

part_die_2.step.py: 4.10 cm3 solid, grid 0.133 mm (125x125x125), 83508 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 83508 samples) |
| thickness distribution | PASS | median 16.00 mm, p95 16.00 mm, max 16.00 mm |
| hollowable at 1.20 mm wall | WARN | 2.52 of 4.10 cm3 (61%) in 1 pocket(s) |
| filament that would save | PASS | 0.38 cm3, 0.5 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

## Captured tool output

The following is the exact stdout from this report-producing command.

```text
part_die_2.step.py: 4.10 cm3 solid, grid 0.133 mm (125x125x125), 83508 surface samples, thickness resolved to 0.067 mm
  PASS  wall >= 0.80 mm (+/-0.07)      0.0% of surface below (0 of 83508 samples)
  PASS  thickness distribution         median 16.00 mm, p95 16.00 mm, max 16.00 mm
  WARN  hollowable at 1.20 mm wall     2.52 of 4.10 cm3 (61%) in 1 pocket(s)
  PASS  filament that would save       0.38 cm3, 0.5 g at 15% infill -- the slicer already leaves most of that space empty
RESULT: printable at this wall
  wrote <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/thickness-die_2.md
```

Printed STEP SHA-256: `92e8d706104147c5791c01a783e78ecb278bf4c46fdc28792bdca00ac66bcab4`. Captured log SHA-256: `7cc6c68986c5fb2a2146f519aa4f5440474d8ed715f9fcb259873c9c482ffd81`.
