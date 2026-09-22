# Occurrence geometry, this run against the published set

`assembled.step` -> `antisol.step`. Compared by label: solid count, exact volume and
bounding box, at 0.0001 mm3 and 1e-06 mm.

A repeated geometry -- the twelve belt tiles, the six corona cells, the
two trays -- is stored once and instanced, so the reader returns all of
its copies under one label. The count and the volume below are the
label's whole family, which is why 166 labels carry 186 solids.

- labels published: 166, carrying 186 solids
- labels in this run: 184, carrying 204 solids
- identical in geometry: 162

## Gone

- `venus_anti_globe_beige`
- `venus_anti_ypattern_orange`
- `venus_sol_globe_beige`
- `venus_sol_ypattern_orange`

## New

- `venus_anti_globe_sunflower_yellow`
- `venus_anti_highland1_beige`
- `venus_anti_highland2_beige`
- `venus_anti_highland3_beige`
- `venus_anti_highland4_beige`
- `venus_anti_highland5_beige`
- `venus_anti_highland6_beige`
- `venus_anti_highland7_beige`
- `venus_anti_lowland1_cocoa_brown`
- `venus_anti_lowland2_cocoa_brown`
- `venus_anti_lowland3_cocoa_brown`
- `venus_sol_globe_sunflower_yellow`
- `venus_sol_highland1_beige`
- `venus_sol_highland2_beige`
- `venus_sol_highland3_beige`
- `venus_sol_highland4_beige`
- `venus_sol_highland5_beige`
- `venus_sol_highland6_beige`
- `venus_sol_highland7_beige`
- `venus_sol_lowland1_cocoa_brown`
- `venus_sol_lowland2_cocoa_brown`
- `venus_sol_lowland3_cocoa_brown`

## Changed geometry

None.

## Verdict

Nothing outside `venus_sol_*` and `venus_anti_*` gained, lost or moved a solid.
