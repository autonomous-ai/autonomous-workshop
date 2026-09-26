# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_world_jupiter_sol.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/world_jupiter_sol/r0002/thickness-world_jupiter_sol.md`

part_world_jupiter_sol.step.py: 14.65 cm3 solid, grid 0.147 mm (235x235x209), 183631 surface samples, thickness resolved to 0.074 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (0 of 183631 samples) |
| thickness distribution | PASS | median 26.83 mm, p95 33.52 mm, max 35.87 mm |
| hollowable at 1.20 mm wall | WARN | 10.19 of 14.65 cm3 (70%) in 1 pocket(s) |
| filament that would save | PASS | 1.53 cm3, 1.9 g at 15% infill -- the slicer already leaves most of that space empty |


RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
