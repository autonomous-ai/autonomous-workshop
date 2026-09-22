# Occurrence geometry, this run against the published set

`assembled.step` -> `assembled.step`. Compared by label: solid count, exact volume and
bounding box, at 0.0001 mm3 and 1e-06 mm.

A repeated geometry -- the twelve belt tiles, the six corona cells, the
two trays -- is stored once and instanced, so the reader returns all of
its copies under one label. The count and the volume below are the
label's whole family, which is why 162 labels carry 182 solids.

- labels published: 162, carrying 182 solids
- labels in this run: 166, carrying 186 solids
- identical in geometry: 152

## Gone

- `mercury_anti_plains1_dark_gray`
- `mercury_anti_plains2_dark_gray`
- `mercury_anti_plains3_dark_gray`
- `mercury_anti_plains4_dark_gray`
- `mercury_sol_plains1_dark_gray`
- `mercury_sol_plains2_dark_gray`
- `mercury_sol_plains3_dark_gray`
- `mercury_sol_plains4_dark_gray`

## New

- `mercury_anti_caloris_floor_white`
- `mercury_anti_caloris_rim_cocoa_brown`
- `mercury_anti_plains1_cocoa_brown`
- `mercury_anti_plains2_cocoa_brown`
- `mercury_anti_plains3_cocoa_brown`
- `mercury_anti_plains4_cocoa_brown`
- `mercury_sol_caloris_floor_white`
- `mercury_sol_caloris_rim_cocoa_brown`
- `mercury_sol_plains1_cocoa_brown`
- `mercury_sol_plains2_cocoa_brown`
- `mercury_sol_plains3_cocoa_brown`
- `mercury_sol_plains4_cocoa_brown`

## Changed geometry

- `mercury_anti_globe_gray` — volume 1226.100377 -> 1174.583993 mm3
- `mercury_sol_globe_gray` — volume 1226.100377 -> 1174.583993 mm3

## Verdict

Nothing outside `mercury_sol_*` and `mercury_anti_*` gained, lost or moved a solid.
