# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_orbit_tray.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-orbit_tray.md`

part_orbit_tray.step.py: 60.39 cm3 solid, grid 0.207 mm (798x430x34), 387119 surface samples, thickness resolved to 0.103 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.10) | PASS | 0.0% of surface below (0 of 387119 samples) |
| thickness distribution | PASS | median 5.90 mm, p95 23.99 mm, max 164.03 mm |
| hollowable at 1.20 mm wall | WARN | 18.95 of 60.39 cm3 (31%) in 1 pocket(s) |
| filament that would save | PASS | 2.84 cm3, 3.5 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
