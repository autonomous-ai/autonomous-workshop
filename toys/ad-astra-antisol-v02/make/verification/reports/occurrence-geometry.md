# Occurrence geometry, this run against the published set

`antisol.step` -> `antisol.step`. Compared by label: solid count, exact volume and
bounding box, at 0.0001 mm3 and 1e-06 mm.

A repeated geometry -- the twelve belt tiles, the six corona cells, the
two trays -- is stored once and instanced, so the reader returns all of
its copies under one label. The count and the volume below are the
label's whole family, which is why 160 labels carry 180 solids.

- labels published: 160, carrying 180 solids
- labels in this run: 158, carrying 178 solids
- identical in geometry: 136

## Gone

- `earth_anti_land5_green`
- `earth_sol_land5_green`

## New

None.

## Changed geometry

- `earth_anti_dryland1_beige` — volume 6.246199 -> 13.521299 mm3
- `earth_anti_dryland2_beige` — volume 3.910006 -> 7.375115 mm3
- `earth_anti_dryland3_beige` — volume 3.285643 -> 4.843203 mm3
- `earth_anti_dryland4_beige` — volume 1.995277 -> 3.094432 mm3
- `earth_anti_dryland5_beige` — volume 1.979871 -> 1.599482 mm3
- `earth_anti_globe_blue` — volume 2205.622025 -> 2098.846955 mm3
- `earth_anti_ice_white` — volume 24.403456 -> 25.932891 mm3
- `earth_anti_land1_green` — volume 38.900577 -> 77.576711 mm3
- `earth_anti_land2_green` — volume 25.657270 -> 76.079030 mm3
- `earth_anti_land3_green` — volume 20.822773 -> 37.293489 mm3
- `earth_anti_land4_green` — volume 19.929860 -> 9.036447 mm3
- `earth_sol_dryland1_beige` — volume 6.246199 -> 13.521299 mm3
- `earth_sol_dryland2_beige` — volume 3.910003 -> 7.375115 mm3
- `earth_sol_dryland3_beige` — volume 3.285643 -> 4.843203 mm3
- `earth_sol_dryland4_beige` — volume 1.995277 -> 3.094432 mm3
- `earth_sol_dryland5_beige` — volume 1.977385 -> 1.598337 mm3
- `earth_sol_globe_blue` — volume 2206.963852 -> 2098.746797 mm3
- `earth_sol_ice_white` — volume 24.404930 -> 25.932892 mm3
- `earth_sol_land1_green` — volume 38.900577 -> 77.576711 mm3
- `earth_sol_land2_green` — volume 25.657270 -> 76.077371 mm3
- `earth_sol_land3_green` — volume 19.766170 -> 37.040902 mm3
- `earth_sol_land4_green` — volume 19.562367 -> 9.392036 mm3

## Verdict

Nothing outside the two Earth pieces gained, lost or moved a solid.
