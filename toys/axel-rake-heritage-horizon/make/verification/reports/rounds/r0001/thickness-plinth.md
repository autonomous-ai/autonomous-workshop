# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/heritage/part_plinth.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/heritage/measure/rounds/r0001/thickness-plinth.md`

part_plinth.step.py: 20.15 cm3 solid, grid 0.207 mm (391x319x92), 302502 surface samples, thickness resolved to 0.103 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.10) | PASS | 0.0% of surface below (0 of 302502 samples) |
| thickness distribution | PASS | median 2.90 mm, p95 64.85 mm, max 79.84 mm |
| hollowable at 1.20 mm wall | WARN | 4.78 of 20.15 cm3 (24%) in 1 pocket(s) |
| filament that would save | PASS | 0.72 cm3, 0.9 g at 15% infill -- the slicer already leaves most of that space empty |


Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
