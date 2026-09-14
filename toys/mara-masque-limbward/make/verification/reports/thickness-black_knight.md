# Thickness and hollow

`artifacts/make/r0001/product/cad/part_black_knight.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-black_knight.md`

part_black_knight.step.py: 2.12 cm3 solid, grid 0.133 mm (121x125x185), 65456 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 65456 samples) |
| thickness distribution | PASS | median 8.00 mm, p95 23.93 mm, max 24.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.92 of 2.12 cm3 (43%) in 1 pocket(s) |
| filament that would save | PASS | 0.14 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

## Recorded tool stdout verdict

RESULT: printable at this wall

Recorded in `measure/rounds/r0001/thickness-black_knight.log` (sha256 d7bb86623d7a998cec34945082cb6223d3f0f04ec691fba054444aacf9f27211). The final verifier reran the same geometry and returned exit 0; report measurement bodies match.
