# Occurrence geometry, this run against the published set

`assembled.step` -> `antisol.step`. Compared by label: solid count, exact volume and
bounding box, at 0.0001 mm3 and 1e-06 mm.

A repeated geometry -- the twelve belt tiles, the six corona cells, the
two trays -- is stored once and instanced, so the reader returns all of
its copies under one label. The count and the volume below are the
label's whole family, which is why 158 labels carry 178 solids.

- labels published: 158, carrying 178 solids
- labels in this run: 162, carrying 182 solids
- identical in geometry: 144

## Gone

None.

## New

- `mars_anti_albedo5_cocoa_brown`
- `mars_anti_albedo6_cocoa_brown`
- `mars_sol_albedo5_cocoa_brown`
- `mars_sol_albedo6_cocoa_brown`

## Changed geometry

- `mars_anti_albedo1_cocoa_brown` — volume 11.188436 -> 32.396822 mm3
- `mars_anti_albedo2_cocoa_brown` — volume 11.123677 -> 16.595225 mm3
- `mars_anti_albedo3_cocoa_brown` — volume 9.320193 -> 12.588262 mm3
- `mars_anti_albedo4_cocoa_brown` — volume 6.704272 -> 7.720408 mm3
- `mars_anti_caps1_white` — volume 15.815417 -> 23.859614 mm3
- `mars_anti_caps2_white` — volume 0.830256 -> 2.615849 mm3
- `mars_anti_globe_red` — volume 1534.640578 -> 1486.522325 mm3
- `mars_sol_albedo1_cocoa_brown` — volume 19.148631 -> 38.930390 mm3
- `mars_sol_albedo2_cocoa_brown` — volume 11.123677 -> 16.595225 mm3
- `mars_sol_albedo3_cocoa_brown` — volume 9.320193 -> 8.173313 mm3
- `mars_sol_albedo4_cocoa_brown` — volume 6.614294 -> 7.720408 mm3
- `mars_sol_caps1_white` — volume 15.815417 -> 23.859615 mm3
- `mars_sol_caps2_white` — volume 0.830256 -> 2.741115 mm3
- `mars_sol_globe_red` — volume 1526.770402 -> 1484.278440 mm3

## Verdict

Nothing outside `mars_sol_*` and `mars_anti_*` gained, lost or moved a solid.
