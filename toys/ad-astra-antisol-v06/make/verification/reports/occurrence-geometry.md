# Occurrence geometry, this run against the published set

`assembled.step` -> `antisol.step`. Compared by label: solid count, exact volume and
bounding box, at 0.0001 mm3 and 1e-06 mm.

A repeated geometry -- the twelve belt tiles, the six corona cells, the
two trays -- is stored once and instanced, so the reader returns all of
its copies under one label. The count and the volume below are the
label's whole family, which is why 184 labels carry 204 solids.

- labels published: 184, carrying 204 solids
- labels in this run: 196, carrying 216 solids
- identical in geometry: 168

## Gone

None.

## New

- `jupiter_anti_collar_cocoa_brown`
- `jupiter_anti_zones1_beige`
- `jupiter_anti_zones2_beige`
- `jupiter_anti_zones3_beige`
- `jupiter_anti_zones4_beige`
- `jupiter_anti_zones5_beige`
- `jupiter_sol_collar_cocoa_brown`
- `jupiter_sol_zones1_beige`
- `jupiter_sol_zones2_beige`
- `jupiter_sol_zones3_beige`
- `jupiter_sol_zones4_beige`
- `jupiter_sol_zones5_beige`

## Changed geometry

- `jupiter_anti_bands1_cocoa_brown` — volume 201.022361 -> 267.582127 mm3
- `jupiter_anti_bands2_cocoa_brown` — volume 196.749150 -> 213.707937 mm3
- `jupiter_anti_bands3_cocoa_brown` — volume 176.776097 -> 53.032843 mm3
- `jupiter_anti_bands4_cocoa_brown` — volume 166.300497 -> 51.515317 mm3
- `jupiter_anti_bands5_cocoa_brown` — volume 131.208028 -> 26.959304 mm3
- `jupiter_anti_bands6_cocoa_brown` — volume 131.163165 -> 15.923558 mm3
- `jupiter_anti_globe_orange` — volume 9302.003856 -> 8919.705793 mm3
- `jupiter_anti_spot_red` — volume 34.054699 -> 5.323083 mm3
- `jupiter_sol_bands1_cocoa_brown` — volume 201.022361 -> 267.582127 mm3
- `jupiter_sol_bands2_cocoa_brown` — volume 196.749150 -> 213.707937 mm3
- `jupiter_sol_bands3_cocoa_brown` — volume 176.776097 -> 53.032843 mm3
- `jupiter_sol_bands4_cocoa_brown` — volume 166.300497 -> 51.515317 mm3
- `jupiter_sol_bands5_cocoa_brown` — volume 131.208028 -> 26.959303 mm3
- `jupiter_sol_bands6_cocoa_brown` — volume 131.163169 -> 15.923558 mm3
- `jupiter_sol_globe_orange` — volume 9302.003775 -> 8919.705805 mm3
- `jupiter_sol_spot_red` — volume 34.054699 -> 5.323083 mm3

## Verdict

Nothing outside `jupiter_sol_*` and `jupiter_anti_*` gained, lost or moved a solid.
