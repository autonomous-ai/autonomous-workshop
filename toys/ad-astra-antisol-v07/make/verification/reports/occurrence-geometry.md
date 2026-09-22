# Occurrence geometry, this run against the published set

`assembled.step` -> `antisol.step`. Compared by label: solid count, exact volume and
bounding box, at 0.0001 mm3 and 1e-06 mm.

A repeated geometry -- the twelve belt tiles, the six corona cells, the
two trays -- is stored once and instanced, so the reader returns all of
its copies under one label. The count and the volume below are the
label's whole family, which is why 196 labels carry 216 solids.

- labels published: 196, carrying 216 solids
- labels in this run: 200, carrying 220 solids
- identical in geometry: 186

## Gone

- `saturn_anti_bands1_cocoa_brown`
- `saturn_anti_bands2_cocoa_brown`
- `saturn_anti_bands3_cocoa_brown`
- `saturn_anti_bands4_cocoa_brown`
- `saturn_sol_bands1_cocoa_brown`
- `saturn_sol_bands2_cocoa_brown`
- `saturn_sol_bands3_cocoa_brown`
- `saturn_sol_bands4_cocoa_brown`

## New

- `saturn_anti_bands1_sunflower_yellow`
- `saturn_anti_bands2_sunflower_yellow`
- `saturn_anti_bands3_sunflower_yellow`
- `saturn_anti_bands4_sunflower_yellow`
- `saturn_anti_cap_white`
- `saturn_anti_southbelt_cocoa_brown`
- `saturn_sol_bands1_sunflower_yellow`
- `saturn_sol_bands2_sunflower_yellow`
- `saturn_sol_bands3_sunflower_yellow`
- `saturn_sol_bands4_sunflower_yellow`
- `saturn_sol_cap_white`
- `saturn_sol_southbelt_cocoa_brown`

## Changed geometry

- `saturn_anti_globe_yellow` — volume 8629.373136 -> 8231.919818 mm3
- `saturn_sol_globe_yellow` — volume 8629.609831 -> 8231.817012 mm3

## Verdict

Nothing outside `saturn_sol_*` and `saturn_anti_*` gained, lost or moved a solid.
